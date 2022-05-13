# pylint:disable=logging-fstring-interpolation
"""Module to request trains."""

import json
import logging
import os
from typing import Tuple, Union

import requests

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


def get_session_tokens() -> Union[Tuple[int, str, str], Tuple[int, str]]:
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


def post_train(station_route: str) -> Tuple[int, str]:
    """
        Sends train request to REQUESTURL:3005 with aquired token and session parameters.
        returns: success_code, message
    """
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

    # if not train_class:
    train_class = repositories[1]
    if not station_route:
        station_route = stations[16]
    # FOR DEMO PURPOSES
    # if train_class not in repositories:
    #     return 1, "The specified train repository does not exist"
    # Does this make sense? There should be a better way lol
    stations_exists = False
    station_route = station_route.lower()
    final_route = ""
    error_message = ""

    for cur in stations.values():
        if cur.lower() in station_route:
            final_route += cur
            stations_exists = True
            station_route = station_route.replace(cur.lower(), '')
    if not stations_exists:
        return 1, "The provided station route does not contain any existing stations."
    if not station_route.strip():
        error_message = f" I couldn't find the following stations so I excluded them from the route: {' '.join(station_route.split())}"

    data = f"{{\n    \"trainclassid\": \"{train_class}\",\n    \"traininstanceid\": 1,\n    \"route\": \"{final_route}\"\n}}"

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
    print(json_response)
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
    return 2, result + error_message
