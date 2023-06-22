import asyncio
import json
import tempfile
from datetime import date
from pprint import pformat
from typing import List, Tuple, cast
from urllib.parse import urlparse

import requests
import yarl
from pydantic import AnyUrl, BaseModel

import app.secbot.inputs.gitlab.handlers.defectdojo.api as defectdojo
from app.secbot import logger
from app.secbot.inputs.gitlab.schemas import AnyGitlabModel
from app.secbot.inputs.gitlab.schemas.output_responses import OutputFinding
from app.secbot.schemas import Severity

WORKER_TO_SCAN_TYPE_MAPPER = {
    "gitleaks": "Gitleaks Scan",
}


class OutputResultObject(BaseModel):
    data: AnyGitlabModel
    worker: str
    result: str


class DefectDojoCredentials(BaseModel):
    url: AnyUrl
    secret_key: str
    user: str
    lead_id: int


def handle_dd_response(resp, context="", raise_on_error=True):
    if (
        resp.response_code not in (200, 201)
        or resp.success is not True
        or isinstance(resp.data, str)
    ):
        if context:
            context = f", context: {context}"
        error_msg = (
            f"[!] Error. Message: {resp.message}. "
            f"Status_code: {resp.response_code}, data: {pformat(resp.data)}, {context}"
        )
        if raise_on_error:
            raise RuntimeError(error_msg)
        if isinstance(resp.data, dict) or isinstance(resp.data, list):
            return resp.data
        try:
            return json.loads(resp.data)
        except Exception:
            return {"error": str(resp.data)}
    # return json data if everything is good
    return resp.data


async def dd_prepare(
    credentials: DefectDojoCredentials,
    product_type: str,
    product_name: str,
    product_description: str,
    repo_url: AnyUrl,
    name: str,
    commit_hash: str,
    description: str,
):
    dd = defectdojo.DefectDojoAPIv2(
        credentials.url,
        credentials.secret_key,
        credentials.user,
        debug=False,
        timeout=360,
    )
    # Check if product type already exists. Create one if it doesn't exist
    product_type_dd = await dd.list_products_type(name=product_type)
    product_type_dd_parsed = handle_dd_response(product_type_dd, product_type)
    product_types = cast(List[dict], product_type_dd_parsed["results"])
    if len(product_types) > 0:
        product_types = [pt for pt in product_types if pt["name"] == product_type]
    if len(product_types) > 0:
        product_type_id = product_types[0]["id"]
        logger.info(
            f"[x] Product type '{product_type}' already exists, getting the first one (#{product_type_id})"
        )
    else:
        # product type is being created with a direct API call due to the absence of an appropriate
        # wrapper method in defectdojo_apiv2
        try:
            logger.info(f"[x] Create product type {product_type}")
            # todo: async
            response = requests.post(
                f"{credentials.url}/api/v2/product_types/",
                headers={"Authorization": f"Token {credentials.secret_key}"},
                json={"name": product_type},
                verify=False,
            )
            response.raise_for_status()
            product_type_id = response.json()["id"]
        except Exception:
            logger.info(f'[!] Error. Cannot create product type "{product_type}"')
            raise

    # Check if product already exists. Create one if it doesn't exist
    product_dd = await dd.list_products(name=product_name)
    product_dd_parsed = handle_dd_response(product_dd, product_name)
    products = cast(List[dict], product_dd_parsed["results"])
    if len(products) > 0:
        products = [
            product
            for product in products
            if product["name"] == product_name
            and product["prod_type"] == product_type_id
        ]
    if len(products) > 0:
        product_id = products[0]["id"]
        logger.info(
            f"[x] Product '{product_name}' already exists, getting the first one (#{product_id})"
        )
    else:
        # create product if it doesn't exist
        logger.info(f"[x] Create product {product_name}")
        product = await dd.create_product(
            product_name,
            product_description,
            product_type_id,
        )
        product = handle_dd_response(product, product_name)
        product_id = product["id"]

    engagement_dd = await dd.list_engagements(name=name)
    engagement_dd_parsed = handle_dd_response(engagement_dd, name)
    engagements = cast(List[dict], engagement_dd_parsed["results"])
    if len(engagements) > 0:
        engagements = [
            engagement
            for engagement in engagements
            if engagement["name"] == name and engagement["product"] == product_id
        ]
    if len(engagements) > 0:
        engagement_id = engagements[0]["id"]
        engagement_name = engagements[0]["name"]
        logger.info(
            f"[x] Engagement '{engagement_name}' already exists, getting the first one (#{engagement_id})"
        )
    else:
        # create the engagement if we didn't find one
        engagement_data = {
            "name": f"{name}",
            "product_id": product_id,
            "lead_id": credentials.lead_id,
            "status": "Completed",
            "target_start": f'{date.today().strftime("%Y-%m-%d")}',
            "target_end": f'{date.today().strftime("%Y-%m-%d")}',
            "engagement_type": "CI/CD",
            "deduplication_on_engagement": False,
            "build_id": f"{name}",
            "commit_hash": f"{commit_hash}",
            "description": f"Latest commit by {description}",
            "source_code_management_uri": f"{repo_url}",
        }

        engagement = await dd.create_engagement(
            name=engagement_data["name"],
            product_id=engagement_data["product_id"],
            lead_id=engagement_data["lead_id"],
            status=engagement_data["status"],
            target_start=engagement_data["target_start"],
            target_end=engagement_data["target_end"],
            engagement_type=engagement_data["engagement_type"],
            deduplication_on_engagement=engagement_data["deduplication_on_engagement"],
            build_id=engagement_data["build_id"],
            commit_hash=engagement_data["commit_hash"],
            description=engagement_data["description"],
            source_code_management_uri=engagement_data["source_code_management_uri"],
        )
        engagement = handle_dd_response(engagement, name)
        engagement_name = engagement["name"]
        engagement_id = engagement["id"]
        logger.info(f"[x] Engagement was created: {engagement_name} #{engagement_id}")
    logger.info(f"[x] Check product at {credentials.url}/product/{product_id}")
    logger.info(
        f"[x] Check engagement at {credentials.url}/engagement/{engagement_id}"
    )
    return engagement_id


