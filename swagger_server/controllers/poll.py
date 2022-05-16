## pylint:disable = logging-fstring-interpolation
"""
    This module queries the blazegraph server periodically and checks for updates on certain events.
    It is also handling notifications.
"""
import threading
from typing import Callable, List
import os
import json
import requests  # type: ignore
from requests.structures import CaseInsensitiveDict  # type: ignore

from . import query


ont_pref = "ex"  # pylint: disable=invalid-name

# all stations and trains
STATIONS: list = []
TRAINS: list = []
# all subbed trains and stations
STATIONS_SUB: list = []
TRAINS_SUB: list = []
# event subbed trains and stations with the channel
TRAIN_ERR: dict = {}
STATION_ERR: dict = {}
TRAIN_FIN: dict = {}
STATION_FIN: dict = {}
TRAIN_REJ: dict = {}
STATION_UP: dict = {}
# list of encountered errors, rejections, etc
ERR_TRAIN_LAST: dict = {}
ERR_STATION_LAST: dict = {}
FIN_TRAIN_LAST: dict = {}
FIN_STATION_LAST: dict = {}
REJ_TRAIN_LAST: dict = {}
UP_STATION_LAST: dict = {}


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


def get_response(response: dict, target: str, more_info: bool = False, info: str = None) -> List[str]:
    if not response or not response["results"]["bindings"]:
        return []
    response_list = []
    for current in response["results"]["bindings"]:
        to_add = current[target]["value"]
        if more_info:
            to_add += f": {current[info]['value']}."
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
            ERR_STATION_LAST[station] = []

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
            ERR_TRAIN_LAST[train] = []
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
                response_error_train, "station", True, 'error')
            for item in list_error_train:
                ERR_TRAIN_LAST[train_id].append(item)

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
                response_error_station, "train", True, 'error')
            for item in list_error_station:
                ERR_STATION_LAST[station_id].append(item)
        print("Finished initialization.", flush=True)
        return

    if not STATIONS_SUB and not TRAINS_SUB:
        return
    # Check if we have any new stations or trains
    query_stations = """
        SELECT ?station WHERE {
            ?station a pht:Station .
        }
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
        list_error_train = get_response(
            response_error_train, "station", True, "error")
        for item in list_error_train:
            if train_id not in ERR_TRAIN_LAST:
                ERR_TRAIN_LAST[train_id] = [item]
                notify_train_er(train_id, item)
            elif item not in ERR_TRAIN_LAST[train_id]:
                ERR_TRAIN_LAST[train_id].append(item)
                notify_train_er(train_id, item)

        query_rej_train = f"""
                SELECT ?station ?reason WHERE {{
                    {ont_pref}:{train_id} a pht:Train .
                    {ont_pref}:{train_id} pht:execution ?exec .
                    ?exec pht:event ?ev .
                    ?ev a pht:StationRejectedEvent .
                    ?ev pht:station ?station .
                    ?ev pht:message ?reason .
                }}
        """
        response_rej_train = query.blazegraph_query(query_rej_train)
        list_rej_train = get_response(
            response_rej_train, "station", True, "reason")
        for item in list_rej_train:
            if train_id not in REJ_TRAIN_LAST:
                REJ_TRAIN_LAST[train_id] = [item]
                notify_train_rej(train_id, item)
            elif item not in REJ_TRAIN_LAST[train_id]:
                REJ_TRAIN_LAST[train_id].append(item)
                notify_train_rej(train_id, item)

        query_fin_train = f"""
                SELECT ?station WHERE {{
                    {ont_pref}:{train_id} a pht:Train .
                    {ont_pref}:{train_id} pht:event ?ev .
                    ?ev a pht:FinishedRunningAtStationEvent .
                    ?ev pht:station ?station .
                }}
        """
        query_tmp_fin = f"""
                SELECT ?station WHERE {{
                        {ont_pref}:{train_id} a pht:Train .
                        ?station a pht:Train .
                        ?train pht:execution ?exec .
                        ?exec pht:plannedRouteStep ?step .
                        ?step pht:station ?station .
                        FILTER NOT EXISTS {{
                            ?exec pht:event ?ev .
                            ?ev a pht:StartedTransmissionEvent .
                            ?ev pht:station ?station .
                        }}
                        
                }}
        """
        response_tmp_fin = query.blazegraph_query(query_tmp_fin)
        list_tmp_fin = get_response(response_tmp_fin, "station", False)

        query_tmp_fin_2 = f"""
                SELECT ?station WHERE {{
                    {ont_pref}:{train_id} a pht:Train .
                    {ont_pref}:{train_id} pht:event ?ev .
                    ?ev a pht:StationRejectedEvent .
                    ?ev pht:station ?station .
                }}
        """
        response_tmp_fin_2 = query.blazegraph_query(query_tmp_fin_2)
        list_tmp_fin_2 = get_response(response_tmp_fin_2, "station", False)

        if not list_tmp_fin_2 and not list_tmp_fin:
            response_fin_train = query.blazegraph_query(query_fin_train)
            list_fin_train = get_response(response_fin_train, "station", False)
            for item in list_fin_train:
                if train_id not in REJ_TRAIN_LAST:
                    FIN_TRAIN_LAST[train_id] = [item]
                    notify_train_fin(train_id)
                elif item not in FIN_TRAIN_LAST[train_id]:
                    FIN_TRAIN_LAST[train_id].append(item)
                    notify_train_fin(train_id)

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
            response_error_station, "train", True, "error")
        for item in list_error_station:
            if station_id not in ERR_STATION_LAST:
                ERR_STATION_LAST[station_id] = [item]
                notify_station_er(station_id, item)
            elif item not in ERR_STATION_LAST[station_id]:
                ERR_STATION_LAST[station_id].append(item)
                notify_station_er(station_id, item)

        query_up_station = f"""
                SELECT ?train WHERE {{
                        {ont_pref}:{station_id} a pht:Station .
                        ?train a pht:Train .
                        ?train pht:execution ?exec .
                        ?exec pht:plannedRouteStep ?step .
                        ?step pht:station {ont_pref}:{station_id} .
                        FILTER NOT EXISTS {{
                            ?exec pht:event ?ev .
                            ?ev a pht:StartedTransmissionEvent .
                            ?ev pht:station {ont_pref}:{station_id} .
                        }}
                        
                }}
        """
        response_up_station = query.blazegraph_query(query_up_station)
        list_up_station = get_response(response_up_station, "train", False)
        for item in list_up_station:
            if station_id not in UP_STATION_LAST:
                UP_STATION_LAST[station_id] = [item]
                notify_station_up(station_id, item)
            elif item not in UP_STATION_LAST[station_id]:
                UP_STATION_LAST[station_id].append(item)
                notify_station_fin(station_id, item)

        query_fin_station = f"""
                SELECT ?train WHERE {{
                    {ont_pref}:{station_id} a pht:Station .
                    ?train pht:event ?ev .
                    ?ev a pht:FinishedRunningAtStationEvent .
                    ?ev pht:station {ont_pref}:{station_id} .
                }}
        """
        response_fin_station = query.blazegraph_query(query_fin_station)
        list_fin_station = get_response(response_fin_station, "train", False)
        for item in list_fin_station:
            if station_id not in FIN_STATION_LAST:
                FIN_STATION_LAST[station_id] = [item]
                notify_station_fin(station_id, item)
            elif item not in FIN_STATION_LAST[station_id]:
                FIN_STATION_LAST[station_id].append(item)
                notify_station_fin(station_id, item)


def notify_train_er(train_id: str, message: str) -> None:
    if train_id in TRAIN_ERR:
        for channel in TRAIN_ERR[train_id]:
            message = f"🚫🚂 Train {train_id} just encountered the following error on {message}"
            send_notification(message, channel)


def notify_station_er(station_id: str, message: str) -> None:
    if station_id in STATION_ERR:
        for channel in STATION_ERR[station_id]:
            message = f"🚫🚉 Station {station_id} just encountered the following error for {message}"
            send_notification(message, channel)


def notify_train_rej(train_id: str, station: str) -> None:
    if train_id in TRAIN_REJ:
        for channel in TRAIN_REJ[train_id]:
            message = f"⛔️🚂 Train {train_id} just got rejected by {station}"
            send_notification(message, channel)


def notify_train_fin(train_id: str) -> None:
    if train_id in TRAIN_FIN:
        for channel in TRAIN_FIN[train_id]:
            message = f"🏁🚂 Train {train_id} just finished its route!"
            send_notification(message, channel)


def notify_station_fin(station_id: str, train_id: str) -> None:
    if station_id in STATION_FIN:
        for channel in STATION_FIN[station_id]:
            message = f"🏁🚉 Train {train_id} just finished running on station {station_id}!"
            send_notification(message, channel)


def notify_station_up(station_id: str, train_id: str) -> None:
    if station_id in STATION_UP:
        for channel in STATION_UP[station_id]:
            message = f" 🚉Train {train_id} will visit {station_id} soon!"
            send_notification(message, channel)


def send_notification(message: str, channel: str) -> None:
    """
        Sends a message to the channel the webhook belongs to.
    """
    url = "https://slack.com/api/chat.postMessage"

    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {os.environ['TOKEN']}"
    headers["Content-Type"] = "application/json"

    data = {
        'channel': channel,
        'text': message
    }

    data_json = json.dumps(data)

    response = requests.post(url, headers=headers, data=data_json)

    print(response, flush=True)


def update_notifications(piece_id: str, events: List[str], channel: str) -> None:
    """
        Updates notification settings for a channel.
    """
    for event in events:
        if event == "station_errors":
            if channel not in STATION_ERR:
                STATION_ERR[channel] = [piece_id]
            elif piece_id not in STATION_ERR[channel]:
                STATION_ERR[channel].append(piece_id)
            if piece_id not in STATIONS_SUB:
                STATIONS_SUB.append(piece_id)
        elif event == "station_upcomming":
            if channel not in STATION_UP:
                STATION_UP[channel] = [piece_id]
            elif piece_id not in STATION_UP[channel]:
                STATION_UP[channel].append(piece_id)
            if piece_id not in STATIONS_SUB:
                STATIONS_SUB.append(piece_id)
        elif event == "station_finished":
            if channel not in STATION_FIN:
                STATION_FIN[channel] = [piece_id]
            elif piece_id not in STATION_FIN[channel]:
                STATION_FIN[channel].append(piece_id)
            if piece_id not in STATIONS_SUB:
                STATIONS_SUB.append(piece_id)
        elif event == "train_finished":
            if channel not in TRAIN_FIN:
                TRAIN_FIN[channel] = [piece_id]
            elif piece_id not in TRAIN_FIN[channel]:
                TRAIN_FIN[channel].append(piece_id)
            if piece_id not in TRAINS_SUB:
                TRAINS_SUB.append(piece_id)
        elif event == "train_errors":
            if channel not in TRAIN_ERR:
                TRAIN_ERR[channel] = [piece_id]
            elif piece_id not in TRAIN_ERR[channel]:
                TRAIN_ERR[channel].append(piece_id)
            if piece_id not in TRAINS_SUB:
                TRAINS_SUB.append(piece_id)
        elif event == "train_rejections":
            if channel not in TRAIN_FIN:
                TRAIN_REJ[channel] = [piece_id]
            elif piece_id not in TRAIN_REJ[channel]:
                TRAIN_REJ[channel].append(piece_id)
            if piece_id not in TRAINS_SUB:
                TRAINS_SUB.append(piece_id)

    return
