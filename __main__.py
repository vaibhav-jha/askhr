"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os

from flask import Flask, jsonify, request
from handlers import question_handler, fetch_user_information, handle_change_preferred_name, handle_change_legal_name
import langsmith_setup

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

        metadata = {}
        for key in req.keys():
            metadata[key] = req[key]

        return question_handler(question=query, metadata=metadata)

    @app.route("/fetch_user", methods=['POST'])
    def fetch_user():
        req = request.get_json()

        if 'wid' not in req.keys():
            return jsonify({"error": "Missing wid "}), 400

        wid = req['wid']
        wd_token = request.headers.get('workday-access-token')

        to_return = fetch_user_information(wid=wid, token=wd_token)

        ret_status = 200 if to_return['status'] == 'success' else 400

        return jsonify(to_return), ret_status

    @app.route("/change_preferred_name", methods=['POST'])
    def change_preferred_name():
        req = request.get_json()

        if 'name' not in req:
            return {'error': "Missing name object"}, 400
        else:
            if all([x not in req['name'] for x in ['first_name', 'last_name', 'middle_name']]):
                return {'error': "Empty name object - {}"}, 400

        try:
         to_return = handle_change_preferred_name(req['wid'], req['name'])
        except Exception as e:
            return {'error': str(e)}, 500

        return jsonify(str(to_return)), 200

    @app.route("/change_legal_name", methods=['POST'])
    def change_legal_name():
        """Expects a new name, wid and base64 encoded file."""
        req = request.get_json()

        if 'name' not in req:
            return {'error': "Missing name object"}, 400
        else:
            if all([x not in req['name'] for x in ['first_name', 'last_name', 'middle_name']]):
                return {'error': "Empty name object - {}"}, 400

        try:
            to_return = handle_change_legal_name(req['wid'], req['name'], req['additional_data'])
        except Exception as e:
            return {'error': str(e)}, 500

        return jsonify(str(to_return)), 200

    return app





if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
