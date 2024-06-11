from prompts import BOT_, EOTurn_, ROLE_, ip_var_


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
