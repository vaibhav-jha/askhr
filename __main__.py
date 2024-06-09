"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os

from flask import Flask, jsonify, request
from handlers import question_handler, fetch_user_information



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
        return question_handler(question=query)

    @app.route("/fetch_user", methods=['POST'])
    def fetch_user():
        req = request.get_json()

        if 'wid' not in req.keys():
            return jsonify({"error": "Missing wid "}), 400

        wid = req['wid']

        to_return = fetch_user_information(wid=wid, )

        ret_status = 200 if to_return['status'] == 'success' else 400

        return jsonify(to_return), ret_status

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
