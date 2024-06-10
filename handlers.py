from discovery import Discovery
from utils import beautify_discovery_results, beautify_dict, beautify_list
from prompts import prompt_template
from watsonx_ai import llama
import requests
from requests_oauth2client import BearerAuth
from os import getenv
import os
from datetime import date

def question_handler(question, metadata=None):
    if metadata is None:
        metadata = {}

    user_details = "__Not Available__"
    chat_history = "__Not Available__"

    if metadata.get('discovery_results'):
        docs_for_llama_context = metadata.get('discovery_results')
    else:
        discovery_results = Discovery().fetch_docs(question)
        print(discovery_results)
        docs_for_llama_context = beautify_discovery_results(discovery_results)

    if 'user_details' in metadata:
        user_details = beautify_dict(metadata['user_details'])
    if 'chat_history' in metadata:
        chat_history = beautify_list(metadata['chat_history'])

    additional_info = f"Today's date is: {date.today().strftime('%B %d, %Y')}"

    from langchain.prompts import PromptTemplate
    prompt = PromptTemplate.from_template(prompt_template,
                                          partial_variables={"context_documents": docs_for_llama_context})

    chain = prompt | llama

    response = chain.invoke({"question": question,
                             "user_details": user_details,
                             "chat_history": chat_history,
                             "additional_info": additional_info,
                             })

    return {"answer": response, "sources": ["WIP", "WIP"]}


def fetch_user_information(wid, token=None):
    bearer_token = token or getenv('WORKDAY_AUTH_TOKEN')
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
