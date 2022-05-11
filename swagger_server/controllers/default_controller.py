"""
    Default controller module.
    Handels the requests that the server receives.
"""
# pylint: disable=E1136
# pylint: disable=W0212
# this is set for the whole file because of https://github.com/PyCQA/pylint/issues/3139
import logging
from typing import Tuple

import connexion

from flask import render_template
# from swagger_server import util
from swagger_server.models.sbf import SBF  # noqa: E501
#from swagger_server.models.sbf_res_img import SBFResImg  # noqa: E501
from . import plot, query, request_train

# for me because I sometimes forget the quotation marks
text = "text"  # pylint: disable=C0103
closeContext = "closeContext"  # pylint: disable=C0103
true = "true"  # pylint: disable=C0103

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

# def validate(check_id):
#     return check_id.isalnum()


def get_id(json_input: dict, check_id: str) -> Tuple[int, str]:
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

    # if not validate(id_value):
    #     return 1, f"Malformed {check_id}: {id_value}"
    return 2, id_value


def get_intent(json_input: dict) -> Tuple[int, str]:
    """
    Retrieves the intent
    json_input: JSON body of request.
    returns: success_code and intent or error message
    """
    if not json_input._intent:
        logging.error("No intent provided in get_intent")
        return 0, "No intent provided."
    return 2, json_input._intent


