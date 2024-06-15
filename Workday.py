from utils import get_wd_auth_from_refresh_token
from os import getenv
import os
import requests
from requests_oauth2client import BearerAuth


class Workday:
    STAFFING = "staffing/v6"

    def __init__(self):
        self.base_url = getenv('WORKDAY_TENANT_URL')
        self.tenant_id = getenv('WORKDAY_TENANT_ID')
        self.auth_token = self._get_bearer_token()

    @classmethod
    def _get_bearer_token(cls, token=None):
        try:
            bearer_token = get_wd_auth_from_refresh_token()
        except Exception as e:
            bearer_token = token or getenv('WORKDAY_AUTH_TOKEN')

        return bearer_token

    def _build_url(self, resource, endpoint):
        return os.path.join(self.base_url, resource, self.tenant_id, endpoint)

    def __call__(self, url, method, **kwargs):
        try:
            headers = kwargs.get('headers')
            params = kwargs.get('params')
            if method == 'get':
                resp = requests.get(url, auth=BearerAuth(self.auth_token), params=params)
            elif method == 'patch':
                resp = requests.patch(url, auth=BearerAuth(self.auth_token), json=params)
            else:
                print(params)
                resp = requests.post(url, auth=BearerAuth(self.auth_token), json=params)

            resp_json = resp.json()
        except Exception as e:
            return {"status": "fail", "message": str(e)}, 500

        return resp_json, resp.status_code

    def get_worker(self, wid, **query_params):
        endpoint = os.path.join('workers', wid)
        wd_url = self._build_url(self.STAFFING, endpoint)

        return self.__call__(wd_url, 'get')

    def get_manager_reports(self, wid):
        endpoint = os.path.join('values/jobChangesGroup/workers/06a5fcbf1965100021db1f986d1400e7', wid)
        wd_url = self._build_url(self.STAFFING, endpoint)

        return self.__call__(wd_url, 'get')

    def get_org_chart(self, supervisory_org_id):
        endpoint = os.path.join('supervisoryOrganizations', supervisory_org_id, 'orgChart')
        wd_url = self._build_url(self.STAFFING, endpoint)

        return self.__call__(wd_url, 'get')

    def get_work_shifts(self, location_id):
        endpoint = os.path.join('values/jobChangesGroup/workShifts')
        wd_url = self._build_url(self.STAFFING, endpoint)

        return self.__call__(wd_url, 'get', params={"location": location_id})

    def post_job_change_request(self, wid, org_id, effective_date):

        endpoint = os.path.join("workers", wid, "jobChanges")
        wd_url = self._build_url(self.STAFFING, endpoint)

        params = {"supervisoryOrganization":
                      {"id": org_id},
                  "reason":
                      {"id": "1a81283cc05110020ad604439ef30000"},
                  "date": effective_date}

        return self.__call__(wd_url, 'post', params=params)

    def patch_job_position(self, job_change_request_id):
        endpoint = os.path.join("jobChanges", job_change_request_id, "position", job_change_request_id)
        wd_url = self._build_url(self.STAFFING, endpoint)

        params = {"createPosition": True}

        return self.__call__(wd_url, 'patch', params=params)

    def patch_location(self, job_change_request_id, shift_id):
        endpoint = os.path.join("jobChanges", job_change_request_id, "location", job_change_request_id)
        wd_url = self._build_url(self.STAFFING, endpoint)

        params = {
            "workShift": {
                "id": shift_id
            }
        }

        return self.__call__(wd_url, 'patch', params=params)

    def post_job_change_submit(self, job_change_request_id):
        endpoint = os.path.join("jobChanges", job_change_request_id, "submit")
        wd_url = self._build_url(self.STAFFING, endpoint)

        params = {}

        return self.__call__(wd_url, 'post', params=params)