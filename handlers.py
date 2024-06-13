import json

from discovery import Discovery
from utils import beautify_discovery_results, beautify_dict, llamafy_assistant_chat, get_wd_auth_from_refresh_token, \
    to_lower_camel_case
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
        docs_for_llama_context = beautify_discovery_results(discovery_results)

    if 'user_details' in metadata:
        user_details = beautify_dict(metadata['user_details'])
    if 'chat_history' in metadata:
        chat_history = llamafy_assistant_chat(metadata['chat_history'])

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


def _get_bearer_token(token=None):
    try:
        bearer_token = get_wd_auth_from_refresh_token()
    except Exception as e:
        bearer_token = token or getenv('WORKDAY_AUTH_TOKEN')

    return bearer_token


def fetch_user_information(wid, token=None):
    bearer_token = _get_bearer_token(token)

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

        user_info['person'] = resp_json['person']

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


def handle_change_preferred_name(wid, to_name):
    from zeep import Client
    from zeep.wsse.username import UsernameToken

    request_body = json.loads(open('soap_requests.json', 'r').read())

    request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Person_Reference']['ID']['_value_1'] = wid

    fn, mn, ln = to_name.get('first_name'), to_name.get('middle_name'), to_name.get('last_name')

    if fn:
        request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['First_Name'] = to_name.get(
            'first_name')
    if to_name.get('middle_name'):
        request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['Middle_Name'] = to_name.get(
            'middle_name')
    if to_name.get('last_name'):
        request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['Last_Name'] = to_name.get(
            'last_name')

    un, pw = getenv('WORKDAY_ADMIN_USERNAME'), getenv('WORKDAY_ADMIN_PASSWORD')
    wsdl_url = "https://wd2-impl-services1.workday.com/ccx/service/ibmsrv_dpt1/Human_Resources/v42.1?wsdl"

    client = Client(wsdl_url, wsse=UsernameToken(un, pw))

    response = client.service.Change_Preferred_Name(**request_body["Change_Preferred_Name"])

    return response


def handle_change_legal_name(wid, to_name, additional_data):
    from zeep import Client
    from zeep.wsse.username import UsernameToken

    request_body = json.loads(open('soap_requests.json', 'r').read())

    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Person_Reference']['ID']['_value_1'] = wid
    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['First_Name'] = to_name.get('first_name')
    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['Middle_Name'] = to_name.get('middle_name')
    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['Last_Name'] = to_name.get('last_name')

    request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
        'File'] = additional_data.get('file')
    request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
        'File_Name'] = additional_data.get('file_name')
    request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
        'Event_Attachment_Description'] = additional_data.get('event_attachment_description')
    request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
        'Content_Type'] = additional_data.get('content_type')

    un, pw = getenv('WORKDAY_ADMIN_USERNAME'), getenv('WORKDAY_ADMIN_PASSWORD')
    wsdl_url = "https://wd2-impl-services1.workday.com/ccx/service/ibmsrv_dpt1/Human_Resources/v42.1?wsdl"

    client = Client(wsdl_url, wsse=UsernameToken(un, pw))

    response = client.service.Change_Legal_Name(**request_body["Change_Legal_Name"])

    return response


def handle_fetch_person(person_id, object):
    wd_tenant_url = getenv('WORKDAY_TENANT_URL')
    wd_tenant_id = getenv('WORKDAY_TENANT_ID')
    wd_url = os.path.join(wd_tenant_url, 'person/v4/', wd_tenant_id, 'people', person_id, to_lower_camel_case(object))

    bearer_token = _get_bearer_token()

    try:
        resp = requests.get(wd_url, auth=BearerAuth(bearer_token))
        resp_json = resp.json()
    except Exception as e:
        return {"status": "fail", "message": str(e)}

    details_return = {
        'first_name': resp_json['data'][0].get('first') or '',
        'last_name': resp_json['data'][0].get('primary') or '',
        'middle_name': resp_json['data'][0].get('middle') or '',
    }

    return details_return
