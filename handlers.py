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


from Workday import Workday


def handle_get_subordinate_list(wid):
    ''' Fetches eligible managers '''
    try:
        wd = Workday()
        worker_response = wd.get_worker(wid)

        worker = worker_response[0]

        # Capture
        supervisory_id = worker["primaryJob"]["supervisoryOrganization"]["id"]
        country = worker["primaryJob"]["location"]["country"]["ISO_3166-1_Alpha-3_Code"]

        orgs_response = wd.get_org_chart(supervisory_id)
        orgs = orgs_response[0]['data'][0]['subordinates']
        filtered_orgs = []
        for org in orgs:
            manager_name = org["managers"][0]["descriptor"]
            manager_wid = org["managers"][0]["id"]

            manager_worker = wd.get_worker(manager_wid)[0]
            manager_country = manager_worker["primaryJob"]["location"]["country"]["ISO_3166-1_Alpha-3_Code"]

            if manager_country == country:
                filtered_orgs.append(dict(name=manager_name, org=manager_wid))
    except Exception as e:
        return {"status": "fail", "message": str(e)}

    return filtered_orgs


def handle_get_available_shifts(wid):
    worker_object = handle_get_worker_object(wid)
    location_id = worker_object["primaryJob"]["location"]["id"]

    bearer_token = _get_bearer_token()
    wd_tenant_url = getenv('WORKDAY_TENANT_URL')
    wd_tenant_id = getenv('WORKDAY_TENANT_ID')
    url = os.path.join(wd_tenant_url, 'staffing/v6/', wd_tenant_id, 'values/jobChangesGroup/workShifts')

    try:
        resp = requests.get(url, auth=BearerAuth(bearer_token), params={"location": location_id})
        resp_json = resp.json()

        shifts_list = resp_json["data"]

        ret_list = []

        for shift in shifts_list:
            ret_list.append({
                "name": shift["descriptor"],
                "id": shift["id"]
            })

    except Exception as e:
        return {"status": "fail", "message": str(e)}

    return ret_list


def handle_get_worker_object(wid):
    bearer_token = _get_bearer_token()
    wd_tenant_url = getenv('WORKDAY_TENANT_URL')
    wd_tenant_id = getenv('WORKDAY_TENANT_ID')
    wd_url = os.path.join(wd_tenant_url, 'staffing/v6/', wd_tenant_id, 'workers', wid)

    try:
        resp = requests.get(wd_url, auth=BearerAuth(bearer_token))
        resp_json = resp.json()
    except Exception as e:
        return {"status": "fail", "message": str(e)}

    return resp_json


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


def _get_person_by_wid(wid, field):
    try:
        worker_info = fetch_user_information(wid=wid)
        person_id = worker_info['person']['id']
        person = handle_fetch_person(person_id=person_id, field=field)
    except:
        raise Exception(f"Couldnt find person object for worker {wid} ")

    return person


# def handle_change_preferred_name(wid, to_name):
#     from zeep import Client
#     from zeep.wsse.username import UsernameToken
#
#     # GET CURRENT NAME OBJECT
#     try:
#         person = _get_person_by_wid(wid=wid, field="preferred_name")
#         fn, mn, ln = person['first_name'], person["middle_name"], person['last_name']
#     except Exception as e:
#         print(e)
#         fn, mn, ln = "", "", ""
#
#     request_body = json.loads(open('soap_requests.json', 'r').read())
#     request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Person_Reference']['ID']['_value_1'] = wid
#
#     fn, mn, ln = to_name.get('first_name') or fn, to_name.get('middle_name') or mn, to_name.get('last_name') or ln
#
#     request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['First_Name'] = fn
#     request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['Middle_Name'] = mn
#     request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['Last_Name'] = ln
#
#     un, pw = getenv('WORKDAY_ADMIN_USERNAME'), getenv('WORKDAY_ADMIN_PASSWORD')
#     wsdl_url = "https://wd2-impl-services1.workday.com/ccx/service/ibmsrv_dpt1/Human_Resources/v42.1?wsdl"
#
#     client = Client(wsdl_url, wsse=UsernameToken(un, pw))
#
#     response = client.service.Change_Preferred_Name(**request_body["Change_Preferred_Name"])
#
#     return response


# def handle_change_legal_name(wid, to_name, additional_data):
#     from zeep import Client
#     from zeep.wsse.username import UsernameToken
#
#     # GET CURRENT NAME OBJECT
#     try:
#         person = _get_person_by_wid(wid=wid, field="legal_name")
#         fn, mn, ln = person['first_name'], person["middle_name"], person['last_name']
#     except Exception as e:
#         print(e)
#         fn, mn, ln = "", "", ""
#
#     if type(to_name) == str:
#         fn, ln = to_name.split(' ')[0] or fn, to_name.split(' ')[-1] or ln
#         mn = to_name.split(' ')[1] if len(to_name.split(' ') == 3) else '' or mn
#     else:
#         fn, mn, ln = to_name.get('first_name') or fn, to_name.get('middle_name') or mn, to_name.get('last_name') or ln
#
#     request_body = json.loads(open('soap_requests.json', 'r').read())
#
#     request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Person_Reference']['ID']['_value_1'] = wid
#     request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['First_Name'] = fn
#     request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['Middle_Name'] = mn
#     request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['Last_Name'] = ln
#
#     request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
#         'File'] = additional_data.get('file')
#     request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
#         'File_Name'] = additional_data.get('file_name')
#     request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
#         'Event_Attachment_Description'] = additional_data.get('event_attachment_description')
#     request_body['Change_Legal_Name']['Business_Process_Parameters']['Business_Process_Attachment_Data'][
#         'Content_Type'] = additional_data.get('content_type')
#
#     un, pw = getenv('WORKDAY_ADMIN_USERNAME'), getenv('WORKDAY_ADMIN_PASSWORD')
#     wsdl_url = "https://wd2-impl-services1.workday.com/ccx/service/ibmsrv_dpt1/Human_Resources/v42.1?wsdl"
#
#     client = Client(wsdl_url, wsse=UsernameToken(un, pw))
#
#     response = client.service.Change_Legal_Name(**request_body["Change_Legal_Name"])
#
#     return response


