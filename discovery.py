import os

from ibm_watson.discovery_v2 import QueryLargePassages


class Discovery:

    def __init__(self):
        self.project_id = "2d4911fa-2bc3-4537-8890-bd035a90898c"
        self.url = "https://api.us-south.discovery.watson.cloud.ibm.com/instances/fe583531-dfa6-46e0-afd4-ad5f0a0756b3"
        self.api_key = os.getenv("DISCOVERY_API_KEY")

        self.instance = self.__get_instance__()

    def __get_instance__(self):
        from ibm_watson import DiscoveryV2
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

        authenticator = IAMAuthenticator(self.api_key)
        discovery = DiscoveryV2(
            version='2024-06-04',
            authenticator=authenticator
        )

        discovery.set_service_url(self.url)

        return discovery

    def fetch_docs(self, query: str):
        response = self.instance.query(
            project_id=self.project_id,
            natural_language_query='What is the difference between FMLA and PFL',
            passages=QueryLargePassages(find_answers=True)
        )

        return response.get_result()['results']