async def dd_upload(
    credentials: DefectDojoCredentials,
    engagement_id,
    scan_type,
    report_file,
    tag: str,
    minimum_severity="High",
):
    dd = defectdojo.DefectDojoAPIv2(
        credentials.url,
        credentials.secret_key,
        credentials.user,
        debug=False,
        timeout=360,
    )
    # scan_type - e.g. Nuclei Scan
    valid_scan_type = WORKER_TO_SCAN_TYPE_MAPPER.get(scan_type, scan_type)
    upload_data = {
        "engagement_id": f"{engagement_id}",
        "scan_type": f"{valid_scan_type}",
        "file": f"{report_file}",
        "active": True,
        "verified": False,
        "close_old_findings": False,
        "skip_duplicates": False,
        "scan_date": f'{date.today().strftime("%Y-%m-%d")}',
        "minimum_severity": f"{minimum_severity}",
    }
    upload = await dd.upload_scan(
        engagement_id=upload_data["engagement_id"],
        scan_type=upload_data["scan_type"],
        file=upload_data["file"],
        active=upload_data["active"],
        verified=upload_data["verified"],
        close_old_findings=upload_data["close_old_findings"],
        skip_duplicates=upload_data["skip_duplicates"],
        scan_date=upload_data["scan_date"],
        minimum_severity=upload_data["minimum_severity"],
        tags=tag,  # list of tags, but we will use only commit hash id
    )
    if not upload.success:
        raise RuntimeError(upload.data)
    return upload


async def dd_findings_by_test(credentials: DefectDojoCredentials, test_id: int):
    dd = defectdojo.DefectDojoAPIv2(
        credentials.url,
        credentials.secret_key,
        credentials.user,
        debug=False,
        timeout=360,
    )
    findings = await dd.list_findings(
        active="true",
        duplicate="false",
        test_id_in=[test_id],
        # NOTE(ivan.zhirov): Temporary solution before the pagination system
        #                    will be added
        # TODO(ivan.zhirov): Implement proper pagination
        limit=500,
    )
    return handle_dd_response(findings, str(test_id))


async def dd_get_test(
    credentials: DefectDojoCredentials,
    test_id: int,
):
    dd = defectdojo.DefectDojoAPIv2(
        credentials.url,
        credentials.secret_key,
        credentials.user,
        debug=False,
        timeout=360,
    )
    test = await dd.get_test(test_id)
    test = handle_dd_response(test, str(test_id))
    return test


async def send_result(
    credentials: DefectDojoCredentials,
    output_result: OutputResultObject,
) -> Tuple[int, List[OutputFinding]]:
    web_url = output_result.data.project.web_url
    product_type = urlparse(web_url).hostname
    product_name = output_result.data.project.path_with_namespace
    commit_hash = output_result.data.commit.id
    eng_id = await dd_prepare(
        credentials,
        product_type=product_type,
        product_name=product_name,
        product_description=web_url,
        repo_url=output_result.data.commit.url.replace("/-/commit/", "/-/blob/"),
        name=yarl.URL(output_result.data.path).path,
        commit_hash=commit_hash,
        description=output_result.data.commit.author.email,
    )
    with tempfile.NamedTemporaryFile(prefix="dd_output_") as tmp_file:
        with open(tmp_file.name, "wb") as tmp_file_write:
            tmp_file_write.write(output_result.result.encode())

        test_upload = await dd_upload(
            credentials,
            engagement_id=eng_id,
            scan_type=output_result.worker,
            report_file=tmp_file.name,
            tag=commit_hash,
        )
        test_upload_id = test_upload.data["test_id"]
    for i in range(30):
        test = await dd_get_test(credentials, test_upload_id)
        if test["percent_complete"] == 100:
            break
        await asyncio.sleep(10)
    else:
        raise RuntimeError(
            f"Took too much time to handle the output, test_id={test_upload_id}"
        )

    await asyncio.sleep(120)  # wait for deduplication

    response = await dd_findings_by_test(credentials, test_upload_id)
    findings = [
        OutputFinding(
            # todo: do smth with types
            title=finding["title"],
            severity=Severity(finding["severity"]),
            url=str(
                yarl.URL(credentials.url).with_path(f"finding/{str(finding['id'])}")
            ),
        )
        for finding in response["results"]
    ]
    return test_upload_id, findings
