"""
    Default controller module.
    Handels the requests that the server receives.
"""
# pylint: disable=E1136
# pylint: disable=W0212
# this is set for the whole file because of https://github.com/PyCQA/pylint/issues/3139
import logging
from typing import Tuple, List
import string
import json
import connexion  # type: ignore

from flask import send_from_directory
# from swagger_server import util
from swagger_server.models.sbf import SBF  # type: ignore
from swagger_server.models.sbf_res import SBFRes  # type: ignore
from swagger_server.models.sbf_res_block import SBFResBlock  # type: ignore
from swagger_server.models.action import ACTION  # type: ignore
from . import plot, query, request_train, blocks, poll

# for me because I sometimes forget the quotation marks
text = "text"  # pylint: disable=C0103
closeContext = "closeContext"  # pylint: disable=C0103
true = "true"  # pylint: disable=C0103


# easier to iterate through functions that way
# this is the reason some functions got an unused 'piece' parameter
station_info = {
    "station_owner": query.get_station_owner,
    "station_responsible": query.get_station_responsible,
    "station_cert": query.get_certificate,
    "station_title": query.get_title,
    "station_description": query.get_description,
    "station_rights": query.get_station_rights,
    "station_loc": query.get_location,
    "comp_env": query.get_comp_env,
    "station_dataset": query.get_station_dataset
}

station_exec = {
    "upcomming_trains": query.get_upcomming_trains,
    "current_at_station": query.get_current_trains,
    "station_error": query.get_station_errors,
    "station_log": query.get_station_log,
    "station_rejections": query.get_station_rejections
}

train_info = {
    "train_creator": query.get_train_creator,
    "train_publisher": query.get_train_publisher,
    "train_title": query.get_title,
    "train_version": query.get_train_version,
    "train_description": query.get_description,
    "train_cert": query.get_certificate,
    "train_model": query.get_train_model
}

train_run = {
    "planned_route": query.get_full_route,
    "future_route": query.get_future_route,
    "past_route": query.get_past_route,
    "train_error": query.get_train_errors,
    "train_log": query.get_train_log,
    "train_rejection": query.get_train_rejections,
    "current_station": query.get_current_station,
    "train_average": query.get_train_average
}


# sometimes there is no "values" attribute in a slack block payload
# so this is a look up table
stations = {
    "Station UKA": "station_aachen",
    "Station UKK": "station_cologne",
    "Station Göttingen": "station_goettingen",
    "Station Leipzig": "station_leipzig",
    "Station Leipzig IMISE": "station_leipzig_imise",
    "Station Mittweida": "station_mittweida",
    "Station Beeck": "station_beeck",
    "Station Menzel": "station_menzel"
}

stations_rev = {
    "station_aachen": "Station UKA",
    "station_cologne": "Station UKK",
    "station_goettingen": "Station Göttingen",
    "station_leipzig": "Station Leipzig",
    "station_leipzig_imise": "Station Leipzig IMISE",
    "station_mittweida": "Station Mittweida",
    "station_beeck": "Station Beeck",
    "station_menzel": "Station Menzel"
}

trains = {
    "Breast Cancer Study": "train_breast_cancer",
    "Melanoma Study": "train_melanoma",
    "Hello World Train": "train_hello_world"
}

trains_rev = {
    "train_breast_cancer": "Breast Cancer Study",
    "train_melanoma": "Melanoma Study",
    "train_hello_world": "Hello World Train"
}


def get_id(json_input: SBF, check_id: str) -> Tuple[int, str]:
    """
    Retrieves the ID value of check_id
    json_input: JSON body of request.
    check_id: train_id, station_id, or user_id
    returns: success_code and id value or error message
    """
    if (
        not check_id in json_input._entities
        or not "value" in json_input._entities[check_id]
    ):
        logging.error("No ID provided in get_id")
        logging.info(json_input)
        return 0, f"No {check_id} was provided."
    id_value = json_input._entities[check_id]["value"].strip()

    return 2, id_value


def get_intent(json_input: SBF) -> Tuple[int, str]:
    """
    Retrieves the intent
    json_input: JSON body of request.
    returns: success_code and intent or error message
    """
    if not json_input._intent:
        logging.error("No intent provided in get_intent")
        return 0, "No intent provided."
    return 2, json_input._intent


