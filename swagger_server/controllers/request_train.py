"""Module to rquest trains."""

import json
import logging
import os
from typing import Tuple, Union

import requests

stations = {
    1: "Bruegel",
    2: "Privat-Weber",
    3: "Private_TEST",
    4: "Private-Weber2",
    5: "Private-Welten",
    6: "HSMW",
    7: "Melanoma Station",
    8: "MDS Station",
    9: "PHT MDS Leipzig",
    10: "PHT IMISE LEIPZIG",
    11: "Station-UKA",
    12: "Station-UKK",
    13: "Station-UMG",
    14: "Station-UMG_temp",
    15: "aachenbeeck",
    16: "aachenmenzel"
}

repositories = {
    1: "train_class_repository/hello-world:latest"
}


def get_session_tokens() -> Union[Tuple[int, str, str], Tuple[int, str]]:
    """
        Returns the session token and session state from menzel.informatik.rwth-aachen.de:3006
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

    url_token = 'https://menzel.informatik.rwth-aachen.de:3006/auth/realms/pht/protocol/openid-connect/token'

    try:
        response_token = requests.post(
            url_token, headers=headers_token, data=data_token, allow_redirects=True)
    except Exception:  # pylint: disable=broad-except
        logging.error(
            f"Couldn't sent request to {url_token}. Module train_request.")
        return 0, "Request Failed."

    try:
        json_response_token = json.loads(response_token.content)
    except Exception:  # pylint: disable=broad-except
        logging.error("Response not in expected format. Module train_request.")
        return 0, "Request failed."
    if not json_response_token["access_token"] or not json_response_token["session_state"]:
        logging.error("No auth token and/or no session state were provided.")
        return 0, "Request failed."
    token = json_response_token["access_token"]
    session_state = json_response_token["session_state"]
    return 2, token, session_state


def post_train(train_class: str, station_route: list[str]) -> Tuple[int, str]:
    """
        Sends train request to https://menzel.informatik.rwth-aachen.de:3005 with aquired token and session parameters.
        returns: success_code, message
    """
    success_code, token, session_state = get_session_tokens()
    if success_code != 2:
        return 1, "Something went wrong requesting the train."

    url = "https://menzel.informatik.rwth-aachen.de:3005/centralservice/api/jobinfo"
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'pht_central_service_session': 's%' + session_state
    }

    if not train_class:
        train_class = repositories[1]
    if not station_route:
        station_route = stations[16]
    data = f"{{\n    \"trainclassid\": \"{train_class}\",\n    \"traininstanceid\": 1,\n    \"route\": \"{station_route}\"\n}}"

    try:
        response = requests.post(url,
                                 headers=headers, data=data, allow_redirects=True)
    except Exception:  # pylint: disable=broad-except
        logging.error(f"Couldn't send request to {url}. Module request_train.")
        return 0, "Train Request failed"

    try:
        json_response = json.loads(response.content)
    except Exception:  # pylint: disable=broad-except
        logging.error("Response not in expected format. Module request_train.")
        return 0, "Train Request failed"

    response_id = json_response["id"]
    pid = json_response["pid"]
    station_message = json_response["stationmessages"]
    route = json_response["route"]

    result = f"Successfully submitted train {train_class}. ID: {response_id}, pid: {pid}, route: "
    for step in route:
        result += step + " "
    result += ". Station messages: "
    for message in station_message:
        result += message + " "
    result += "."
    return 2, result
