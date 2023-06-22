# import pytest
# import yaml
#
# from app.exceptions import SecbotConfigError
# from app.secbot.config import SecbotConfig
# from app.workflow import SecbotWorkflow, SecbotWorkflowRunner
#
#
# def test_register_workflow():
#     yaml_string = """
#         version: "1.0"
#         components:
#             gitleaks:
#                 handler_name: gitleaks
#             defectdojo:
#                 handler_name: defectdojo
#             slack:
#                 handler_name: slack
#         jobs:
#           - name: Example jobs
#             rules:
#               gitlab:
#             scans:
#               - gitleaks
#             outputs:
#               - defectdojo
#             notifications:
#               - slack
#     """  # noqa: W291,E261
#     config = SecbotConfig(yaml.safe_load(yaml_string))
#     runner = SecbotWorkflowRunner(config=config)
#
#     workflow = SecbotWorkflow(input_name="gitlab")
#     runner.register_workflow(workflow)
#
#     assert "gitlab" in runner.workflows[0].input_name
#
#
# def test_workflow_validation_without_components():
#     yaml_string = """
#         version: "1.0"
#         components:
#             gitleaks:
#                 handler_name: gitleaks
#             defectdojo:
#                 handler_name: defectdojo
#             slack:
#                 handler_name: slack
#         jobs:
#           - name: Example jobs
#             rules:
#               gitlab:
#             scans:
#               - gitleaks
#             outputs:
#               - defectdojo
#             notifications:
#               - slack
#     """  # noqa: W291,E261
#     config = SecbotConfig(yaml.safe_load(yaml_string))
#     runner = SecbotWorkflowRunner(config=config)
#
#     runner.validate()
#     assert runner.is_validated is True
#
#
# def test_workflow_validation():
#     yaml_string = """
#         version: "1.0"
#         components:
#             gitleaks:
#                 handler_name: gitleaks
#             defectdojo:
#                 handler_name: defectdojo
#             slack:
#                 handler_name: slack
#         jobs:
#           - name: Example jobs
#             rules:
#               gitlab:
#             scans:
#               - gitleaks
#             outputs:
#               - defectdojo
#             notifications:
#               - slack
#     """  # noqa: W291,E261
#     config = SecbotConfig(yaml.safe_load(yaml_string))
#     runner = SecbotWorkflowRunner(config=config)
#
#     workflow = SecbotWorkflow(input_name="gitlab")
#     runner.register_workflow(workflow)
#
#     with pytest.raises(SecbotConfigError):
#         runner.validate()