def get_selected(json_data: ACTION) -> List[str]:
    """
        Retrieves route from a json payload when the route is selected in a Slack block.
        json_data: the incomming payload
    """
    action_info = json.loads(json_data["actionInfo"])
    if "value" in action_info:
        value = action_info["value"]
        # we cant do json.loads(value) here because things in list aren't "str"
        if value.startswith("["):
            value = value[1:]
        if value.endswith("]"):
            value = value[:-1]
        if value.endswith(","):
            value = value[:-1]
        return value.split(",")
    # we could also load from message here but so far that hasn't been necessary
    return []


def get_user(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles queries for user information.
    returns: retrieved user information
    """

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    code_id, user_id = get_id(json_input, "userID")
    if code_id != 2:
        resp = SBFRes(
            text=f"Something went wrong processing your request: {user_id}", close_context=true)
        return resp, 200
    _, message = query.get_user_info(user_id)
    resp = SBFRes(text=message, close_context=true)
    return resp, 200


def get_coffee() -> Tuple[SBFRes, int]:   # noqa: E501
    """
        🫖
    """
    return SBFRes(text="I'm a teapot!", close_context=true), 418


def station_information(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles queries for station_information information.
    returns: retrieved station information
    """
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return SBFRes(
            text="Something went wrong processing your request: Not intent provided",
            close_context=true), 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return SBFRes(text=f"Something went wrong processing your request: {station_id}", close_context=true), 200
    if intent in station_info:
        code_success, message = station_info[intent](
            station_id, "Station")  # type: ignore
        if intent == "station_loc" and code_success == 2:
            message = f"🏡 Location for station {station_id}: {message}"

    elif intent == "station_info":
        message = f"Information for station {station_id}: "
        one_datapoint = False
        # Add performance info
        tmp = ""
        code_query, cpu, mem, response_cpu, response_mem, message = query.get_station_performance(
            station_id)
        if code_query == 2:
            if cpu:
                tmp += plot.describe_usage(response_cpu,
                                           "CPU Usage in %: ", False, True)
            if mem:
                tmp += plot.describe_usage(response_mem,
                                           "Memory Usage in MB: ", False, False)

        for func in station_info.values():
            code_success, sub_message = func(
                station_id, "Station")  # type: ignore
            if code_success == 2:
                one_datapoint = True
                message += sub_message
        message += tmp
        if not one_datapoint:
            return SBFRes(text=f"No information for station {station_id} found.", close_context=true), 200
    else:
        logging.error("Intent not recognized in station_information")
        return SBFRes(text="Something went wrong processing your request: Unrecognized Intent.",
                      close_context=true), 200
    return SBFRes(text=message, close_context=true), 200


def station_execution(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles queries for station exeuction information.
    returns: retrieved station exec information
    """
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return SBFRes(text="Something went wrong processing your request: Not intent provided",
                      close_context=true), 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return SBFRes(text=f"Something went wrong processing your request: {station_id}", close_context=true), 200
    if intent in station_exec:
        _, message = station_exec[intent](
            station_id, "Station")  # type: ignore
    else:
        logging.error("Intent not recognized in station_execution")
        return SBFRes(text="Something went wrong processing your request: Unrecognized Intent.",
                      close_context=true), 200
    return SBFRes(text=message, close_context=true), 200


def train_information(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles queries for train business information.
    returns: retrieved train information
    """
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return SBFRes(text="Something went wrong processing your request: Not intent provided",
                      close_context=true), 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return SBFRes(text=f"Something went wrong processing your request: {train_id}",
                      close_context=true), 200
    # TODO publication date
    if intent in train_info:
        _, message = train_info[intent](train_id, "Train")  # type: ignore
    elif intent == "train_info":
        message = f"Information for train {train_id}: "
        one_datapoint = False
        # Add performance info
        code_query, cpu, mem, response_cpu, response_mem, message = query.get_train_performance(
            train_id)
        tmp = ""
        if code_query == 2:
            if cpu:
                tmp += plot.describe_usage(response_cpu,
                                           "CPU Usage in %: ", True, True)
            if mem:
                tmp += plot.describe_usage(response_mem,
                                           "Memory Usage in MB: ", True, False)
        for func in train_info.values():
            code_success, sub_message = func(train_id, "Train")  # type: ignore
            if code_success == 2:
                one_datapoint = True
                message += sub_message

        message += tmp
        if not one_datapoint:
            return SBFRes(text=f"No information for train {train_id} found.", close_context=true), 200
    else:
        logging.error("Intent not recognized in train_information")
        return SBFRes(text="Something went wrong processing your request: Unrecognized Intent.",
                      close_context=true), 200
    return SBFRes(text=message, close_context=true), 200


def train_runtime(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles queries for train execution/ runtime information.
    returns: retrieved train runtime information
    """
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return SBFRes(text="Something went wrong processing your request: Not intent provided",
                      close_context=true), 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return SBFRes(text=f"Something went wrong processing your request: {train_id}",
                      close_context=true), 200
    # TODO  comp env seperate?
    if intent in train_run:
        _, message = train_run[intent](train_id)  # type: ignore
    else:
        logging.error("Intent not recognized in train_runtimecution")
        return SBFRes(text="Something went wrong processing your request: Unrecognized Intent.",
                      close_context=true), 200
    return SBFRes(text=message, close_context=true), 200


def train_request(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles train requests.
    returns: {text: success_message, closeContext: true}, 200
    """
    # TODO: via slack blocks

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    if (
        not "route" in json_input._entities
        or not "value" in json_input._entities["route"]
    ):
        return SBFRes("Missing route.", true), 0
    # train_class = json_input._entities["train_class"]["value"]
    route = json_input._entities["route"]["value"]

    if route == "test":
        route = ""
    code, response = request_train.post_train(route)
    if code == 0:
        return SBFRes(
            text="Something went wrong: Train couldn't be sent",
            close_context=true), 200
    return SBFRes(response, true), 200


def get_all(json_input: SBF) -> Tuple[SBFRes, int]:
    """
    Handles queries to retrieve all trains or stations.
    returns: all trains/ stations
    """
    # TODO ???
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code, intent = get_intent(json_input)
    if code == 0:
        resp = SBFRes(
            text="Something went wrong processing your request: Not intent provided", close_context=true)
        return resp, 200
    if intent == "all_stations":
        code, message = query.get_all("Station")
    elif intent == "all_trains":
        code, message = query.get_all("Train")
    else:
        logging.error("Intent not recognized in get_all")
        resp = SBFRes(
            text="Something went wrong processing your request: Unrecognized Intent.", close_context=true)
        return resp, 200
    resp = SBFRes(text=message, close_context=true)
    return resp, 200


def help_text(json_input: SBF) -> Tuple[SBFResBlock, int]:  # pylint: disable=unused-argument
    """Simply returns a help/ general information text.
    returns: Help text
    """
    message = """
        Here are some examples of what I can do:
        💡 Retrieve information about a station or a train
        🚉 Get the trains that are currently at a station
        🧭 Tell you where a train is currently at
        🗺 Get a train's route
        📈 Get performance details for a train or station
        🚂 Request a train
        🛑 Get errors a train encountered
        🙅‍♀️ Ask if a train was rejected
        🗓 Tell you which trains will visit a station
        🗄 Get information about a station's dataset
        🟢 Please make sure to include station or train IDs in your message, e.g.:
            At which station is train train123 at the moment?
            Which train is currently at station station6 ?
    """
    return SBFResBlock(blocks=blocks.help_buttons(message)), 200


def greeting(json_input: SBF) -> Tuple[SBFResBlock, int]:
    return SBFResBlock(blocks=blocks.hello_buttons(), close_context=true), 200


def get_performance(json_input: SBF, intent: str = "", piece_id="") -> Tuple[SBFRes, int]:
    """
    Handles queries for performance information and visualistations.
    Does return an error if visualistation failed.
    returns: link to the generated image or error message
    """
    if json_input:
        json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
        code, intent = get_intent(json_input)
        if code == 0:
            return SBFRes(text="Something went wrong processing your request: Not intent provided",
                          close_context=true), 200
        if intent != "get_performance":
            logging.error("Intent not recognized in get_performance.")
            return SBFRes(text="Something went wrong: Intent not recognized", close_context=true), 200

        if not json_input._entities:
            logging.error("No entities in get_performance.")
            return SBFRes(text="Something went wrong: Entities missing.", close_context=true), 200

        if "stationID" in json_input._entities:
            intent = "station_performance"
            code_id, station_id = get_id(json_input, "stationID")
            if code_id != 2:
                return SBFRes(text=f"Something went wrong processing your request: {station_id}",
                              close_context=true), 200
        elif "trainID" in json_input._entities:
            intent = "train_performance"
            code_id, train_id = get_id(json_input, "trainID")
            if code_id != 2:
                return SBFRes(text=f"Something went wrong processing your request: {train_id}",
                              close_context=true), 200
    if intent == "station_performance":
        if piece_id:
            station_id = piece_id
        (
            code_query,
            cpu,
            mem,
            response_cpu,
            response_mem,
            message,
        ) = query.get_station_performance(station_id)
        if not code_query == 2:
            return SBFRes(text=message, close_context=true), 200
        code_plot, image_link = plot.plot_station_performance(
            station_id, cpu, mem, response_cpu, response_mem
        )
        if not code_plot == 2:
            return SBFRes(text="Something went wrong: Could not generate image.", close_context=true), 200
        return SBFResBlock(blocks=blocks.image_block(url=image_link, piece_id=station_id), close_context=true), 200
    if intent == "train_performance":
        if piece_id:
            train_id = piece_id
        code_query, cpu, mem, response_cpu, response_mem, message = query.get_train_performance(
            train_id)
        if not code_query == 2:
            return SBFRes(text=message, close_context=true), 200
        if not cpu and not mem:
            return SBFRes(text=f"No performance data for train {train_id} present.", close_context=true), 200
        code_plot, image_link = plot.plot_train_performance(
            train_id, cpu, mem, response_cpu, response_mem)
        if not code_plot == 2:
            return SBFRes(text="Something went wroung: Could not generate image.", close_context=true), 200
        return SBFResBlock(blocks=blocks.image_block(url=image_link, piece_id=train_id), close_context=true), 200
    return SBFRes(text="Someting went wrong: Neither trainID nor stationID present.", close_context=true), 200


def button(json_input: ACTION) -> Tuple[SBFRes, int]:
    """
        Handles button interactions.

    """
    print(json_input, flush=True)
    if "actionInfo" in json_input:
        action_info = json.loads(json_input["actionInfo"])
        if "actionId" in action_info:
            action_id = action_info["actionId"]
        else:
            return SBFResBlock(blocks=blocks.simple_text("Something went wrong: Could not find a actionID")), 200
        if action_id == "info_about_stations":
            return SBFResBlock(blocks=blocks.station_selection()), 200
        elif action_id == "info_about_trains":
            return SBFResBlock(blocks=blocks.train_selection()), 200
        elif action_id == "information":
            return help_text(json_input)
        elif action_id == "all_stations":
            _, message = query.get_all("Station")
            return SBFResBlock(blocks=blocks.simple_text(message)), 200
        elif action_id == "all_trains":
            _, message = query.get_all("Train")
            return SBFResBlock(blocks=blocks.simple_text(message)), 200
        elif action_id == "train_request":
            return {"blocks": blocks.train_request_block()}, 200
        elif action_id == "train_route":
            route = get_selected(json_input)
            if route:
                _, message = request_train.post_train(route)
                return SBFResBlock(blocks=blocks.simple_text(message)), 200
            else:
                return SBFResBlock(blocks=blocks.simple_text("Train request failed. Could not find stations")), 200
        elif action_id == "station_selection":
            # For some reason the value part here is null
            station_name = json_input["msg"]
            station_id = stations[station_name]
            return SBFResBlock(blocks=blocks.station_block(station_name=station_name, station_id=station_id)), 200
        elif action_id == "train_selection":
            # For some reason the value part here is null
            train_name = json_input["msg"]
            train_id = trains[train_name]
            return SBFResBlock(blocks=blocks.train_block(train_id, train_name)), 200
        elif action_id == "notifications":
            piece_id = action_info["value"]
        elif action_id.startswith("update_notifications_"):
            piece_id = action_id.strip("update_notifications_")
            channel = json_input["channel"]
            poll.update_notifications(
                piece_id, get_selected(json_input), channel)
            return SBFResBlock(blocks=blocks.simple_text("✅ I updated your notification settings.")), 200
        elif action_id == "notifications_station":
            station_id = action_info["value"]
            return SBFResBlock(blocks=blocks.update_notifications_station(station_id)), 200
        elif action_id == "notifications_train":
            train_id = action_info["value"]
            return SBFResBlock(blocks=blocks.update_notifications_train(train_id)), 200
        elif action_id == "station_performance" or action_id == "train_performance":
            piece_id = action_info["value"]
            return get_performance(json_input={}, intent=action_id, piece_id=piece_id)
        elif action_id in station_info:
            station_id = action_info["value"]
            station_name = stations_rev[station_id]
            _, message = station_info[action_id](
                station_id, "Station")  # type: ignore
            return SBFResBlock(blocks=blocks.simple_text(message)), 200
        elif action_id in station_exec:
            station_id = action_info["value"]
            station_name = stations_rev[station_id]
            _, message = station_exec[action_id](
                station_id, "Station")  # type: ignore
            return SBFResBlock(blocks=blocks.simple_text(message)), 200
        elif action_id in train_info:
            train_id = action_info["value"]
            train_name = trains_rev[station_id]
            _, message = train_info[action_id](
                train_id, "Train")  # type: ignore
            return SBFResBlock(blocks=blocks.simple_text(message)), 200
        elif action_id in train_run:
            train_id = action_info["value"]
            train_name = trains_rev[train_id]
            _, message = train_run[action_id](
                train_id, "Train")  # type: ignore
            return SBFResBlock(blocks=blocks.simple_text(message)), 200
        elif action_id == "train_info":
            train_id = action_info["value"]
            message = f"Information for train {train_id}: "
            one_datapoint = False
            # Add performance info
            code_query, cpu, mem, response_cpu, response_mem, message = query.get_train_performance(
                train_id)
            tmp = ""
            if code_query == 2:
                if cpu:
                    tmp += plot.describe_usage(response_cpu,
                                               "CPU Usage in %: ", True, True)
                if mem:
                    tmp += plot.describe_usage(response_mem,
                                               "Memory Usage in MB: ", True, False)
            for func in train_info.values():
                code_success, sub_message = func(
                    train_id, "Train")  # type: ignore
                if code_success == 2:
                    one_datapoint = True
                    message += sub_message

            message += tmp
            if not one_datapoint:
                return SBFResBlock(blocks.simple_text(f"No information for train {train_id} found.")), 200
            return SBFResBlock(blocks.simple_text(message)), 200
        elif action_id == "station_info":
            station_id = action_info["value"]
            message = f"Information for station {station_id}: "
            one_datapoint = False
            # Add performance info
            tmp = ""
            code_query, cpu, mem, response_cpu, response_mem, message = query.get_station_performance(
                station_id)
            if code_query == 2:
                if cpu:
                    tmp += plot.describe_usage(response_cpu,
                                               "CPU Usage in %: ", False, True)
                if mem:
                    tmp += plot.describe_usage(response_mem,
                                               "Memory Usage in MB: ", False, False)

            for func in station_info.values():
                code_success, sub_message = func(
                    station_id, "Station")  # type: ignore
                if code_success == 2:
                    one_datapoint = True
                    message += sub_message
            message += tmp
            if not one_datapoint:
                return SBFResBlock(blocks=blocks.simple_text(f"No information for station {station_id} found.")), 200
            return SBFResBlock(blocks=blocks.simple_text(message)), 200

    print("ERRROR: Action ID not found", flush=True)
    return SBFRes(text="Something went wrong: I could not find the action_id in my list", close_context=true), 200


def get_image(image_name: str):
    """
        Returns the png file with the filename image_name.
    """
    allowed_chars = set(string.ascii_lowercase + string.digits + '_')
    if not set(image_name) <= allowed_chars:
        return 404
    filename = f"{image_name}.png"
    # uses relative file path
    return send_from_directory("./controllers/images", filename)
