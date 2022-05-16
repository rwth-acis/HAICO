# pylint:disable=logging-fstring-interpolation
"""Module to request trains."""

import json
import logging
import os
from typing import Tuple

import requests  # type: ignore

station_codes = {
    "station_aachen": "fe31acff-683a-4535-9408-afe5af718171",
    "station_cologne": "5e8a7b57-6cad-4336-a14c-859b8a0f5d13",
    "station_goettingen": "e6dff3b3-f258-4326-b7b0-2568a6d9bd02",
    "station_leipzig": "4ed9ed14-803a-4b82-9790-f168bbf353cb",
    "station_leipzig_imise": "259ea219-0f4d-479a-ab62-b47d06268204",
    "station_mittweida": "01059b0d-096f-4ea8-bb9b-993e0499e513",
    "station_beeck": "aachenbeeck",
    "station_menzel": "aachenmenzel"
}

repositories = {
    1: "train_class_repository/hello-world:latest"
}


def get_session_tokens() -> Tuple[int, str, str]:
    """
        Returns the session token and session state from REQUESTURL
        returns: success_code, token, session_state or success_code, failed_message
    """
    headers_token = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data_token = {
        'grant_type': 'password',
        'client_id': 'central-service',
        'username': os.environ['LOGINNAME'],
        'password': os.environ['PASSWORD']
    }

    url_request_enpoint = os.environ['REQUESTURL']
    url_token = f"{url_request_enpoint}:3006/auth/realms/pht/protocol/openid-connect/token"

    try:
        response_token = requests.post(
            url_token, headers=headers_token, data=data_token, allow_redirects=True)
    except Exception:  # pylint: disable=broad-except
        logging.error(
            f"Couldn't sent request to {url_token}. Module train_request.")
        return 0, "Request Failed.", ""

    try:
        json_response_token = json.loads(response_token.content)
    except Exception:  # pylint: disable=broad-except
        logging.error("Response not in expected format. Module train_request.")
        return 0, "Request failed.", ""
    if not "access_token" in json_response_token or not "session_state" in json_response_token:
        logging.error("No auth token and/or no session state were provided.")
        return 0, "Request failed.", ""
    token = json_response_token["access_token"]
    session_state = json_response_token["session_state"]
    return 2, token, session_state


def post_train(station_route: list) -> Tuple[int, str]:
    """
        Sends train request to REQUESTURL:3005 with aquired token and session parameters.
        station_route: Stations to visit
        returns: success_code, message
    """
    if not station_route:
        return 1, "No route specified."

    success_code, token, session_state = get_session_tokens()
    if success_code != 2:
        return 1, "Something went wrong requesting the train."

    url_request_enpoint = os.environ['REQUESTURL']
    url = f"{url_request_enpoint}:3005/centralservice/api/jobinfo"
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'pht_central_service_session': 's%' + session_state
    }

    # We currently only have one
    train_class = repositories[1]
    # translate station IDs to hard coded strings
    # as only existing stations can be selected we don't need to check if they exist
    final_route = ""
    for stat in station_route:
        if stat in station_codes:
            final_route += station_codes[stat] + ","
    # should not end in comma
    final_route = final_route[:-1]

    data = f"{{\n    \"trainclassid\": \"{train_class}\",\n    \"traininstanceid\": 1,\n    \"route\": \"{final_route}\"\n}}"  # pylint: disable=line-too-long

    try:
        response = requests.post(url, headers=headers,
                                 data=data, allow_redirects=True)
    except Exception:  # pylint: disable=broad-except
        logging.error(f"Couldn't send request to {url}. Module request_train.")
        return 0, "Train Request failed"

    try:
        print("Requestion train...", flush=True)
        json_response = json.loads(response.content)
        print(json_response, flush=True)
    except Exception:  # pylint: disable=broad-except
        logging.error("Response not in expected format. Module request_train.")
        return 0, "Train Request failed"
    if response.status_code != 201:
        # This means that the query was successful but the we probably got a 404
        print(f"Train could not be posted: {response.status_code}", flush=True)
        return 0, "Train request failed."

    response_id = json_response["id"]
    station_message = json_response["stationmessages"]

    result_message = f"Successfully submitted train {train_class}. ID: {response_id}, route: {station_route}"
    result_message += ". Station messages: "
    for message in station_message:
        result_message += message + " "
    result_message = result_message[:-1]
    result_message += "."
    return 2, result_message
