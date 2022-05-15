## pylint:disable = logging-fstring-interpolation
"""
    This module queries the blazegraph server periodically and checks for updates on certain events.
    It is also handling notifications.
"""
import threading
from typing import Callable, List
import os
import requests  # type: ignore

from . import query, blocks

ont_pref = "ex"  # pylint: disable=invalid-name

# all stations and trains
STATIONS: list = []
TRAINS: list = []
# list of encountered errors
ERROR_TRAIN_LAST: dict = {}
ERROR_STATION_LAST: dict = {}


def start_polling(interval_sec: int) -> None:
    print(
        f"Started polling. Interval: every {interval_sec} seconds.", flush=True)
    set_interval(poll_server, interval_sec)  # type: ignore
    return


def set_interval(func: Callable[[None], None], sec: int):
    def func_wrapper():
        set_interval(func, sec)
        func()
    timer = threading.Timer(sec, func_wrapper)
    timer.start()
    return timer


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


def get_id(piece: str):
    return piece.split('#')[-1]


def poll_server() -> None:
    """
        Polls the blazegraph database to check if any errors have occured.
    """
    # Initialize
    if not STATIONS and not TRAINS:
        print("Initializing...", flush=True)
        query_stations = """
            SELECT ?station WHERE {
                ?station a pht:Station .
            }
        """
        response_stations = query.blazegraph_query(query_stations)
        list_stations = get_response(response_stations, "station", False)
        for station in list_stations:
            station = get_id(station)
            STATIONS.append(station)
            ERROR_STATION_LAST[station] = []

        query_trains = """
            SELECT ?train WHERE {
                ?train a pht:Train .
            }
        """
        response_trains = query.blazegraph_query(query_trains)
        list_trains = get_response(response_trains, "train", False)
        for train in list_trains:
            train = get_id(train)
            TRAINS.append(train)
            ERROR_TRAIN_LAST[train] = []
        for train_id in TRAINS:
            query_error_train = f"""
                SELECT ?station ?error WHERE {{
                    {ont_pref}:{train_id} a pht:Train .
                    ?ev a pht:StationErrorEvent .
                    ?ev pht:station ?station .
                    ?ev pht:message ?error .
                }}
            """
            response_error_train = query.blazegraph_query(query_error_train)
            list_error_train = get_response(
                response_error_train, "station", True)
            for item in list_error_train:
                ERROR_TRAIN_LAST[train_id].append(item)

        for station_id in STATIONS:
            query_error_station = f"""
                SELECT ?error ?train WHERE {{
                    {ont_pref}:{station_id} a pht:Station .
                    ?train a pht:Train .
                    ?ev a pht:StationErrorEvent .
                    ?ev pht:station {ont_pref}:{station_id} .
                    ?ev pht:message ?error .
                }}
            """
            response_error_station = query.blazegraph_query(
                query_error_station)
            list_error_station = get_response(
                response_error_station, "train", True)
            for item in list_error_station:
                ERROR_STATION_LAST[station_id].append(item)
        print("Finished initialization.", flush=True)
        return

    # Check if we have any new stations or trains
    query_stations = """
        SELECT ?station WHERE {{
            ?station a pht:Station .
        }}
    """
    response_stations = query.blazegraph_query(query_stations)
    list_stations = get_response(response_stations, "station", False)
    for station in list_stations:
        station = get_id(station)
        if station not in STATIONS:
            STATIONS.append(station)

    query_trains = """
        SELECT ?train WHERE {
            ?train a pht:Train .
        }
    """
    response_trains = query.blazegraph_query(query_trains)
    list_trains = get_response(response_trains, "train", False)
    for train in list_trains:
        train = get_id(train)
        if train not in TRAINS:
            TRAINS.append(train)

    # Check if any stations or trains are no longer present

    STATIONS[:] = (
        station for station in STATIONS if station not in list_stations)
    TRAINS[:] = (train for train in TRAINS if train not in list_trains)

    # Check if an error occured
    for train_id in TRAINS:
        query_error_train = f"""
            SELECT ?station ?error WHERE {{
                {ont_pref}:{train_id} a pht:Train .
                {ont_pref}:{train_id} pht:event ?ev .
                ?ev a pht:StationErrorEvent .
                ?ev pht:station ?station .
                ?ev pht:message ?error .
            }}
        """
        response_error_train = query.blazegraph_query(query_error_train)
        list_error_train = get_response(response_error_train, "station", True)
        for item in list_error_train:
            if train_id not in ERROR_TRAIN_LAST:
                ERROR_TRAIN_LAST[train_id] = [item]
                train_error(train_id, item)
            elif item not in ERROR_TRAIN_LAST[train_id]:
                ERROR_TRAIN_LAST[train_id].append(item)
                train_error(train_id, item)

        for station_id in STATIONS:
            query_error_station = f"""
                SELECT ?error ?train WHERE {{
                    {ont_pref}:{station_id} a pht:Station .
                    ?train a pht:Train .
                    ?ev a pht:StationErrorEvent .
                    ?ev pht:station {ont_pref}:{station_id} .
                    ?ev pht:message ?error .
                    ?train pht:event ?ev .
                }}
            """
            response_error_station = query.blazegraph_query(
                query_error_station)
            list_error_station = get_response(
                response_error_station, "train", True)
            for item in list_error_station:
                if station_id not in ERROR_STATION_LAST:
                    ERROR_STATION_LAST[station_id] = [item]
                    station_error(station_id, item)
                elif item not in ERROR_STATION_LAST[station_id]:
                    ERROR_STATION_LAST[station_id].append(item)
                    station_error(station_id, item)


def train_error(train_id: str, error_message: str) -> None:
    message = f"🚫🚂 Train {train_id} just encountered the following error on {error_message}"
    send_notification(message)


def station_error(station_id: str, error_message: str) -> None:
    message = f"🚫🚉 Station {station_id} just encountered the following error for {error_message}"
    send_notification(message)


def send_notification(message: str) -> None:
    """
        Sends a message to the channel the webhook belongs to.
    """
    headers: dict = {}
    json_data = blocks.simple_text(message)
    print("Notifying channel ... ", flush=True)
    response = requests.post(
        os.environ['SLACK_HOOK'], headers=headers, json=json_data)
    print(response, flush=True)
