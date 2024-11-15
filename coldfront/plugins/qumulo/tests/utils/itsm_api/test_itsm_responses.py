import json

from django.test import TestCase

from unittest import skip


class TestImportDataFromItsm(TestCase):

    def mock_itsm_response_body(self) -> str:
        with open("mock_itsm_response_body_service_provision_found.json", "r") as file:
            return json.load(file)

    def mock_itsm_response_body_not_found(self) -> str:
        with open(
            "mock_itsm_response_body_service_provision_not_found.json", "r"
        ) as file:
            return json.load(file)
    @skip("Test incomplete")
    def test_service_provision_found(self) -> None:
        response_body = self.mock_itsm_response_body()

    @skip("Test incomplete")
    def test_service_provision_not_found(self) -> None:
        response_body = self.mock_itsm_response_body_not_found()
