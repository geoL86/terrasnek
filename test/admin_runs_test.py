"""
Module for testing the Terraform Cloud API Endpoint: Admin Runs.
"""

from .base import TestTFCBaseTestCase

import time


class TestTFCAdminRuns(TestTFCBaseTestCase):
    """
    Class for testing the Terraform Cloud API Endpoint: Admin Runs.
    """

    _unittest_name = "admin-runs"

    def setUp(self):
        # Create an OAuth client for the test and extract it's ID
        oauth_client_payload = self._get_oauth_client_create_payload()
        oauth_client = self._api.oauth_clients.create(oauth_client_payload)
        self._oauth_client_id = oauth_client["data"]["id"]

        oauth_token_id = oauth_client["data"]["relationships"]["oauth-tokens"]["data"][0]["id"]
        _ws_payload = self._get_ws_with_vcs_create_payload(oauth_token_id)
        workspace = self._api.workspaces.create(_ws_payload)["data"]
        self._ws_id = workspace["id"]

        variable_payloads = [
            self._get_variable_create_payload(
                "email", self._test_email, self._ws_id),
            self._get_variable_create_payload(
                "org_name", "terrasnek_unittest", self._ws_id),
            self._get_variable_create_payload(
                "TFE_TOKEN", self._test_api_token, self._ws_id, category="env", sensitive=True)
        ]
        for payload in variable_payloads:
            self._api.variables.create(payload)

        create_run_payload = self._get_run_create_payload(self._ws_id)
        self._run = self._api.runs.create(create_run_payload)["data"]
        self._run_id = self._run["id"]

    def tearDown(self):
        self._api.workspaces.destroy(workspace_id=self._ws_id)

    def test_admin_runs(self):
        """
        Test the Admin Workspaces API endpoints: list, show, destroy.
        """
        # TODO: add params
        all_runs = self._api.admin_runs.list()["data"]

        found_run = False
        for run in all_runs:
            run_id = run["id"]
            if run_id == self._run_id:
                found_run = True
                break
        self.assertTrue(found_run)

        # Wait for it to plan
        self._logger.debug("Sleeping while plan half-executes...")
        time.sleep(1)
        self._logger.debug("Done sleeping.")

        # Force Cancel
        self._api.admin_runs.force_cancel(self._run_id)
        status_timestamps = self._api.runs.show(self._run_id)["data"]["attributes"]["status-timestamps"]
        while "force-canceled-at" not in status_timestamps:
            time.sleep(1)
            status_timestamps = \
                self._api.runs.show(self._run_id)["data"]["attributes"]["status-timestamps"]
        self.assertNotEqual(status_timestamps["force-canceled-at"], None)