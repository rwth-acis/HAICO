## pylint:disable = logging-fstring-interpolation
"""
    This module queries the blazegraph server periodically and checks for updates on certain events.
    It is also handling notifications.
"""
import logging
import os
import threading
from typing import Callable, List

import requests
from flask import render_template

from . import query


ont_pref = ""
"""
EMAILS stores which emails want to receive messages for which events and for which stations/ trains
e.g EMAILS = {
	"email3": [{
		"id": "train1",
		"events": ["ERROR_TRAIN"]
	}, {
		"id": "station2",
		"events": ["READY_STATION", "FINISHED_STATION"]
	}]
}
ERROR_(TRAIN/STATION), FINISHED_(TRAIN/STATION), and READY_STATION store which trains/ stations need to be queried for
(ERROR/FINISHED/READY)_(TRAIN/STATION)_LAST stores the last seen events for each train/ station
e.g. ERROR_TRAIN_LAST = {
    "train6": ["Error message on station8.", "Error message on station0."]
}
READY_STATION_LAST = {
    "station2": ["train4"],
    "station9": ["train3", "train00"]
}
FINISHED_TRAIN_LAST = {
	"train2": {
		"visited": ["station1"],
		"not_visited": ["station9", "station7"],
		"route": [
			[1, "station1"],
			[2, "station9"],
			[3, "station3"],
			[4, "station9"]
		]
	}
}
"""
EMAILS = {}
ERROR_TRAIN = []
ERROR_TRAIN_LAST = {}
FINISHED_TRAIN = []
FINISHED_TRAIN_LAST = {}
# notification for when a train just arrived at a station
READY_STATION = []
READY_STATION_LAST = {}
FINISHED_STATION = []
FINISHED_STATION_LAST = {}
ERROR_STATION = []
ERROR_STATION_LAST = {}


def start_polling(interval_sec: int):
    logging.info(f"Started polling. Interval: every {interval_sec} seconds.")
    set_interval(poll_server, interval_sec)
    return


def get_response(response: dict, target: str, error_message: bool = False) -> List[str]:
    if not response or not response["results"]["bindings"]:
        return []
    response_list = []
    for current in response["results"]["bindings"]:
        to_add = current[target]["value"]
        if error_message:
            to_add += f": {current['error']['value']}."
        response_list.append(to_add)
    return response_list


