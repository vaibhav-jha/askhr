from discovery import Discovery
from utils import beautify_discovery_results
from prompts import prompt_template
from watsonx_ai import llama
import requests
from requests_oauth2client import BearerAuth
from os import getenv
import os


def question_handler(question):
    discovery_results = Discovery().fetch_docs(question)
    docs_for_llama_context = beautify_discovery_results(discovery_results)

    from langchain.prompts import PromptTemplate
    prompt = PromptTemplate.from_template(prompt_template,
                                          partial_variables={"context_documents": docs_for_llama_context})

    chain = prompt | llama

    response = chain.invoke({"question": question})

    return {"answer": response, "sources": ["WIP", "WIP"]}


def fetch_user_information(wid):
    bearer_token = getenv('WORKDAY_AUTH_TOKEN')
    wd_tenant_url = getenv('WORKDAY_TENANT_URL')
    wd_tenant_id = getenv('WORKDAY_TENANT_ID')
    wd_url = os.path.join(wd_tenant_url, 'staffing/v6/', wd_tenant_id, 'workers', wid)

    try:
        resp = requests.get(wd_url, auth=BearerAuth(bearer_token))
        resp_json = resp.json()
    except Exception as e:
        return {"status": "fail", "message": str(e)}

    if "error" in resp_json.keys():
        return {"status": "fail", "message": resp_json['error']}

    user_info = {}

    try:

        user_info['Name'] = resp_json['descriptor']
        user_info['Department'] = resp_json['primaryJob']['supervisoryOrganization']['descriptor']
        user_info['Role'] = resp_json['primaryJob']['businessTitle']

        service_url = os.path.join(wd_url, "serviceDates")
        resp = requests.get(service_url, auth=BearerAuth(bearer_token))
        resp_json = resp.json()

        user_info['ContinuousServiceDate'] = resp_json['data'][0]['continuousServiceDate']
        user_info['HireDate'] = resp_json['data'][0]['hireDate']

        user_info['status'] = 'success'
    except Exception as e:
        user_info['status'] = 'fail'
        user_info['message'] = str(e)

    return user_info
