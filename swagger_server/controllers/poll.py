from . import query
from typing import Tuple


def train_finished_route(str: train_id) -> str:
    message = f"Train {train_id} has finished running. "
    code_avg, message_avg = query.get_train_average(train_id)
    if code_avg == 2:
        message += message_avg
    return message


def train_ready(station_id: str, train_id: str) -> str:
    message = f"Train {train_id} is now ready to start running at station {station_id}."
    return message


def train_finished_station(station_id: str, train_id: str) -> str:
    message = f"Train {train_id} finished running at station {station_id}."
    # TODO: performance?
    return message