def poll_server():
    """
        Queries the blazegraph server for updates.
        Only queries those stations/ trains for which monitoring is requested.
    """
    logging.info("Polling ...")
    # error_train
    for train_id in ERROR_TRAIN:
        query_error_train = f"""
            SELECT ?station ?error WHERE {{
                {ont_pref}:{train_id} a pht:Train .
                {ont_pref}:{train_id} pht:execution ?exec .
                ?exec pht:event ?ev .
                ?ev a pht:StationErrorEvent .
                ?ev pht:station ?station .
                ?ev pht:message ?error .
            }}
        """
        response_error_train = query.blazegraph_query(query_error_train)
        list_error_train = get_response(response_error_train, "station", True)
        for item in list_error_train:
            if item not in ERROR_TRAIN_LAST[train_id]:
                ERROR_TRAIN_LAST[train_id].append(item)
                train_error(train_id, item)

    # finished_train
    # assumption: there's only ever one train with train id train_id running at the same time
    for train_id in FINISHED_TRAIN:
        query_finished_train = f"""
            SELECT ?station WHERE {{
                {ont_pref}:{train_id} a pht:Train .
                {ont_pref}:{train_id} pht:execution ?exec .
                ?exec pht:event ?ev .
                ?ev a pht:FinishedRunningAtStationEvent .
                ?ev pht:station ?station .
            }}
        """
        response_finished_train = query.blazegraph_query(query_finished_train)
        list_finished_train = get_response(response_finished_train, "station")
        for item in list_finished_train:
            if item not in FINISHED_TRAIN_LAST[train_id]["visited"]:
                if item not in FINISHED_TRAIN_LAST[train_id]["not_visited"]:
                    FINISHED_TRAIN_LAST[train_id]["not_visited"].remove(item)
                FINISHED_TRAIN_LAST[train_id]["visited"].append(item)
                if item == FINISHED_TRAIN_LAST[train_id]["route"][-1][1]:
                    train_finished_route(train_id)
                else:
                    # maybe the train was rejected on the last station(s)
                    query_rej = f"""
                        SELECT ?station WHERE {{
                            {ont_pref}:{train_id} a pht:Train .
                            {ont_pref}:{train_id} pht:execution ?exec .
                            ?exec pht:event ?ev .
                            ?ev a pht:StationRejectedEvent .
                            ?ev pht:station ?station .
                        }}
                    """
                    response_rej = query.blazegraph_query(query_rej)
                    if response_rej and response_rej["results"]["bindings"]:
                        for current in response_rej["results"]["bindings"]:
                            station = current["results"]["bindings"]
                            if station in FINISHED_TRAIN_LAST[train_id]["not_visited"]:
                                FINISHED_TRAIN_LAST[train_id]["not_visited"].remove(
                                    station)
                                FINISHED_TRAIN_LAST[train_id]["visited"].append(
                                    station)
                    if not FINISHED_TRAIN_LAST[train_id]["not_visited"]:
                        train_finished_route(train_id)

    # ready_station
    for station_id in READY_STATION:
        query_ready_station = f"""
            SELECT ?train WHERE {{
                    {ont_pref}:{station_id} a pht:Station .
                    ?train a pht:Train .
                    ?train pht:execution ?exec .
                    ?exec pht:plannedRouteStep ?step .
                    ?step pht:station {ont_pref}:{station_id} .
                    ?exec pht:event ?ev .
                    ?ev a pht:StartedTransmissionEvent .
                    ?ev pht:station {ont_pref}:{station_id} .
                    FILTER NOT EXISTS {{
                        ?exec pht:event ?ev .
                        ?ev a pht:StartedRunningAtStationEvent .
                        ?ev pht:station {ont_pref}:{station_id} .
                    }}
                    
            }}
        """
        response_ready_station = query.blazegraph_query(query_ready_station)
        list_ready_station = get_response(response_ready_station, "train")
        for train in list_ready_station:
            if train not in READY_STATION_LAST[station_id]:
                READY_STATION_LAST[station_id].append(train)
                train_ready_on_station(station_id, train_id)

    # finished_station
    for station_id in FINISHED_STATION:
        query_finished_station = f"""
            SELECT ?train WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                ?train pht:execution ?exec .
                ?exec pht:event ?ev .
                ?ev a pht:FinishedRunningAtStationEvent .
                ?ev pht:station {ont_pref}:{station_id} .
            }}
        """
        response_finished_station = query.blazegraph_query(
            query_finished_station)
        list_finished_station = get_response(
            response_finished_station, "train")
        for train in FINISHED_STATION_LAST[station_id]:
            if train not in list_finished_station:
                FINISHED_STATION_LAST[station_id].append(train)
                train_finished_on_station(station_id, train)

    # error_station
    for station_id in ERROR_STATION:
        query_error_station = f"""
            SELECT ?error ?train WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                ?train a pht:Train .
                ?train pht:execution ?exec .
                ?exec pht:event ?ev .
                ?ev a pht:StationErrorEvent .
                ?ev pht:station {ont_pref}:{station_id} .
                ?ev pht:message ?error .
            }}
        """
        response_error_station = query.blazegraph_query(query_error_station)
        list_error_station = get_response(
            response_error_station, "train", True)
        for item in list_error_station:
            if item not in ERROR_STATION_LAST[station_id]:
                ERROR_STATION_LAST[station_id].append(item)
                station_error(station_id, item)

    logging.info("...done")


def set_interval(func: Callable[[None], None], sec: int):
    def func_wrapper():
        set_interval(func, sec)
        func()
    timer = threading.Timer(sec, func_wrapper)
    timer.start()
    return timer


