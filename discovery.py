import os

from ibm_watson.discovery_v2 import QueryLargePassages


class Discovery:

    def __init__(self):
        self.project_id = os.getenv("DISCOVERY_PROJECT_ID")
        self.url = os.getenv("DISCOVERY_URL")
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
            natural_language_query=query,
            passages=QueryLargePassages(find_answers=True)
        )

        return response.get_result()['results']
