# pylint: disable=E1136
# pylint: disable=W0212
# this is set for the whole file because of https://github.com/PyCQA/pylint/issues/3139
import logging
from typing import Tuple, Union

import connexion
#import six
from SPARQLWrapper import JSON, SPARQLWrapper
from swagger_server import util
from swagger_server.models.sbf import SBF  # noqa: E501
from swagger_server.models.sbf_res import SBFRes  # noqa: E501
from swagger_server.models.sbf_res_img import SBFResImg  # noqa: E501

from . import plot, query, request_train

# for me because I sometimes forget the quotation marks
text = "text"  # pylint: disable=C0103
closeContext = "closeContext"  # pylint: disable=C0103
false = "false"  # pylint: disable=C0103


def validate(check_id):
    return check_id.isalnum()


def get_id(json_input: dict, check_id: str) -> Tuple[int, str]:
    """
        Retrieves the ID value of check_id
        json_input: JSON body of request.
        check_id: train_id, station_id, or user_id
        returns: success_code and id value or error message
    """
    if not check_id in json_input._entities or not "value" in json_input._entities[check_id]:
        logging.error("No ID provided in validate_request")
        return 0, f"No {check_id} was provided."
    id_value = json_input._entities[check_id]["value"].strip(
    )

    if not validate(id_value):
        return 1, f"Malformed {check_id}: {id_value}"
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
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        return {text: "Something went wrong. Not a JSON request", closeContext: "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    code_id, user_id = get_id(json_input, "userID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {user_id}", closeContext: false}, 200
    _, message = query.get_user_info(user_id)
    return {text: message, closeContext: false}, 200


def get_coffee():  # noqa: E501
    """get_coffee

    Get coffee # noqa: E501


    :rtype: None
    """
    return {text: "I'm a teapot", closeContext: "false"}, 418


def station_business(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for station_business information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in station_business")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {station_id}", closeContext: false}, 200
    if intent == "station_responsible":
        _, message = query.get_station_role(station_id, "Responsible")
    elif intent == "station_owner":
        _, message = query.get_station_role(station_id, "Owner")
    elif intent == "station_cert":
        _, message = query.get_certificate(station_id, "Station")
    elif intent == "station_title":
        _, message = query.get_title(station_id, "Station")
    elif intent == "station_description":
        _, message = query.get_description(station_id, "Station")
    elif intent == "station_rights":
        _, message = query.get_station_rights(station_id)
    elif intent == "station_loc":
        code_loc, message_loc = query.get_location(station_id)
        if code_loc == 2:
            message = f"Location for station {station_id}: {message_loc}"
        else:
            message = message_loc
    elif intent == "station_info":
        message = f"Information for station {station_id}: "
        code_owner, message_owner = query.get_station_role(station_id, "Owner")
        if code_owner == 2:
            message += message_owner
        code_responsible, message_responsible = query.get_station_role(
            station_id, "Responsible")
        if code_responsible == 2:
            message += message_responsible
        code_description, message_description = query.get_description(
            station_id, "Station")
        if code_description == 2:
            message += message_description
        code_title, message_title = query.get_station_role(
            station_id, "Station")
        if code_title == 2:
            message += message_title
        code_rights, message_rights = query.get_station_rights(station_id)
        if code_rights == 2:
            message += message_rights
        code_location, message_location = query.get_location(station_id)
        if code_location == 2:
            message += message_location
        code_cert, message_cert = query.get_certificate(station_id, "Station")
        if code_cert == 2:
            message += message_cert
        code_dataset, message_dataset = query.get_station_dataset(station_id)
        if code_dataset == 2:
            message += message_dataset
        if code_cert != 2 and code_dataset != 2 and code_description != 2 and code_location != 2 and code_owner != 2 and code_responsible != 2 and code_rights != 2 and code_title != 2:
            return {text: f"No information for station {station_id} found.", closeContext: false}, 200
    else:
        logging.error("Intent not recognized in station_business")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def station_runtime(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for station runtime information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in station_runtime")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {station_id}", closeContext: false}, 200
    if intent == "comp_env":
        _, message = query.get_comp_env(station_id)
    else:
        logging.error("Intent not recognized in station_runtime")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def station_dataset(json_input: str) -> Tuple[dict, str]:
    """
        Handles queries for station dataset information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in station_dataset")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {station_id}", closeContext: false}, 200
    if intent == "station_dataset":
        _, message = query.get_station_dataset(station_id)
    else:
        logging.error("Intent not recognized in station_dataset")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def station_execution(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for station exeuction information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in station_execution")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, station_id = get_id(json_input, "stationID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {station_id}", closeContext: false}, 200
    elif intent == "station_upcomming":
        _, message = query.get_upcomming_trains(station_id)
    elif intent == "current_at_station":
        _, message = query.get_current_trains(station_id)
    elif intent == "station_error":
        _, message = query.get_station_errors(station_id)
    elif intent == "station_logs":
        _, message = query.get_station_log(station_id)
    elif intent == "station_rejections":
        _, message = query.get_station_rejections(station_id)
    else:
        logging.error("Intent not recognized in station_execution")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def train_business(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for train business information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in train_business")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {train_id}", closeContext: false}, 200
    # TODO publication date
    if intent == "train_title":
        _, message = query.get_title(train_id, "Train")
    elif intent == "train_version":
        _, message = query.get_train_version(train_id)
    elif intent == "train_creator":
        _, message = query.get_train_role(train_id, "creator")
    elif intent == "train_publisher":
        _, message = query.get_train_role(train_id, "publisher")
    elif intent == "train_cert":
        _, message = query.get_certificate(train_id, "Train")
    elif intent == "train_info":
        message = f"Information for train {train_id}: "
        code_creator, message_creator = query.get_train_role(
            train_id, "creator")
        if code_creator == 2:
            message += message_creator
        code_publisher, message_publisher = query.get_train_role(
            train_id, "publisher")
        if code_publisher == 2:
            message += message_publisher
        # code_source, message_source = query.
        # if code_creator == 2:
        #     message += message_source
        code_description, message_description = query.get_description(
            train_id, "Train")
        if code_description == 2:
            message += message_description
        code_title, message_title = query.get_title(train_id, "Train")
        if code_title == 2:
            message += message_title
        code_version, message_version = query.get_train_version(train_id)
        if code_version == 2:
            message += message_version
        #code_pubdate, message_pubdate
        # if code_pubdate == 2:
        #     message += message_pubdate
        code_cert, message_cert = query.get_certificate(train_id, "Train")
        if code_cert == 2:
            message += message_cert
        code_model, message_model = query.get_train_model(train_id)
        if code_model == 2:
            message += message_model
        if code_cert != 2 and code_creator != 2 and code_description != 2 and code_model != 2 and code_publisher != 2 and code_title != 2 and code_version != 2:  # and code_source != 2 and code_pubdate != 2
            return {text: f"No information for train {train_id} found.", closeContext: false}, 200
    else:
        logging.error("Intent not recognized in train_business")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def train_technical(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for technical train information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in train_technical")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {train_id}", closeContext: false}, 200
    # TODO  comp env seperate?
    if intent == "train_model":
        _, message = query.get_train_model(train_id)
    else:
        logging.error("Intent not recognized in train_technical")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def train_runtime(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for train execution/ runtime information.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in train_execution")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code_intent, intent = get_intent(json_input)
    if code_intent == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    code_id, train_id = get_id(json_input, "trainID")
    if code_id != 2:
        return {text: f"Something went wrong processing your request: {train_id}", closeContext: false}, 200
    # TODO  comp env seperate?
    elif intent == "planned_route":
        _, message = query.get_full_route(train_id)
    elif intent == "future_route":
        _, message = query.get_future_route(train_id)
    elif intent == "past_route":
        _, message = query.get_past_route(train_id)
    elif intent == "train_last_started_run":
        # TODO
        return
    elif intent == "train_error":
        _, message = query.get_train_errors(train_id)
    elif intent == "train_log":
        _, message = query.get_train_log(train_id)
    elif intent == "train_rejection":
        _, message = query.get_train_rejections(train_id)
    elif intent == "current_station":
        _, message = query.get_current_station(train_id)
    else:
        logging.error("Intent not recognized in train_execution")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def train_request(json_input: dict) -> Tuple[dict, int]:
    """
        Handles train requests.
        returns: {text: success_message, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        return {text: "Something went wrong. Not a JSON request", closeContext: "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    print(json_input)
    if not "train_class" in json_input._entities or not "value" in json_input._entities["train_class"] or not "stations" in json_input._entities or not "value" in json_input._entities["stations"]:
        return "Missing train class or route.", 0
    train_class = json_input._entities["train_class"]["value"]
    stations = json_input._entities["stations"]["value"]

    # FOR TESTING
    if train_class == "test":
        train_class = ""
    if stations == "test":
        stations = []
    # TODO station array
    code, response = request_train.post_train(train_class, stations)
    if code == 0:
        return {text: "Something went wrong: Train couldn't be sent", closeContext: false}, 200
    return {text: response, closeContext: false}, 200


def get_all(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries to retrieve all trains or stations.
        returns: {text: retrieved_information, closeContext: false}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in get_all")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code, intent = get_intent(json_input)
    if code == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    if intent == "all_stations":
        code, message = query.get_all("Station")
    elif intent == "all_trains":
        code, message = query.get_all("Train")
    else:
        logging.error("Intent not recognized in get_all")
        return {text: "Something went wrong processing your request: Unrecognized Intent.", closeContext: false}, 200
    return {text: message, closeContext: false}, 200


def get_performance(json_input: dict) -> Tuple[dict, int]:
    """
        Handles queries for performance visualistations.
        Does NOT return an error if visualistation failed.
        returns: {fileBody: base64 encoded pdf, fileName: pdf_name, fileType: "pdf"}, 200
    """
    if not connexion.request.is_json:
        logging.error("No JSON request in get_performance")
        return {text: "Something went wrong processing your request: Not a JSON request", closeContext: "false"}, 200
    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501

    code, intent = get_intent(json_input)
    if code == 0:
        return {text: "Something went wrong processing your request: Not intent provided", closeContext: false}, 200
    if intent == "station_performance":
        code_id, station_id = get_id(json_input, "stationID")
        if code_id != 2:
            return {text: f"Something went wrong processing your request: {station_id}", closeContext: false}, 200
        code_query, cpu, mem, response_cpu, response_mem, _ = query.get_station_performance(
            station_id)
        if code_query == 2:
            code_plot, encoded_pdf = plot.plot_station_performance(
                station_id, cpu, mem, response_cpu, response_mem)
            if code_plot == 2:
                return {
                    "fileBody": str(encoded_pdf),
                    "fileName": "station_performance",
                    "fileType": "pdf"
                }, 200
    if intent == "train_perfomance":
        code_id, train_id = get_id(json_input, "trainID")
        if code_id != 2:
            return {text: f"Something went wrong processing your request: {train_id}", closeContext: false}, 200
        code_query, cpu, mem, response_cpu, response_mem, _ = query.get_train_performance(
            train_id)
        if code_query == 2:
            code_plot, encoded_pdf = plot.plot_train_performance(
                train_id, cpu, mem, response_cpu, response_mem)
            if code_plot == 2:
                return {
                    "fileBody": str(encoded_pdf),
                    "fileName": "train_performance",
                    "fileType": "pdf"
                }, 200
    if intent == "train_memory":
        code_query, cpu, mem, response_cpu, response_mem, _ = query.get_train_performance(
            train_id)
        if code_query == 2 and mem:
            code_plot, encoded_pdf = plot.plot_train_mem(
                train_id, response_mem)
            if code_plot == 2:
                return {
                    "fileBody": str(encoded_pdf),
                    "fileName": "train_memory",
                    "fileType": "pdf"
                }, 200
    if intent == "train_cpu":
        code_query, cpu, mem, response_cpu, response_mem, _ = query.get_train_performance(
            train_id)
        if code_query == 2 and cpu:
            code_plot, encoded_pdf = plot.plot_train_cpu(
                train_id, response_cpu)
            if code_plot == 2:
                return {
                    "fileBody": str(encoded_pdf),
                    "fileName": "train_cpu",
                    "fileType": "pdf"
                }, 200
    else:
        logging.error("Intent not recognized in get_performance.")
