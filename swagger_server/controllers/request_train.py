# pylint:disable=logging-fstring-interpolation
"""Module to request trains."""

import json
import logging
import os
from typing import Tuple

import requests  # type: ignore

stations = {
    0: "Bruegel",
    1: "Privat-Weber",
    2: "Private_TEST",
    3: "Private-Weber2",
    4: "Private-Welten",
    5: "HSMW",
    6: "Melanoma Station",
    7: "MDS Station",
    8: "PHT MDS Leipzig",
    9: "PHT IMISE LEIPZIG",
    10: "Station-UKA",
    11: "Station-UKK",
    12: "Station-UMG",
    13: "Station-UMG_temp",
    14: "aachenbeeck",
    15: "aachenmenzel"
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


def post_train(station_route: str) -> Tuple[int, str]:
    """
        Sends train request to REQUESTURL:3005 with aquired token and session parameters.
        station_route: Stations to visit MUST be separated by "," without space
        example: station_route="station_1,station_2"
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
    error_message = ""

    data = f"{{\n    \"trainclassid\": \"{train_class}\",\n    \"traininstanceid\": 1,\n    \"route\": \"{station_route}\"\n}}"

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
        print(f"Train could not be posted: {response.status_code}", flush=True)
        return 0, "Train request failed."

    response_id = json_response["id"]
    #pid = json_response["pid"]
    station_message = json_response["stationmessages"]
    route = json_response["route"]
    print(json_response)

    result = f"Successfully submitted train {train_class}. ID: {response_id}, route: "
    for step in route:
        result += step + " "
    result += ". Station messages: "
    for message in station_message:
        result += message + " "
    result += "."
    return 2, result + error_message
