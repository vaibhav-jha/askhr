from prompts import BOT_, EOTurn_, ROLE_, ip_var_
from os import getenv
import requests
import os
import base64


def beautify_discovery_results(results):
    final_string = ""

    for i, result in enumerate(results):

        if i == 2:
            break

        docstring = ""
        docstring += f"Document Number: {i + 1}\n"
        docstring += f"Document Name: {result['extracted_metadata'].get('filename')}\n"
        docstring += f"Document Text:\n '''{result.get('text')}'''\n\n"

        docstring += "-" * 10
        docstring += "\n\n"

        final_string += docstring

    return final_string


def beautify_dict(any_dict):
    ret_str = ""
    for k, v in any_dict.items():
        ret_str += f"{k}: {v}\n"
    ret_str += '\n'
    return ret_str


def beautify_list(any_list):
    ret_str = "```"
    for i in any_list:
        if type(i) == dict:
            ret_str += beautify_dict(i)
        else:
            ret_str += f"\n{i}"
    ret_str += '```\n'
    return ret_str

def llamafy_assistant_chat(messages):
    ret_text = ""
    for message in messages:
        key = "u"
        if "a" in message.keys():
            role = "assistant"
            key = "a"
        else:
            role = "user"

        ret_text += f"{ROLE_(role)}\n{message[key]} {EOTurn_} "

    return ret_text


def get_wd_auth_from_refresh_token():
    client_secret = getenv("CLIENT_SECRET_UNLIMITED")
    client_id = getenv("CLIENT_ID_UNLIMITED")

    refresh_token = getenv("REFRESH_TOKEN_UNLIMITED")

    wd_tenant_base_url = "https://wd2-impl-services1.workday.com/"
    wd_tenant_id = getenv('WORKDAY_TENANT_ID')
    url = os.path.join(wd_tenant_base_url, 'ccx/oauth2/', wd_tenant_id, 'token')

    payload = f"grant_type=refresh_token&refresh_token={refresh_token}"

    # Combine username and password and encode in Base64
    auth_str = f"{client_id}:{client_secret}"
    auth_bytes = auth_str.encode('ascii')
    auth_base64 = base64.b64encode(auth_bytes).decode('ascii')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_base64}'
    }

    # Perform the GET request with basic authentication
    response = requests.request("GET", url, data=payload, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        # Print the response content
        return response.json()["access_token"]

    else:
        print(f"Request failed with status code: {response.status_code}")
        raise Exception("Bad request")


def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def to_lower_camel_case(snake_str):
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    camel_string = to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]


def modify_chat_history(chat_history, remove_trigger="Do you have any other question related to the leave policy", additional_remove_count=3):

    modified_chat_history = []

    i = 0
    total_chats = len(chat_history)

    while i < total_chats:
        text_block = chat_history[i]
        i += 1

        if "u" in text_block.keys():
            modified_chat_history.append(text_block)
            continue

        assistant_message = text_block['a']

        if remove_trigger in assistant_message:
            position = assistant_message.find(remove_trigger)
            assistant_message = assistant_message[:position-1]

            text_block['a'] = assistant_message

            i += additional_remove_count
        modified_chat_history.append(text_block)
    return  modified_chat_history






