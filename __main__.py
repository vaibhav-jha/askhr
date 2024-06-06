"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os

from flask import Flask, jsonify, request
from discovery import Discovery
from utils import beautify_discovery_results
from prompts import prompt_template
from watsonx_ai import llama


def create_app(config=None):
    app = Flask(__name__)

    # Definition of the routes. Put them into their own file. See also
    # Flask Blueprints: http://flask.pocoo.org/docs/latest/blueprints
    @app.route("/hello_world")
    def hello_world():
        return "Hello World"

    @app.route("/answer_question", methods=['POST'])
    def answer():
        req = request.get_json()

        query = req['question']

        discovery_results = Discovery().fetch_docs(query)
        docs_for_llama_context = beautify_discovery_results(discovery_results)

        from langchain.prompts import PromptTemplate
        prompt = PromptTemplate.from_template(prompt_template,
                                              partial_variables={"context_documents": docs_for_llama_context})

        chain = prompt | llama

        response = chain.invoke({"question": query})

        return {"summary": response}

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