def get_user(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries for user information.
    returns: {text: retrieved_information, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        return {
            text: "Something went wrong. Not a JSON request",
            closeContext: true,
        }, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    code_id, user_id = get_id(json_input, "userID")
    if code_id != 2:
        return {
            text: f"Something went wrong processing your request: {user_id}",
            closeContext: true,
        }, 200
    _, message = query.get_user_info(user_id)
    return {text: message, closeContext: true}, 200


def get_coffee():  # noqa: E501
    """get_coffee

    Get coffee # noqa: E501


    :rtype: None
    """
    return {text: "I'm a teapot", closeContext: true}, 418


def station_information(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries for station_information information.
    returns: {text: retrieved_information, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in station_information")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    print(json_input)
    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {
            text: "Something went wrong processing your request: Not intent provided",
            closeContext: true,
        }, 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {station_id}", closeContext: true}, 200
    if intent in station_info:
        code_success, message = station_info[intent](station_id, "Station")
        if intent == "station_loc" and code_success == 2:
            message = f"🏡 Location for station {station_id}: {message}"

    elif intent == "station_info":
        message = f"Information for station {station_id}: "
        one_datapoint = False
        for func in station_info.values():
            code_success, sub_message = func(station_id, "Station")
            if code_success == 2:
                one_datapoint = True
                message += sub_message

        if not one_datapoint:
            return {text: f"No information for station {station_id} found.", closeContext: true}, 200
    else:
        logging.error("Intent not recognized in station_information")
        print(json_input)
        return {
            text: "Something went wrong processing your request: Unrecognized Intent.",
            closeContext: true,
        }, 200
    return {text: message, closeContext: true}, 200


def station_execution(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries for station exeuction information.
    returns: {text: retrieved_information, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in station_execution")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {
            text: "Something went wrong processing your request: Not intent provided",
            closeContext: true,
        }, 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {station_id}", closeContext: true}, 200
    if intent in station_exec:
        _, message = station_exec[intent](station_id, "Station")
    else:
        logging.error("Intent not recognized in station_execution")
        return {
            text: "Something went wrong processing your request: Unrecognized Intent.",
            closeContext: true,
        }, 200
    return {text: message, closeContext: true}, 200


def train_information(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries for train business information.
    returns: {text: retrieved_information, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in train_information")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {
            text: "Something went wrong processing your request: Not intent provided",
            closeContext: true,
        }, 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return {
            text: f"Something went wrong processing your request: {train_id}",
            closeContext: true,
        }, 200
    # TODO publication date
    if intent in train_info:
        _, message = train_info[intent](train_id, "Train")
    elif intent == "train_info":
        message = f"Information for train {train_id}: "
        one_datapoint = False
        for func in train_info.values():
            code_success, sub_message = func(train_id, "Train")
            if code_success == 2:
                one_datapoint = True
                message += sub_message
        if not one_datapoint:
            return {text: f"No information for train {train_id} found.", closeContext: true}, 200
    else:
        logging.error("Intent not recognized in train_information")
        return {
            text: "Something went wrong processing your request: Unrecognized Intent.",
            closeContext: true,
        }, 200
    return {text: message, closeContext: true}, 200


def train_runtime(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries for train execution/ runtime information.
    returns: {text: retrieved_information, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in train_runtimecution")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {
            text: "Something went wrong processing your request: Not intent provided",
            closeContext: true,
        }, 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return {
            text: f"Something went wrong processing your request: {train_id}",
            closeContext: true,
        }, 200
    # TODO  comp env seperate?
    if intent in train_run:
        _, message = train_run[intent](train_id)
    else:
        logging.error("Intent not recognized in train_runtimecution")
        return {
            text: "Something went wrong processing your request: Unrecognized Intent.",
            closeContext: true,
        }, 200
    return {text: message, closeContext: true}, 200


def train_request(json_input: dict) -> Tuple[dict, int]:
    """
    Handles train requests.
    returns: {text: success_message, closeContext: true}, 200
    """
    # TODO: via slack blocks
    if not connexion.request.is_json:
        return {
            text: "Something went wrong. Not a JSON request",
            closeContext: true,
        }, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    print(json_input)
    if (
        not "stations" in json_input._entities
        or not "value" in json_input._entities["stations"]
    ):
        return "Missing route.", 0
    # train_class = json_input._entities["train_class"]["value"]
    stations = json_input._entities["stations"]["value"]

    if stations == "test":
        stations = ""
    code, response = request_train.post_train(stations)
    if code == 0:
        return {
            text: "Something went wrong: Train couldn't be sent",
            closeContext: true,
        }, 200
    return {text: response, closeContext: true}, 200


def get_all(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries to retrieve all trains or stations.
    returns: {text: retrieved_information, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in get_all")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code, intent = get_intent(json_input)
    if code == 0:
        return {
            text: "Something went wrong processing your request: Not intent provided",
            closeContext: true,
        }, 200
    if intent == "all_stations":
        code, message = query.get_all("Station")
    elif intent == "all_trains":
        code, message = query.get_all("Train")
    else:
        logging.error("Intent not recognized in get_all")
        return {
            text: "Something went wrong processing your request: Unrecognized Intent.",
            closeContext: true,
        }, 200
    return {text: message, closeContext: true}, 200


def help_text(json_input: dict) -> Tuple[dict, int]:
    """Simply returns a help/ general information text.
    returns: {text: help_text, closeContext: true}, 200"""
    if not connexion.request.is_json:
        logging.error("No JSON request in help_text")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    message = """
        Hello 👋
        Here are some examples of what I can do:
        🚉 Get the trains that are currently at a station
        🧭 Tell you where a train is currently at
        🗺 Get a train's route
        📈 Get performance details for a train or station
        🧮 Tell you average performance information about a train
        💡 Retrieve information about a station or a train
        🚂 Request a train
        🛑 Get errors a train encountered
        🙅‍♀️ Ask if a train was rejected
        🗓 Tell you which trains will visit a station
        🗄 Get information about a station's dataset
        🟢 Please make sure to include station or train IDs in your message, e.g.:
            At which station is train train123 at the moment?
            Which train is currently at station station6 ? 
    """
    return render_template("test.json.jinja"), 200


def get_performance(json_input: dict) -> Tuple[dict, int]:
    """
    Handles queries for performance information and visualistations.
    Does return an error if visualistation failed.
    returns: {fileBody: base64 encoded png, fileName: png_name, fileType: "png"}, 200
    or {text: message, closeContext: true}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in get_performance")
        return {
            text: "Something went wrong processing your request: Not a JSON request",
            closeContext: true,
        }, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    code, intent = get_intent(json_input)
    if code == 0:
        return {
            text: "Something went wrong processing your request: Not intent provided",
            closeContext: true,
        }, 200
    if intent == "get_performance":
        if json_input._entities:
            if "stationID" in json_input._entities:
                code_id, station_id = get_id(json_input, "stationID")
                if code_id != 2:
                    return {
                        text: f"Something went wrong processing your request: {station_id}",
                        closeContext: true,
                    }, 200
                (
                    code_query,
                    cpu,
                    mem,
                    response_cpu,
                    response_mem,
                    message,
                ) = query.get_station_performance(station_id)
                if code_query == 2:
                    code_plot, encoded_pdf = plot.plot_station_performance(
                        station_id, cpu, mem, response_cpu, response_mem
                    )
                    if code_plot == 2:
                        return {text: encoded_pdf, closeContext: true}
                        # return {
                        #     "fileBody": str(encoded_pdf),
                        #     "fileName": "station_performance",
                        #     "fileType": "pdf"
                        # }, 200
                return {text: message, closeContext: true}, 200
            if "trainID" in json_input._entities:
                code_id, train_id = get_id(json_input, "trainID")
                if code_id != 2:
                    return {
                        text: f"Something went wrong processing your request: {train_id}",
                        closeContext: true,
                    }, 200
                if (
                    "amount" in json_input._entities
                    and json_input._entities["amount"]["value"] == "average"
                ):
                    _, message = query.get_train_average(train_id)
                    return {text: message, closeContext: true}, 200
                # if "train_memory" in json_input._entities:
                #     code_query, cpu, mem, response_cpu, response_mem, message = query.get_train_performance(
                #         train_id)
                #     if code_query == 2 and mem:
                #         code_plot, encoded_pdf = plot.plot_train_mem(
                #             train_id, response_mem)
                #         if code_plot == 2:
                #             return {
                #                 "fileBody": str(encoded_pdf),
                #                 "fileName": "train_memory",
                #                 "fileType": "pdf"
                #             }, 200
                #     return {text: message, closeContext: true}, 200
                # if "train_cpu" in json_input._entities:
                #     code_query, cpu, mem, response_cpu, response_mem, message = query.get_train_performance(
                #         train_id)
                #     if code_query == 2 and cpu:
                #         code_plot, encoded_pdf = plot.plot_train_cpu(
                #             train_id, response_cpu)
                #         if code_plot == 2:
                #             return {
                #                 "fileBody": str(encoded_pdf),
                #                 "fileName": "train_cpu",
                #                 "fileType": "pdf"
                #             }, 200
                #
                #      return {text: message, closeContext: true}, 200
                else:
                    (
                        code_query,
                        cpu,
                        mem,
                        response_cpu,
                        response_mem,
                        message,
                    ) = query.get_train_performance(train_id)
                    if code_query == 2:
                        code_plot, encoded_pdf = plot.plot_train_performance(
                            train_id, cpu, mem, response_cpu, response_mem
                        )
                        if code_plot == 2:
                            return {text: encoded_pdf, closeContext: true}
                            # return {
                            #     "fileBody": str(encoded_pdf),
                            #     "fileName": "train_performance",
                            #     "fileType": "png"
                            # }, 200

                    return {text: message, closeContext: true}, 200

        else:
            logging.error("Intent not recognized in get_performance.")
    return {text: "Something went wrong: Intent not recognized", closeContext: true}, 200


def button(json_input: dict) -> Tuple[dict, int]:
    """
        Handles button interactions
    """
    print(json_input)
    if "actions" in json_input and "action_id" in json_input["actions"][0]:
        action_id = json_input["actions"][0]["action_id"]
        channel_id = ""
        if "channel" in json_input:
            channel_id = json_input["channel"]
        if action_id == "info_about_stations":
            return {"channel_id": channel_id, "blocks": render_template("station_selection.json.jinja")}
        elif action_id == "info_about_trains":
            return {"channel_id": channel_id, "blocks": render_template("train_selection.json.jinja")}
        elif action_id == "information":
            return
        elif action_id == "all_stations":
            _, message = query.get_all("Station")
            return {"channel_id": channel_id, "blocks": render_template("simple_text.json.jinja", message=message)}
        elif action_id == "all_trains":
            _, message = query.get_all("Train")
            return {"channel_id": channel_id, "blocks": render_template("simple_text.json.jinja", message=message)}
        elif action_id == "request_train":
            return {"channel_id": channel_id, "blocks": render_template("route_selector.json.jinja")}
        elif action_id == "station_selection":
            station_id = json_input["actions"]["selected_option"]["value"]
            station_name = json_input["actions"]["selected_option"]["text"]["text"]
            return {"channel_id": channel_id, "blocks": render_template("station.json.jinja", station_id=station_id, station_name=station_name)}
        elif action_id == "train_selection":
            train_id = json_input["actions"]["selected_option"]["value"]
            train_name = json_input["actions"]["selected_option"]["text"]["text"]
            return {"channel_id": channel_id, "blocks": render_template("train.json.jinja", train_id=train_id, train_name=train_name)}
        elif action_id in station_info:
            station_id = json_input["actions"]["selected_option"]["value"]
            _, message = station_info[action_id](station_id, "Station")
            return {"channel_id": channel_id, "blocks": render_template("simple_text.json.jinja", message=message)}
        elif action_id in station_exec:
            station_id = json_input["actions"]["selected_option"]["value"]
            _, message = station_exec[action_id](station_id, "Station")
            return {"channel_id": channel_id, "blocks": render_template("simple_text.json.jinja", message=message)}
        elif action_id in train_info:
            train_id = json_input["actions"]["selected_option"]["value"]
            _, message = train_info[action_id](train_id, "Train")
            return {"channel_id": channel_id, "blocks": render_template("simple_text.json.jinja", message=message)}
        elif action_id in train_run:
            train_id = json_input["actions"]["selected_option"]["value"]
            _, message = train_run[action_id](train_id, "Train")
            return {"channel_id": channel_id, "blocks": render_template("simple_text.json.jinja", message=message)}

    return {"text": "Not found"}
