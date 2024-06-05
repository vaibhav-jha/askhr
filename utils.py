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
