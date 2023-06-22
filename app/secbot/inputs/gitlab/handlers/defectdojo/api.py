import json
import logging
from typing import List

import aiohttp

from app.secbot.logger import logger

version = "1.2.0."


class DefectDojoAPIv2(object):
    """An API wrapper for DefectDojo."""

    def __init__(
        self,
        host,
        api_token,
        user,
        api_version="v2",
        timeout=60,
        debug=False,
    ):
        """Initialize a DefectDojo API instance.

        :param host: The URL for the DefectDojo server. (e.g., http://localhost:8000/DefectDojo/)
        :param api_token: The API token generated on the DefectDojo API key page.
        :param user: The user associated with the API key.
        :param api_version: API version to call, the default is v2.
        :param timeout: HTTP timeout in seconds, default is 30.
        :param debug: Prints requests and responses, useful for debugging.

        """

        self.host = host + "/api/" + api_version + "/"
        self.api_token = api_token
        self.user = user
        self.api_version = api_version
        self.timeout = timeout
        self.logger = logger

        if debug:
            self.logger.setLevel(logging.DEBUG)

    # Engagements API
    async def list_engagements(
        self,
        status=None,
        product_id=None,
        name_contains=None,
        name=None,
        limit=20,
        offset=0,
    ):
        """Retrieves all the engagements.

        :param product_in: List of product ids (1,2).
        :param name_contains: Engagement name
        :param limit: Number of records to return.
        :param offset: The initial index from which to return the result

        """

        params = {}
        if limit:
            params["limit"] = limit

        if offset:
            params["offset"] = offset

        if product_id:
            params["product"] = product_id

        if status:
            params["status"] = status

        # TODO remove name_contains here, or add to Defect Dojo. Currently it does nothing
        if name_contains:
            params["name_contains"] = name_contains

        if name:
            params["name"] = name

        return await self._request("GET", "engagements/", params)

    async def create_engagement(
        self,
        name,
        product_id,
        lead_id,
        status,
        target_start,
        target_end,
        active="True",
        pen_test="False",
        check_list="False",
        threat_model="False",
        risk_path="",
        test_strategy="",
        progress="",
        done_testing="False",
        engagement_type="CI/CD",
        build_id=None,
        commit_hash=None,
        branch_tag=None,
        build_server=None,
        source_code_management_server=None,
        source_code_management_uri=None,
        orchestration_engine=None,
        description=None,
        deduplication_on_engagement=True,
    ):
        """Creates an engagement with the given properties.

        :param name: Engagement name.
        :param product_id: Product key id.
        :param lead_id: Testing lead from the user table.
        :param status: Engagement Status: In Progress, On Hold, Completed.
        :param target_start: Engagement start date.
        :param target_end: Engagement end date.
        :param active: Active
        :param pen_test: Pen test for engagement.
        :param check_list: Check list for engagement.
        :param threat_model: Thread Model for engagement.
        :param risk_path: risk_path
        :param test_strategy: Test Strategy URLs
        :param progress: Engagement progress measured in percent.
        :param engagement_type: Interactive or CI/CD
        :param build_id: Build id from the build server
        :param commit_hash: Commit hash from source code management
        :param branch_tag: Branch or tag from source code management
        :param build_server: Tool Configuration id of build server
        :param source_code_management_server: URL of source code management
        :param source_code_management_uri: Link to source code commit
        :param orchestration_engine: URL of orchestration engine
        :param deduplication_on_engagement: boolean value for deduplication_on_engagement

        """

        data = {
            "name": name,
            "product": product_id,
            "lead": lead_id,
            "status": status,
            "target_start": target_start,
            "target_end": target_end,
            "active": active,
            "pen_test": pen_test,
            "check_list": check_list,
            "threat_model": threat_model,
            "risk_path": risk_path,
            "test_strategy": test_strategy,
            "progress": progress,
            "done_testing": done_testing,
            "engagement_type": engagement_type,
        }

        if description:
            data.update({"description": description})

        if build_id:
            data.update({"build_id": build_id})

        if commit_hash:
            data.update({"commit": commit_hash})

        if branch_tag:
            data.update({"branch_tag": branch_tag})

        if build_server:
            data.update({"build_server": build_server})

        if source_code_management_server:
            data.update(
                {"source_code_management_server": source_code_management_server}
            )

        if source_code_management_uri:
            data.update({"source_code_management_uri": source_code_management_uri})

        if orchestration_engine:
            data.update({"orchestration_engine": orchestration_engine})

        if deduplication_on_engagement:
            data.update({"deduplication_on_engagement": deduplication_on_engagement})

        return await self._request("POST", "engagements/", data=data)

    async def set_engagement(
        self,
        id,
        product_id=None,
        lead_id=None,
        name=None,
        status=None,
        target_start=None,
        target_end=None,
        active=None,
        pen_test=None,
        check_list=None,
        threat_model=None,
        risk_path=None,
        test_strategy=None,
        progress=None,
        done_testing=None,
        engagement_type="CI/CD",
        build_id=None,
        commit_hash=None,
        branch_tag=None,
        build_server=None,
        source_code_management_server=None,
        source_code_management_uri=None,
        orchestration_engine=None,
        description=None,
    ):

        """Updates an engagement with the given properties.

        :param id: Engagement id.
        :param name: Engagement name.
        :param product_id: Product key id.
        :param lead_id: Testing lead from the user table.
        :param status: Engagement Status: In Progress, On Hold, Completed.
        :param target_start: Engagement start date.
        :param target_end: Engagement end date.
        :param active: Active
        :param pen_test: Pen test for engagement.
        :param check_list: Check list for engagement.
        :param threat_model: Thread Model for engagement.
        :param risk_path: risk_path
        :param test_strategy: Test Strategy URLs
        :param progress: Engagement progress measured in percent.
        :param engagement_type: Interactive or CI/CD
        :param build_id: Build id from the build server
        :param commit_hash: Commit hash from source code management
        :param branch_tag: Branch or tag from source code management
        :param build_server: Tool Configuration id of build server
        :param source_code_management_server: URL of source code management
        :param source_code_management_uri: Link to source code commit
        :param orchestration_engine: URL of orchestration engine
        """

        data = {}

        if name:
            data["name"] = name

        if product_id:
            data["product"] = product_id

        if lead_id:
            data["lead"] = lead_id

        if status:
            data["status"] = status

        if target_start:
            data["target_start"] = target_start

        if target_end:
            data["target_end"] = target_end

        if active is not None:
            data["active"] = active

        if pen_test:
            data["pen_test"] = pen_test

        if check_list:
            data["check_list"] = check_list

        if threat_model:
            data["threat_model"] = threat_model

        if risk_path:
            data["risk_path"] = risk_path

        if test_strategy:
            data["test_strategy"] = test_strategy

        if progress:
            data["progress"] = progress

        if done_testing:
            data["done_testing"] = done_testing

        if build_id:
            data["build_id"] = build_id

        if commit_hash:
            data["commit"] = commit_hash

        if description:
            data["description"] = description

        return await self._request("PATCH", "engagements/" + str(id) + "/", data=data)

    async def list_products(self, name=None, name_contains=None, limit=200, offset=0):

        """Retrieves all the products.

        :param name: Search by product name.
        :param name_contains: Search by product name.
        :param limit: Number of records to return.
        :param offset: The initial index from which to return the results.

        """

        params = {}
        if limit:
            params["limit"] = limit

        if offset:
            params["offset"] = offset

        if name:
            params["name"] = name

        if name_contains:
            params["name__icontains"] = name_contains

        return await self._request("GET", "products/", params)

    async def create_product(self, name, description, prod_type):
        """Creates a product with the given properties.

        :param name: Product name.
        :param description: Product description..
        :param prod_type: Product type.

        """

        data = {"name": name, "description": description, "prod_type": prod_type}

        return await self._request("POST", "products/", data=data)

    async def get_test(self, test_id):
        """Retrieves a test using the given test id.

        :param test_id: Test identification.

        """
        return await self._request("GET", "tests/" + str(test_id) + "/")

    # Findings API
    async def list_findings(
        self,
        active=None,
        duplicate=None,
        mitigated=None,
        severity=None,
        verified=None,
        severity_lt=None,
        severity_gt=None,
        severity_contains=None,
        title_contains=None,
        url_contains=None,
        date_lt=None,
        date_gt=None,
        date=None,
        product_id_in=None,
        engagement_id_in=None,
        test_id_in=None,
        build=None,
        prefetch: List[str] = None,
        test_tags: List[str] = None,
        related_fields: bool = False,
        limit=20,
        offset=0,
    ):

        """Returns filtered list of findings.

        :param active: Finding is active: (true or false)
        :param duplicate: Duplicate finding (true or false)
        :param mitigated: Mitigated finding (true or false)
        :param severity: Severity: Low, Medium, High and Critical.
        :param verified: Finding verified.
        :param severity_lt: Severity less than Low, Medium, High and Critical.
        :param severity_gt: Severity greater than Low, Medium, High and Critical.
        :param severity_contains: Severity contains: (Medium, Critical)
        :param title_contains: Filter by title containing the keyword.
        :param url_contains: Filter by URL containing the keyword.
        :param date_lt: Date less than.
        :param date_gt: Date greater than.
        :param date: Return findings for a particular date.
        :param product_id_in: Product id(s) associated with a finding. (1,2 or 1)
        :param engagement_id_in: Engagement id(s) associated with a finding. (1,2 or 1)
        :param test_in: Test id(s) associated with a finding. (1,2 or 1)
        :param build_id: User specified build id relating to the build number
                         from the build server. (Jenkins, Travis etc.).
        :param limit: Number of records to return.
        :param offset: The initial index from which to return the results

        """

        params = {}
        if limit:
            params["limit"] = limit

        if offset:
            params["offset"] = offset

        if active:
            params["active"] = active

        if duplicate:
            params["duplicate"] = duplicate

        if mitigated:
            params["mitigated"] = mitigated

        if severity:
            params["severity__in"] = severity

        if verified:
            params["verified"] = verified

        if severity_lt:
            params["severity__lt"] = severity_lt

        if severity_gt:
            params["severity__gt"] = severity_gt

        if severity_contains:
            params["severity"] = severity_contains

        if title_contains:
            params["title"] = title_contains

        if url_contains:
            params["url__contains"] = url_contains

        if date_lt:
            params["date__lt"] = date_lt

        if date_gt:
            params["date__gt"] = date_gt

        if date:
            params["date"] = date

        if engagement_id_in:
            params["test__engagement"] = engagement_id_in

        if product_id_in:
            params["test__engagement__product"] = product_id_in

        if test_id_in:
            params["test"] = test_id_in

        if build:
            params["build_id__contains"] = build

        if prefetch:
            params["prefetch"] = ",".join(prefetch)

        if test_tags:
            params["test__tags"] = ",".join(test_tags)

        if related_fields:
            params["related_fields"] = "true"

        return await self._request("GET", "findings/", params)

    # Upload API
    async def upload_scan(
        self,
        engagement_id,
        scan_type,
        file,
        active,
        verified,
        close_old_findings,
        skip_duplicates,
        scan_date,
        build="",
        tags=None,
        version=None,
        branch_tag=None,
        commit_hash=None,
        minimum_severity="Info",
        auto_group_by=None,
    ):
        """Uploads and processes a scan file.

        :param application_id: Application identifier.
        :param file_path: Path to the scan file to be uploaded.

        """
        if build is None:
            build = ""

        with open(file, "rb") as f:
            filedata = f.read()

        self.logger.debug("filedata:")
        self.logger.debug(filedata)

        data = {
            "file": filedata,
            "engagement": engagement_id,
            "scan_type": scan_type,
            "active": active,
            "verified": verified,
            "close_old_findings": close_old_findings,
            "skip_duplicates": skip_duplicates,
            "scan_date": scan_date,
            "tags": tags,
            "build_id": build,
            "version": version,
            "branch_tag": branch_tag,
            "commit_hash": commit_hash,
            "minimum_severity": minimum_severity,
            # 'push_to_jira': ('', True)
        }
        if auto_group_by:
            data["auto_group_by"] = auto_group_by

        """
        TODO: implement these parameters:
          lead
          test_type
          scan_date
        """
        return await self._request("POST", "import-scan/", files=data)

    async def list_language_types(self, id=None, language_name=None, limit=20):
        """Retrieves source code languages.

        :param id: Search by language id.
        :param language_name: Search by language name
        :param limit: Number of records to return.

        """

        params = {}
        if limit:
            params["limit"] = limit

        if id:
            params["id"] = id

        if language_name:
            params["language__icontains"] = language_name

        return await self._request("GET", "language_types/", params)

    async def list_products_type(self, id=None, name=None, limit=100, offset=0):
        """
        Retrieves product types

        :param id: Search for a specific product type ID
        :param name: Search a specific product type key
        :param limit: Number of records to return.
        :param offset: The initial index from which to return the result
        """

        params = {}
        if id:
            params["id"] = id

        if name:
            params["name"] = name

        if limit:
            params["limit"] = limit

        if offset:
            params["offset"] = offset

        return await self._request("GET", "product_types/", params)

    # Utility

    @staticmethod
    def _build_list_params(param_name, key, values):
        """Builds a list of POST parameters from a list or single value."""
        params = {}
        if hasattr(values, "__iter__"):
            index = 0
            for value in values:
                params[str(param_name) + "[" + str(index) + "]." + str(key)] = str(
                    value
                )
                index += 1
        else:
            params[str(param_name) + "[0]." + str(key)] = str(values)
        return params

    @staticmethod
    def _sanitize_multipart_data(data):
        ret = {}
        for name, value in data.items():
            if value is None:
                continue
            if isinstance(value, bool):
                value = "true" if value else "false"
            ret[name] = value
        return ret

    async def _request(self, method, url, params=None, data=None, files=None):
        """Common handler for all HTTP requests."""
        if not params:
            params = {}

        if data:
            data = json.dumps(data)
        if files:
            data = self._sanitize_multipart_data(files)

        headers = {
            "Authorization": (
                ("ApiKey " + self.user + ":" + self.api_token)
                if (self.api_version == "v1")
                else ("Token " + self.api_token)
            ),
        }

        if not files:
            headers["Accept"] = "application/json"
            headers["Content-Type"] = "application/json"

        self.logger.debug("request:")
        self.logger.debug(method + " " + url)
        self.logger.debug("headers: " + str(headers))
        self.logger.debug("params:" + str(params))
        self.logger.debug("data:" + str(data))
        self.logger.debug("files:" + str(files))

        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                response = await session.request(
                    method=method,
                    url=self.host + url,
                    params=params,
                    data=data,
                    headers=headers,
                    timeout=self.timeout,
                )
                status_code = response.status
                text = await response.text()
                data = await response.json()

                self.logger.debug("response:")
                self.logger.debug(status_code)
                self.logger.debug(text)
                try:
                    if status_code == 201:  # Created new object
                        try:
                            object_id = response.headers["Location"].split("/")
                            key_id = object_id[-2]
                            data = int(key_id)
                        except Exception:
                            pass

                        return DefectDojoResponse(
                            message="Upload complete",
                            response_code=status_code,
                            data=data,
                            success=True,
                        )
                    elif status_code == 204:  # Object updates
                        return DefectDojoResponse(
                            message="Object updated.",
                            response_code=status_code,
                            success=True,
                        )
                    elif status_code == 400:  # Object not created
                        return DefectDojoResponse(
                            message="Error occurred in API.",
                            response_code=status_code,
                            success=False,
                            data=text,
                        )
                    elif status_code == 404:  # Object not created
                        return DefectDojoResponse(
                            message="Object id does not exist.",
                            response_code=status_code,
                            success=False,
                            data=text,
                        )
                    elif status_code == 401:
                        return DefectDojoResponse(
                            message="Unauthorized.",
                            response_code=status_code,
                            success=False,
                            data=text,
                        )
                    elif status_code == 414:
                        return DefectDojoResponse(
                            message="Request-URI Too Large.",
                            response_code=status_code,
                            success=False,
                        )
                    elif status_code == 500:
                        return DefectDojoResponse(
                            message="An error 500 occurred in the API.",
                            response_code=status_code,
                            success=False,
                            data=text,
                        )
                    else:
                        return DefectDojoResponse(
                            message="Success",
                            data=data,
                            success=True,
                            response_code=status_code,
                        )
                except ValueError:
                    return DefectDojoResponse(
                        message="JSON response could not be decoded.",
                        response_code=status_code,
                        success=False,
                        data=text,
                    )
        except aiohttp.ClientResponseError as e:
            self.logger.warning("There was an error while handling the request.")
            self.logger.exception(e)
            return DefectDojoResponse(
                message="There was an error while handling the request.",
                response_code=e.status,
                success=False,
            )


class DefectDojoResponse(object):
    """
    Container for all DefectDojo API responses, even errors.

    """

    def __init__(self, message, success, data=None, response_code=-1):
        self.message = message
        self.data = data
        self.success = success
        self.response_code = response_code
        self.logger = logger

    def __str__(self):
        if self.data:
            return str(self.data)
        else:
            return self.message

    def id(self):
        self.logger.debug("response_code" + str(self.response_code))
        if self.response_code == 400:  # Bad Request
            raise ValueError(
                "Object not created:"
                + json.dumps(
                    self.data, sort_keys=True, indent=4, separators=(",", ": ")
                )
            )
        return int(self.data["id"])

    def count(self):
        return self.data["count"]

    def data_json(self, pretty=False):
        """Returns the data as a valid JSON string."""
        if pretty:
            return json.dumps(
                self.data, sort_keys=True, indent=4, separators=(",", ": ")
            )
        else:
            return json.dumps(self.data)