def handle_fetch_person(person_id, field):
    wd_tenant_url = getenv('WORKDAY_TENANT_URL')
    wd_tenant_id = getenv('WORKDAY_TENANT_ID')
    wd_url = os.path.join(wd_tenant_url, 'person/v4/', wd_tenant_id, 'people', person_id, to_lower_camel_case(field))

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


## ++++++++ SOAP REQUESTS

def handle_change_preferred_name(wid, to_name, force_all=False):
    from zeep import Client
    from zeep.wsse.username import UsernameToken

    # GET CURRENT NAME OBJECT
    try:
        person = _get_person_by_wid(wid=wid, field="preferred_name")
        fn, mn, ln = person['first_name'], person["middle_name"], person['last_name']
    except Exception as e:
        print(e)
        fn, mn, ln = "", "", ""

    request_body = json.loads(open('soap_requests.json', 'r').read())
    request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Person_Reference']['ID']['_value_1'] = wid

    if force_all:
        fn, mn, ln = to_name.get('first_name'), to_name.get('middle_name'), to_name.get('last_name')
    else:
        fn, mn, ln = to_name.get('first_name') or fn, to_name.get('middle_name') or mn, to_name.get('last_name') or ln

    request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['First_Name'] = fn
    request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['Middle_Name'] = mn
    request_body['Change_Preferred_Name']['Change_Preferred_Name_Data']['Name_Data']['Last_Name'] = ln

    un, pw = getenv('WORKDAY_ADMIN_USERNAME'), getenv('WORKDAY_ADMIN_PASSWORD')
    wsdl_url = "https://wd2-impl-services1.workday.com/ccx/service/ibmsrv_dpt1/Human_Resources/v42.1?wsdl"

    client = Client(wsdl_url, wsse=UsernameToken(un, pw))

    response = client.service.Change_Preferred_Name(**request_body["Change_Preferred_Name"])

    return response


def handle_change_legal_name(wid, to_name, additional_data, force_all=False):
    from zeep import Client
    from zeep.wsse.username import UsernameToken

    # GET CURRENT NAME OBJECT
    try:
        person = _get_person_by_wid(wid=wid, field="legal_name")
        fn, mn, ln = person['first_name'], person["middle_name"], person['last_name']
    except Exception as e:
        print(e)
        fn, mn, ln = "", "", ""

    if type(to_name) == str:
        fn, ln = to_name.split(' ')[0] or fn, to_name.split(' ')[-1] or ln
        mn = to_name.split(' ')[1] if len(to_name.split(' ') == 3) else '' or mn
    else:
        if force_all:
            fn, mn, ln = to_name.get('first_name'), to_name.get('middle_name'), to_name.get('last_name')
        else:
            fn, mn, ln = to_name.get('first_name') or fn, to_name.get('middle_name') or mn, to_name.get(
                'last_name') or ln

    request_body = json.loads(open('soap_requests.json', 'r').read())

    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Person_Reference']['ID']['_value_1'] = wid
    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['First_Name'] = fn
    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['Middle_Name'] = mn
    request_body['Change_Legal_Name']['Change_Legal_Name_Data']['Name_Data']['Last_Name'] = ln

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


def handle_shift_change(wid, new_manager_id, shift_id, effective_date):
    ## FIND ORG ID FROM MANAGER ID
    try:
        wd = Workday()

        manager_worker = wd.get_worker(new_manager_id)[0]

        # Find new manager's org id
        manager_supervisory_org_id = manager_worker["primaryJob"]["supervisoryOrganization"]["id"]
        orgs_under_supervisory_org = wd.get_org_chart(manager_supervisory_org_id)[0]
        orgs = orgs_under_supervisory_org['data'][0]['subordinates']
        filtered_orgs = [org for org in orgs if org['managers'][0]['id'] == new_manager_id]
        manager_org_id = filtered_orgs[0]['id']

        # JOB change request
        job_change_req_response = wd.post_job_change_request(wid=wid, org_id=manager_org_id,
                                                             effective_date=effective_date)
        job_change_id = job_change_req_response[0]['id']

        # Add new position True
        wd.patch_job_position(job_change_id)

        # Add shift
        wd.patch_location(job_change_request_id=job_change_id, shift_id=shift_id)

        # Submit request
        final_response = wd.post_job_change_submit(job_change_request_id=job_change_id)

    except Exception as e:
        return {"status": "fail", "message": str(e)}

    return final_response[0]