def set_notification(event: str, target_id: str, email: str):
    """
        Adds email to notification list.
        Updates the corresponding lists and dicts and queries last state.
        event: event to listen for
        target_id: id of the piece to be monitored
        email: user that wants to receive updates
    """
    if not email in EMAILS:
        EMAILS[email] = [{"id": target_id, "events": [event]}]
    else:
        id_exists = False
        for cur_entry in EMAILS[email]:
            if cur_entry["id"] == target_id:
                id_exists: True
                if event in cur_entry["events"]:
                    logging.warning(
                        f"Notifications for this email, ID, and event are already set ({email} {event} {target_id})")
                    return 1
                cur_entry["events"].append(event)
                break
        if not id_exists:
            EMAILS[email].append({"id": target_id, "events": [event]})
    if event == "ERROR_TRAIN":
        if not target_id in ERROR_TRAIN:
            ERROR_TRAIN.append(target_id)
            query_error_train = f"""
                SELECT ?station ?error WHERE {{
                    {ont_pref}:{target_id} a pht:Train .
                    {ont_pref}:{target_id} pht:execution ?exec .
                    ?exec pht:event ?ev .
                    ?ev a pht:StationErrorEvent .
                    ?ev pht:station ?station .
                    ?ev pht:message ?error .
                }}
            """
            response_error_train = query.blazegraph_query(query_error_train)
            ERROR_TRAIN_LAST[target_id] = get_response(
                response_error_train, "station", True)
    elif event == "FINISHED_TRAIN":
        if not target_id in FINISHED_TRAIN:
            FINISHED_TRAIN.append(target_id)
            query_finished_train = f"""
                SELECT ?station WHERE {{
                    {ont_pref}:{target_id} a pht:Train .
                    {ont_pref}:{target_id} pht:execution ?exec .
                    ?exec pht:event ?ev .
                    ?ev a pht:FinishedRunningAtStationEvent .
                    ?ev pht:station ?station .
                }}
            """
            response_finished_train = query.blazegraph_query(
                query_finished_train)
            list_finished_train = get_response(
                response_finished_train, "station")

            query_route = f"""
            SELECT ?step ?station WHERE {{
                {ont_pref}:{target_id} a pht:Train .
                {ont_pref}:{target_id} pht:execution ?exec .
                ?exec pht:plannedRouteStep ?plan .
                ?plan pht:station ?station .
                ?plan pht:stepNumber ?step .
            }}
            """
            response_route = query.blazegraph_query(query_route)
            step_station = []
            for current in response_route["results"]["bindings"]:
                step = current["step"]["value"]
                station = current["station"]["value"]
                step_station.extend([[step, station]])

            sorted_values = sorted(step_station, key=lambda c: c[0])

            not_visited = []
            for station, _ in sorted_values:
                if station not in list_finished_train:
                    not_visited.append(station)
            FINISHED_TRAIN_LAST[target_id] = {
                "visited": list_finished_train, "route": sorted_values, "not_visited": not_visited}
    elif event == "READY_STATION":
        if not target_id in READY_STATION:
            READY_STATION.append(target_id)
            query_ready_station = f"""
                SELECT ?train WHERE {{
                    {ont_pref}:{target_id} a pht:Station .
                    ?train a pht:Train .
                    ?train pht:execution ?exec .
                    ?exec pht:plannedRouteStep ?step .
                    ?step pht:station {ont_pref}:{target_id} .
                    ?exec pht:event ?ev .
                    ?ev a pht:StartedTransmissionEvent .
                    ?ev pht:station {ont_pref}:{target_id} .
                    FILTER NOT EXISTS {{
                        ?exec pht:event ?ev .
                        ?ev a pht:StartedRunningAtStationEvent .
                        ?ev pht:station {ont_pref}:{target_id} .
                    }}
                    
                }}
            """
            response_ready_station = query.blazegraph_query(
                query_ready_station)
            READY_STATION_LAST[target_id] = get_response(
                response_ready_station, "train")
    elif event == "FINISHED_STATION":
        if not target_id in FINISHED_STATION:
            FINISHED_STATION.append(target_id)
            query_finished_station = f"""
                SELECT ?train WHERE {{
                    {ont_pref}:{target_id} a pht:Station .
                    ?train pht:execution ?exec .
                    ?exec pht:event ?ev .
                    ?ev a pht:FinishedRunningAtStationEvent .
                    ?ev pht:station {ont_pref}:{target_id} .
                }}
            """
            response_finished_station = query.blazegraph_query(
                query_finished_station)
            FINISHED_STATION_LAST[target_id] = get_response(
                response_finished_station, "train")
    elif event == "ERROR_STATION":
        if not target_id in ERROR_STATION:
            ERROR_STATION.append(target_id)
            query_error_station = f"""
                SELECT ?error ?train WHERE {{
                    {ont_pref}:{target_id} a pht:Station .
                    ?train a pht:Train .
                    ?train pht:execution ?exec .
                    ?exec pht:event ?ev .
                    ?ev a pht:StationErrorEvent .
                    ?ev pht:station {ont_pref}:{target_id} .
                    ?ev pht:message ?error .
                }}
            """
            response_error_station = query.blazegraph_query(
                query_error_station)
            ERROR_STATION_LAST[target_id] = get_response(
                response_error_station, "train", True)
    else:
        logging.error("Event not recognized in poll.py set_notification")
        return 0
    logging.info(
        f"Successfully updated notification information for {email} {event} {target_id}.")
    return 2


