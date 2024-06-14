"""
Documentation

See also https://www.python-boilerplate.com/flask
"""
import os
from flask_cors import cross_origin

from flask import Flask, jsonify, request

from handlers import question_handler, fetch_user_information, handle_change_preferred_name, handle_change_legal_name, \
    handle_fetch_person, handle_get_worker_object, handle_get_subordinate_list, handle_get_available_shifts, \
    handle_shift_change

from Workday import Workday


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
    @cross_origin()  # Enable CORS for this specific endpoint
    def change_legal_name():
        """Expects a new name, wid and base64 encoded file."""
        req = request.get_json()

        bearer_token = request.headers.get('Authorization')
        bearer_token = bearer_token.split(' ')[-1] if bearer_token else ''
        if bearer_token != 'YnVkaW1hbg==':
            return {"error": "Unauthorized"}, 401

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

    @app.route("/fetch_worker_<field>", methods=['GET'])
    def get_worker_name(field):
        """Expects a new name, wid and base64 encoded file."""
        supported = ['legal_name', 'preferred_name']
        if field not in supported:
            return {"error": f"Currently only supports [{', '.join(supported)}]"}, 400

        req = request.args.to_dict()
        wid = req['wid']
        worker_info = fetch_user_information(wid=wid)

        if worker_info['status'] == 'fail':
            return jsonify(worker_info), 200
        person_id = worker_info['person']['id']

        return_data = handle_fetch_person(person_id=person_id, field=field)

        return jsonify(return_data), 200

    @app.route("/get_worker_details", methods=['GET'])
    def get_worker_object():
        req = request.args.to_dict()
        wid = req['wid']

        worker_info = handle_get_worker_object(wid=wid)

        return worker_info

    @app.route("/get_subordinate_list", methods=['GET'])
    def get_subordinate_list():
        req = request.args.to_dict()
        wid = req['wid']
        manager_list = handle_get_subordinate_list(wid=wid)

        if type(manager_list) is not list:
            return manager_list, 500

        return manager_list

    @app.route("/get_available_shifts", methods=['GET'])
    def get_available_shifts():
        req = request.args.to_dict()
        wid = req['wid']
        shifts_list = handle_get_available_shifts(wid=wid)

        return shifts_list

    @app.route("/shift_change", methods=['POST'])
    def shift_change():
        req = request.get_json()
        wid = req['wid']
        org_name = req['org']
        shift_id = req['shift_id']
        effective_date = req['effective_date']  # maybe date format

        try:
            response = handle_shift_change(wid=wid, org_name=org_name, shift_id=shift_id, effective_date=effective_date)

        except Exception as e:
            return {"status": "fail", "details": str(e)}, 400

        return jsonify(str(response)), 200

    # @app.route("/reset_workday_names", methods=['POST'])
    # def reset_workday_names():
    #
    #     return handle_reset_workday_names()
    #
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port)