def remove_notification(event: str, target_id: str, email: str):
    """
        Removes email from notification list.
        Updates the corresponding lists and dicts and queries last state.
        event: event to be removes
        target_id: corresponding id
        email: user that no longer wants to receive updates
    """
    if not email in EMAILS:
        logging.warning(
            f"""Attempting to remove notifications for a email which didn't subscribe to any notifications
            ({email} {event} {target_id}).""")
        return 1
    id_subscribed = False
    event_subscribed = False
    for cur_entry in EMAILS[email]:
        if target_id == cur_entry["id"]:
            id_subscribed = True
            if event in cur_entry["events"]:
                event_subscribed = True
                cur_entry["events"].remove(event)
                if not cur_entry["events"]:
                    # this email doesn't want to receive any more notifications for the given ID
                    EMAILS[email].remove(cur_entry)
                break

    if not id_subscribed:
        logging.warning(
            f"Attempting to remove notifications for an ID for which no notifications were subscribed to ({email} {event} {target_id}).")
        return 1
    if not event_subscribed:
        logging.warning(
            f"Attempting to remove notifications for an event for which no notifications were subscribed to ({email} {event} {target_id}).")
        return 1
    logging.info(
        f"Successfully removed notifications for {email} {event} {target_id}")
    return 2


def train_error(train_id: str, error_message: str) -> None:
    message = f"🚫 Train {train_id} just encountered the following : {error_message}"
    interested = []
    for email in EMAILS:
        for cur_entry in email:
            if cur_entry["id"] == train_id:
                interested.append(train_id)
    if not interested:
        if train_id in ERROR_TRAIN:
            ERROR_TRAIN.remove(train_id)
        ERROR_TRAIN_LAST.pop(train_id, None)
    block = render_template("simple_notification.json.jinja2",
                            message=message
                            )
    send_notification(interested, block)


def train_finished_route(train_id: str) -> None:
    message = f"✅ Train {train_id} has finished running. "
    code_avg, message_avg = query.get_train_average(train_id)
    if code_avg == 2:
        message += message_avg
    interested = []
    for email in EMAILS:
        for cur_entry in email:
            if cur_entry["id"] == train_id:
                interested.append(train_id)
    if not interested:
        if train_id in FINISHED_TRAIN:
            FINISHED_TRAIN.remove(train_id)
        FINISHED_TRAIN_LAST.pop(train_id, None)
    block = render_template("train_returned.json.jinja2",
                            message=message,
                            train_id=train_id
                            )
    send_notification(interested, block)


def train_ready_on_station(station_id: str, train_id: str) -> None:
    message = f"⏰ Train {train_id} is now ready to start running at station {station_id}."
    interested = []
    for email in EMAILS:
        for cur_entry in email:
            if cur_entry["id"] == station_id:
                interested.append(station_id)
    if not interested:
        if train_id in READY_STATION:
            READY_STATION.remove(station_id)
        READY_STATION_LAST.pop(station_id, None)
    block = render_template("simple_notification.json.jinja2",
                            message=message
                            )
    send_notification(interested, block)


def train_finished_on_station(station_id: str, train_id: str) -> None:
    message = f"✅ Train {train_id} finished running on station {station_id}."
    interested = []
    for email in EMAILS:
        for cur_entry in email:
            if cur_entry["id"] == station_id:
                interested.append(station_id)
    if not interested:
        if train_id in FINISHED_STATION:
            FINISHED_STATION.remove(station_id)
        FINISHED_STATION_LAST.pop(station_id, None)
    block = render_template("simple_notification.json.jinja2",
                            message=message
                            )
    send_notification(interested, block)


def station_error(station_id: str, error_message: str) -> None:
    message = f"🚫 On station {station_id} the following error was just encountered: {error_message}"
    interested = []
    for email in EMAILS:
        for cur_entry in email:
            if cur_entry["id"] == station_id:
                interested.append(station_id)
    if not interested:
        if station_id in ERROR_STATION:
            ERROR_STATION.remove(station_id)
        ERROR_STATION_LAST.pop(station_id, None)
    block = render_template("simple_notification.json.jinja2",
                            message=message
                            )
    send_notification(interested, block)


def send_notification(emails: List[str], block) -> None:

    for email in emails:
        payload = {"blocks": block}
        sbf_url = f"{os.environ['SBFURL']}/sendMessageToSlack/{os.environ['SLACKTOKEN']}/{email}"
        result = requests.post(sbf_url, json=payload)
        # TODO check if successfull

    return
