# pylint: disable=E1136
# this is set for the whole file because of https://github.com/PyCQA/pylint/issues/3139
import datetime
#import json
import logging
import time

import connexion
#import six
from SPARQLWrapper import JSON, SPARQLWrapper
from swagger_server import util
from swagger_server.models.sbf import SBF  # noqa: E501
from swagger_server.models.sbf_res import SBFRes  # noqa: E501
from swagger_server.models.sbf_res_img import SBFResImg  # noqa: E501

from . import plot


# TODO doc strings
# TODO module string
# TODO currently only returns first results if there are multiple (keywork: max)

# for me because I sometimes forget the quotation marks
text = "text"
closeContext = "closeContext"
false = "false"
# ex only used in tests
ont_pref = "ex"


def blazegraph_query(query: str) -> dict:
    prefix = """
    PREFIX pht: <http://www.personalhealthtrainmetadata.org/#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX ex: <http://www.example.org/pht_examples#>
    PREFIX mock: <http://phtmetadatamock.org#>
    """
    # Blazegraph endpoint
    url = "http://127.0.0.1:9998/bigdata/sparql"

    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(prefix + query)

    try:
        response = sparql.queryAndConvert()
        return response
    except Exception as exc:  # pylint: disable=broad-except
        print(exc)


# without optionals
def parse_response(json_response: dict) -> list:
    # malformed SPARQL query
    if not json_response:
        logging.error("Malformed SPARQL query.")
        return 0
    queried_data: list = json_response["head"]["vars"]
    queries_to_check: list = queried_data[:]
    results: list = json_response["results"]["bindings"]
    results_to_check: list = results[:]
    if len(queried_data) == 0:
        # queried data should actually never be empty
        return 0

    if len(results) == 0:
        # nothing matches the query
        logging.info("Query did not return any results.")
        return 1

    response = []

    while len(results_to_check) != 0:
        current = results_to_check.pop(0)
        while len(queries_to_check) != 0:
            element = queries_to_check.pop(0)
            element_var = current[element]
            element_res = element_var["value"]
            response.append(element_res)
        queries_to_check = queried_data[:]
    return response


def parse_ask_response(json_response: dict) -> bool:
    # json_response["boolean"] is already a bool
    return json_response["boolean"]


def validate(check_id):
    return check_id.isalnum()


def validate_request(json_input: dict, check_id: str):
    if not check_id in json_input._entities or not "value" in json_input._entities[check_id]:  # pylint: disable=W0212
        return f"No {check_id} was provided.", 0
    id_value = json_input._entities[check_id]["value"].strip(  # pylint: disable=W0212
    )
    if not validate(id_value):
        return f"Malformed {check_id}: {id_value}", 0
    return id_value, 1

# time_recv is a string in unix epoch format


def calculate_time(time_recv: str) -> None:
    try:
        time_recv = float(time_recv)
        time_now = time.time()
        elapsed = time_now - time_recv
        print(
            f"Time elapsed between receiving request and sending response in seconds: {elapsed}")
    except ValueError:
        print("Invalid time format in JSON request. This is okay.")


def get_admin_by_id(json_input):  # noqa: E501
    """get_admin_by_id

    Returns the information about the Station Admin by ID. # noqa: E501

    :param json_input: ID of Station Admin
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "adminID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    admin_id = validation[0]

    query_string = f"""
        SELECT ?name ?email WHERE{{
            ?x a pht:Station .
            ?x pht:stationOwner {ont_pref}:{0} .
            {ont_pref}:{admin_id} foaf:name ?name .
            {ont_pref}:{admin_id} foaf:mbox ?email .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No admin for ID {admin_id} found", "closeContext": "false"}, 200
    message = f"Name and email for Station Admin {admin_id}: {parsed[0]}, {parsed[1]}."
    to_return = {"text": message, "closeContext": "false"}
    if json_input._time:  # pylint: disable=W0212
        calculate_time(json_input._time)  # pylint: disable=W0212
    return to_return, 200


def get_all_stations():  # noqa: E501
    """get_all_stations

    Returns IDs of all Stations. # noqa: E501


    :rtype: SBFRes
    """

    time_recv = time.time()
    query_string = """
        SELECT ?Stations WHERE {
            ?Stations a pht:Station .
        }
    """

    response = blazegraph_query(query_string)
    parsed = parse_response(response)

    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    if parsed == 1:
        return {"text": "No stations found.", "closeContext": "false"}, 200

    message = "I found "

    # ensuring a grammatically correct message
    if len(parsed) == 1:
        message += f"one station: {parsed[0]}"
    elif len(parsed) == 2:
        message += f"two stations: {parsed[0]} and {parsed[1]}."
    else:
        message += str(len(parsed)) + " stations: "
        # ensuring a grammatically correct message: I found 3 stations: a, b, and c
        for i, item in parsed:
            message += item
            if i == len(parsed) - 1:
                message += "."
            elif i == len(parsed) - 2:
                message += ", and "
            else:
                message += ", "

    calculate_time(time_recv)
    return {"text": message, "closeContext": "false"}, 200


def get_all_trains():  # noqa: E501
    """get_all_trains

    Returns the IDs of all trains # noqa: E501


    :rtype: SBFRes
    """
    # imprecise, delta will be smaller than with the others as framwork takes time to send us things
    time_recv = time.time()

    query_string = """
        SELECT ?Trains WHERE {
            ?Trains a pht:Train .
        }
    """

    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": "No trains found.", "closeContext": "false"}, 200

    # ensuring a grammatically correct message
    message = "I found "
    if len(parsed) == 1:
        message += f"one train: {parsed[0]} ."
    elif len(parsed) == 2:
        message += f"two trains: {parsed[0]} and {parsed[1]} ."
    else:
        # ensuring a grammatically correct message: I found 3 trains: a, b, and c
        message += str(len(parsed)) + " trains: "
        for i, item in enumerate(parsed):
            message += item
            if i == len(parsed) - 1:
                message += "."
            elif i == len(parsed) - 2:
                message += ", and "
            else:
                message += ", "

    calculate_time(time_recv)
    return {"text": message, "closeContext": "false"}, 200


def get_coffee():  # noqa: E501
    """get_coffee

    Get coffee # noqa: E501


    :rtype: None
    """
    return {"text": "I'm a teapot", "closeContext": "false"}, 418


def get_comp_env_by_id(json_input):  # noqa: E501
    """get_comp_env_by_id

    Return the information about the computational environment of a
    Station by Station ID. # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                {ont_pref}:{station_id} pht:computationalEnvironment ?env .
                ?env a pht:ExecutionEnvironment .
                OPTIONAL {{?env pht:estimatedGFLOPS ?gflop .}}
                OPTIONAL {{?env pht:supportsOCI ?OCI . }}
                OPTIONAL {{?env pht:hasCUDASupport ?CUDA . }}
                OPTIONAL {{?env pht:maximumNumberOfModelsSupported ?maxModels . }}
                OPTIONAL {{?env pht:maximumModelSizeKilobytesSupported ?maxSize .}}
                OPTIONAL {{?env pht:programmingLanguageSupport ?language}}
        }}
        LIMIT 1
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text":
                f"""I didn't find any information about the computational environment
                of station {station_id}""",
                "closeContext": "false"}, 200

    body = response["results"]["bindings"][0]
    message = f"Computational environment for station {station_id}:"
    # I'm sure there's a more elegant way
    flag = False
    if "gflop" in body:
        flag = True
        message += f" GFLOPS: {body['gflop']['value']},"
    if "OCI" in body:
        flag = True
        message += f" has OCI support: {body['OCI']['value']},"
    if "CUDA" in body:
        flag = True
        message += f" has CUDA support: {body['CUDA']['value']},"
    if "maxModels" in body:
        flag = True
        message += f" maximum number of models that are spported: {body['maxModels']['value']},"
    if "maxSize" in body:
        flag = True
        message += f" maximum spported model size: {body['maxSize']['value']} KB,"
    if "language" in body:
        flag = True
        message += f" supported programming languages: {body['lanugage']['value']}."
    if not flag:
        message = f"""I didn't find any information about the computational
        environment of station {station_id}."""

    # message should end in full stop
    if message.endswith(','):
        # I'm also sure there's a more elegent way for this.
        message = message[:-1]
        message += '.'

    return {"text": message, "closeContext": "false"}, 200


def get_cur_train_station_by_id(json_input):  # noqa: E501
    """get_cur_train_station_by_id

    Return the station a train is at given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT ?station WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec a pht:TrainExecution .
            ?exec pht:event ?ev .
            ?ev a pht:StartedRunningAtStationEvent .
            ?ev pht:station ?station .
            FILTER NOT EXISTS {{
                ?exec pht:event ?fin .
                ?fin a pht:FinishedRunningAtStationEvent .
            }}
        }}
    """

    response = blazegraph_query(query_string)
    parsed = parse_response(response)

    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"The train with ID {train_id} is currently not running at any station.",
                "closeContext": "false"}, 200

    message = f"The train {train_id} is currently running at station {parsed[0]}."
    return {"text": message, "closeContext": "false"}, 200


def get_running_trains():  # noqa: E501
    """get_running_trains

    Return all running trains. # noqa: E501


    :rtype: SBFRes
    """

    query_string = """
        SELECT ?train WHERE {
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event pht:StartedRunningStationEvent .
            FILTER NOT EXISTS {
                ?exec pht:event ?ev .
                ?ev a pht:FinishedRunningStationEvent .
            }
        }
    """

    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": "There are currently no running trains.", "closeContext": "false"}, 200

    message = "I found "
    if len(parsed) == 1:
        message += f"one running train: {parsed[0]} "
    elif len(parsed) == 2:
        message += f"two running trains: {parsed[0]} and {parsed[2]} "
    else:
        message += str(len(parsed)) + " running trains: "
        for i, item in enumerate(parsed):
            message += item
            if i == len(parsed) - 1:
                message += "."
            elif i == len(parsed) - 2:
                message += ", and "
            else:
                message += ", "

    return {"text": message, "closeContext": "false"}, 200


def get_station_cert_by_id(json_input):  # noqa: E501
    """get_station_cert_by_id

    Return a station's certificate given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:certificate ?cert .
            OPTIONAL {{?cert pht:certificateBegins ?begin .}}
            OPTIONAL {{?cert pht:certificateEnd ?end .}}
            OPTIONAL {{?cert pht:certificateData ?certData .}}
            OPTIONAL {{?cert pht:certificateIssuer ?issuer .}}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text":
                f"I didn't find any information about the certificate of station {station_id}",
                "closeContext": "false"}, 200

    body = response["results"]["bindings"][0]
    message = f"Certificate information for station {station_id}:"
    # I'm sure there's a more elegant way
    flag = False
    if "begin" in body:
        flag = True
        message += f" certficate begin: {body['begin']['value']},"
    if "end" in body:
        flag = True
        message += f" certficate end: {body['end']['value']},"
    if "issuer" in body:
        flag = True
        message += f" certficate was issued by: {body['issuer']['value']},"
    if "certData" in body:
        flag = True
        message += f" certificate data: {body['certData']['value']}."
    if not flag:
        message = f"I didn't find any certificate information for station {station_id} ."
    if message.endswith(','):
        # I'm also sure there's a more elegent way for this.
        # The returned message should end with a . not with a ,
        message = message[:-1]
        message += '.'

    return {"text": message, "closeContext": "false"}, 200


def get_station_dataset_by_id(json_input):  # noqa: E501
    """get_station_dataset_by_id

    Return the dataset of a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """

    if not connexion.request.is_json:
        return {"text": "Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?setType WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:dataSet ?dataset .
            OPTIONAL {{?dataset a pht:TabularDataSet .
                        BIND("tabular" AS ?setType)}}
            OPTIONAL {{?dataset a pht:FileDataSet .
                        BIND("file" AS ?setType)}}
        }}
        LIMIT 1
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        # either no dataset is present, no station with the given ID exists,
        # or the present dataset matches neither File nor Tabular
        return {"text": f"No data set for station {station_id} found.",
                "closeContext": "false"}, 200

    result = response["results"]["bindings"][0]["setType"]["value"]
    if result == "file":
        message = f"Station {station_id} has the data set format File Data Set. "
        query_file = f"""
            SELECT ?type WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                {ont_pref}:{station_id} pht:dataSet ?dataset .
                ?dataset pht:fileType ?type .
            }}
            LIMIT 1
        """
        response_file = blazegraph_query(query_file)
        if response_file and response_file["results"]["bindings"]:
            message += f"File Type: {response_file['results']['bindings'][0]['type']['value']}. "
    elif result == "tabular":
        message = f"Station {station_id} has the data set format Tabular Data Set. "
        query_tab = f"""
            SELECT * WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                {ont_pref}:{station_id} pht:dataSet ?dataset .
                OPTIONAL {{?dataset pht:dataType ?type .}}
                OPTIONAL {{?dataset pht:key ?key .}}
                OPTIONAL {{?dataset pht:description ?description .}}
                OPTIONAL {{?dataset pht:theme ?theme .}}
            }}
            LIMIT 1
        """
        response_tab = blazegraph_query(query_tab)
        if response_tab and response_tab["results"]["bindings"]:
            result_tab = response_tab["results"]["bindings"][0]
            if "type" in result_tab:
                message += f"Data type: {result_tab['type']['value']} ."
            if "key" in result_tab:
                message += f"Access key: {result_tab['key']['value']} ."
            if "description" in result_tab:
                message += f"Description: {result_tab['description']['value']} ."
            if "theme" in result_tab:
                message += f"Theme: {result_tab['theme']['value']} ."
        else:
            message = f"Station {station_id} has an unrecognized data set format. "

    query_dataset = f"""
        SELECT * WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:dataSet ?dataset .
            OPTIONAL {{?dataset pht:theme ?theme .}}
            OPTIONAL {{?dataset pht:pid ?pid .}}
            OPTIONAL {{?dataset pht:license ?license .}}
            OPTIONAL {{?dataset pht:right ?right .}}
            OPTIONAL {{?dataset pht:accessURL ?url .}}
            OPTIONAL {{?dataset pht:dataSetCharacteristic ?char .}}
        }}
        LIMIT 1
    """
    response_dataset = blazegraph_query(query_dataset)
    if response_dataset and response_dataset["results"]["bindings"]:
        result = response_dataset["results"]["bindings"][0]
        if "theme" in result:
            message += f"Data set theme: {result['theme']['values']}"
        if "pid" in result:
            message += f"Data set identifier: {result['pid']['values']}"
        if "license" in result:
            message += f"Data set license: {result['theme']['license']}"
        if "right" in result:
            message += f"Data set right: {result['right']['values']}"
        if "url" in result:
            message += f"Data set access URL: {result['url']['values']}"
        if "char" in result:
            message += f"Data set characteristic: {result['char']['values']}"

    query_access_privacy = f"""
        SELECT * WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:dataSet ?dataset .
            OPTIONAL {{?dataset pht:accessConstrain pht:accessConstrainRequestNeeded .
                        BIND("R" as ?access)}}
            OPTIONAL {{?dataset pht:accessConstrain pht:accessConstrainUnconstrained .
                        BIND("U" as ?access)}}
            OPTIONAL {{?dataset pht:accessConstrain pht:accessConstrainNoAccess .
                        BIND("N" as ?access)}}
            OPTIONAL {{?dataset pht:usedDifferentialPrivacy ?p .
                    OPTIONAL {{?p a pht:DifferentialPrivacyKAnonymity .
                                BIND("K" as ?privacy)}}
                    OPTIONAL {{?p a pht:DifferentialPrivacyLDiversity .
                                BIND("L" as ?privacy)}}
                    OPTIONAL {{?p a pht:DifferentialPrivacyTCloseness .
                                BIND ("T" as ?privacy)}}
                    OPTIONAL {{?p a pht:DifferentialPrivacyDifferentialPrivacy .
                                BIND("O" as ?privacy)}}}}
        }}
        LIMIT 1
    """

    response_access_privacy = blazegraph_query(query_access_privacy)
    if response_access_privacy and response_access_privacy["results"]["bindings"]:
        result = response_access_privacy["results"]["bindings"][0]
        if "access" in result:
            message += "Access Constrain: "
            access_constrain = result["access"]["value"]
            message += "Request needed. " if access_constrain == "R" else ("No Access. " if access_constrain == "N" else (
                "Unconstrained. " if access_constrain == "U" else "Not Specified. "))
        if "privacy" in result:
            message += "Used Differential Privacy: "
            privacy = result["privacy"]["value"]
            message += "K Anonymity." if privacy == "K" else ("L Diversity." if privacy == "L" else (
                "T Closeness." if privacy == "T" else ("Differntial Privacy." if privacy == "O" else "Undefined.")))

    return {text: message, closeContext: false}, 200


def get_station_description_by_id(json_input):  # noqa: E501
    """get_station_description_by_id

    Return station's description given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?description WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:description ?description .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No description for station {station_id} found.",
                "closeContext": "false"}, 200
    message = f"Description for station {station_id}: {parsed[0]}"
    return {"text": message, "closeContext": "false"}, 200


def get_station_errors_by_id(json_input):  # noqa: E501
    """get_station_errors_by_id

    Return the errors a train encountered at a station given the stations ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
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

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No error logs for station {station_id} found.",
                "closeContext": "false"}, 200
    # TODO
    message = f"Error logs for station {station_id}: "
    for current in response["results"]["bindings"]:
        train = current["train"]["value"]
        error = current["error"]["value"]
        message += train + ": " + error
    return {text: message, closeContext: false}, 200


def get_station_finished_running_by_id(json_input):  # noqa: E501
    """get_station_finished_running_by_id

    Return the the finished runs on a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:FinishedRunningAtStationEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            OPTIONAL {{ ?ev pht:timestamp ?time . }}
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"There are currently no finished runs on station {station_id}",
                "closeContext": "false"}, 200
    return 'do some magic!'


def get_station_finished_transmission_by_id(json_input):  # noqa: E501
    """get_station_finished_transmission_by_id

    Return the the finished tranmissions on a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?train ?time WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:FinishedTransmissionEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            OPTIONAL {{ ?ev pht:timestamp ?time . }}
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {text: f"No trains have finished transmission at station {station_id}", closeContext: false}, 200
    time_train = []
    for current in response["results"]["bindings"]:
        if "time" in current:
            date = current["time"]["value"]
            try:
                converted_time = datetime.datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                try:
                    converted_time = datetime.datetime.strptime(
                        date, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    converted_time = datetime.datetime.fromtimestamp(
                        date.time())
        else:
            converted_time = datetime.datetime.fromtimestamp(time.time())
        train = current["train"]["value"]
        time_train.extend([[converted_time, train]])
    sorted_values = sorted(time_train, key=lambda c: c[0])
    message = f"Last finished transmission on station {station_id} by train: {sorted_values[-1][1]}"
    return {text: message, closeContext: false}, 200


def get_station_info_by_id(json_input):  # noqa: E501
    """get_station_info_by_id

    Return all info of a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
        {ont_pref}:{station_id} a pht:Station .
            OPTIONAL {{{ont_pref}:{station_id} pht:stationOwner ?owner .}}
            OPTIONAL {{{ont_pref}:{station_id} pht:responsibleForStation ?resp .}}
            OPTIONAL {{{ont_pref}:{station_id} pht:description ?desc .}}
            OPTIONAL {{{ont_pref}:{station_id} pht:title ?title .}}
            OPTIONAL {{{ont_pref}:{station_id} pht:rights ?rights .}}
            OPTIONAL {{{ont_pref}:{station_id} pht:longitude ?long .
                       {ont_pref}:{station_id} pht:latitude ?lat .}}

        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {text: f"No information for station {station_id} found.", closeContext: false}, 200
    message = f"Available information for station {station_id}: "
    result = response["results"]["bindings"][0]
    if "owner" in result:
        message += f"Station owner: {result['owner']['value']}. "
    if "resp" in result:
        message += f"Station responsible: {result['resp']['value']}. "
    if "desc" in result:
        message += f"Station description: {result['desc']['value']}. "
    if "title" in result:
        message += f"Station title: {result['title']['value']}. "
    if "long" in result and "lat" in result:
        message += f"Station location: longitude: {result['long']['value']}, latidue: {result['lat']['value']}. "

    query_string_cert = f"""
        SELECT * WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:certificate ?cert .
            OPTIONAL {{?cert pht:certificateBegins ?begin .}}
            OPTIONAL {{?cert pht:certificateEnd ?end .}}
            OPTIONAL {{?cert pht:certificateData ?certData .}}
            OPTIONAL {{?cert pht:certificateIssuer ?issuer .}}
        }}
    """

    response_cert = blazegraph_query(query_string_cert)
    if response_cert and response_cert["results"]["bindings"]:
        result_cert = response_cert["results"]["bindings"][0]
        message += "Certificate information: "
        # I'm sure there's a more elegant way
        flag = False
        if "begin" in result_cert:
            flag = True
            message += f" certficate begin: {result_cert['begin']['value']},"
        if "end" in result_cert:
            flag = True
            message += f" certficate end: {result_cert['end']['value']},"
        if "issuer" in result_cert:
            flag = True
            message += f" certficate was issued by: {result_cert['issuer']['value']},"
        if "certData" in result_cert:
            flag = True
            message += f" certificate data: {result_cert['certData']['value']}."
        if not flag:
            message += "A certificate for the station exists but there is no further information about the certificate present. "

    query_data = f"""
        SELECT ?setType WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:dataSet ?dataset .
            OPTIONAL {{?dataset a pht:TabularDataSet .
                        BIND("tabular" AS ?setType)}}
            OPTIONAL {{?dataset a pht:FileDataSet .
                        BIND("file" AS ?setType)}}
        }}
        LIMIT 1
    """

    response_data = blazegraph_query(query_data)
    if response_data and response_data["results"]["bindings"]:
        result_data = response_data["results"]["bindings"][0]["setType"]["value"]
        if result_data == "file":
            message += "The station has the data set format File Data Set. "
            query_file = f"""
                SELECT ?type WHERE {{
                    {ont_pref}:{station_id} a pht:Station .
                    {ont_pref}:{station_id} pht:dataSet ?dataset .
                    ?dataset pht:fileType ?type .
                }}
                LIMIT 1
            """
            response_file = blazegraph_query(query_file)
            if response_file and response_file["results"]["bindings"]:
                message += f"File Type: {response_file['results']['bindings'][0]['type']['value']}. "
        elif result_data == "tabular":
            message += "The station has the data set format Tabular Data Set. "
            query_tab = f"""
                SELECT * WHERE {{
                    {ont_pref}:{station_id} a pht:Station .
                    {ont_pref}:{station_id} pht:dataSet ?dataset .
                    OPTIONAL {{?dataset pht:dataType ?type .}}
                    OPTIONAL {{?dataset pht:key ?key .}}
                    OPTIONAL {{?dataset pht:description ?description .}}
                    OPTIONAL {{?dataset pht:theme ?theme .}}
                }}
                LIMIT 1
            """
            response_tab = blazegraph_query(query_tab)
            if response_tab and response_tab["results"]["bindings"]:
                result_tab = response_tab["results"]["bindings"][0]
                if "type" in result_tab:
                    message += f"Data type: {result_tab['type']['value']} ."
                if "key" in result_tab:
                    message += f"Access key: {result_tab['key']['value']} ."
                if "description" in result_tab:
                    message += f"Description: {result_tab['description']['value']} ."
                if "theme" in result_tab:
                    message += f"Theme: {result_tab['theme']['value']} ."
            else:
                message = f"Station {station_id} has an unrecognized data set format. "

        query_dataset = f"""
            SELECT * WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                {ont_pref}:{station_id} pht:dataSet ?dataset .
                OPTIONAL {{?dataset pht:theme ?theme .}}
                OPTIONAL {{?dataset pht:pid ?pid .}}
                OPTIONAL {{?dataset pht:license ?license .}}
                OPTIONAL {{?dataset pht:right ?right .}}
                OPTIONAL {{?dataset pht:accessURL ?url .}}
                OPTIONAL {{?dataset pht:dataSetCharacteristic ?char .}}
            }}
            LIMIT 1
        """
        response_dataset = blazegraph_query(query_dataset)
        if response_dataset and response_dataset["results"]["bindings"]:
            result = response_dataset["results"]["bindings"][0]
            if "theme" in result:
                message += f"Data set theme: {result['theme']['values']}"
            if "pid" in result:
                message += f"Data set identifier: {result['pid']['values']}"
            if "license" in result:
                message += f"Data set license: {result['theme']['license']}"
            if "right" in result:
                message += f"Data set right: {result['right']['values']}"
            if "url" in result:
                message += f"Data set access URL: {result['url']['values']}"
            if "char" in result:
                message += f"Data set characteristic: {result['char']['values']}"

        query_access_privacy = f"""
            SELECT * WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                {ont_pref}:{station_id} pht:dataSet ?dataset .
                OPTIONAL {{?dataset pht:accessConstrain pht:accessConstrainRequestNeeded .
                            BIND("R" as ?access)}}
                OPTIONAL {{?dataset pht:accessConstrain pht:accessConstrainUnconstrained .
                            BIND("U" as ?access)}}
                OPTIONAL {{?dataset pht:accessConstrain pht:accessConstrainNoAccess .
                            BIND("N" as ?access)}}
                OPTIONAL {{?dataset pht:usedDifferentialPrivacy ?p .
                        OPTIONAL {{?p a pht:DifferentialPrivacyKAnonymity .
                                    BIND("K" as ?privacy)}}
                        OPTIONAL {{?p a pht:DifferentialPrivacyLDiversity .
                                    BIND("L" as ?privacy)}}
                        OPTIONAL {{?p a pht:DifferentialPrivacyTCloseness .
                                    BIND ("T" as ?privacy)}}
                        OPTIONAL {{?p a pht:DifferentialPrivacyDifferentialPrivacy .
                                    BIND("O" as ?privacy)}}}}
            }}
            LIMIT 1
        """

        response_access_privacy = blazegraph_query(query_access_privacy)
        if response_access_privacy and response_access_privacy["results"]["bindings"]:
            result = response_access_privacy["results"]["bindings"][0]
            if "access" in result:
                message += "Access Constrain: "
                access_constrain = result["access"]["value"]
                message += "Request needed. " if access_constrain == "R" else ("No Access. " if access_constrain == "N" else (
                    "Unconstrained. " if access_constrain == "U" else "Not Specified. "))
            if "privacy" in result:
                message += "Used Differential Privacy: "
                privacy = result["privacy"]["value"]
                message += "K Anonymity." if privacy == "K" else ("L Diversity." if privacy == "L" else (
                    "T Closeness." if privacy == "T" else ("Differntial Privacy." if privacy == "O" else "Undefined.")))

    query_comp_env = f"""
        SELECT * WHERE {{
                {ont_pref}:{station_id} a pht:Station .
                {ont_pref}:{station_id} pht:computationalEnvironment ?env .
                ?env a pht:ExecutionEnvironment .
                OPTIONAL {{?env pht:estimatedGFLOPS ?gflop .}}
                OPTIONAL {{?env pht:supportsOCI ?OCI . }}
                OPTIONAL {{?env pht:hasCUDASupport ?CUDA . }}
                OPTIONAL {{?env pht:maximumNumberOfModelsSupported ?maxModels . }}
                OPTIONAL {{?env pht:maximumModelSizeKilobytesSupported ?maxSize .}}
                OPTIONAL {{?env pht:programmingLanguageSupport ?language}}
        }}
    """

    response_comp = blazegraph_query(query_comp_env)
    if response_comp and response_comp["results"]["bindings"]:
        result_comp = response_comp["results"]["bindings"][0]
        message += "Computational environment: "
        flag = False
        if "gflop" in result_comp:
            flag = True
            message += f"GFLOPS: {result_comp['gflop']['value']}. "
        if "OCI" in result_comp:
            flag = True
            message += f"Has OCI support: {result_comp['OCI']['value']}. "
        if "CUDA" in result_comp:
            flag = True
            message += f"Has CUDA support: {result_comp['CUDA']['value']}. "
        if "maxModels" in result_comp:
            flag = True
            message += f"Maximum number of models that are spported: {result_comp['maxModels']['value']}. "
        if "maxSize" in result_comp:
            flag = True
            message += f"Maximum spported model size: {result_comp['maxSize']['value']} KB. "
        if "language" in result_comp:
            flag = True
            message += f"Supported programming languages: {result_comp['lanugage']['value']}. "
        if not flag:
            message = message[:-len("Computational environment: ")]

    return {text: message, closeContext: false}, 200


def get_station_location_by_id(json_input):  # noqa: E501
    """get_station_location_by_id

    Return a station's location given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?long ?lat WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:longitude ?long .
            {ont_pref}:{station_id} pht:latitude ?lat .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No location for station {station_id} found.",
                "closeContext": "false"}, 200
    # TODO they needn't be in order
    message = f"Longitude: {parsed[0]}, latitude: {parsed[1]} for station {station_id}"
    return {"text": message, "closeContext": "false"}, 200


def get_station_log_by_id(json_input):  # noqa: E501
    """get_station_log_by_id

    Return the a train's logs at a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?log ?train WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StationLogEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            ?ev pht:message ?log .
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No logs for station {station_id} found.",
                "closeContext": "false"}, 200

    message = f"Logs for station {station_id}:"
    for current in response["results"]["bindings"]:
        train = current["train"]["value"]
        log = current["log"]["value"]
        message += f" {train}: {log},"
    message = message[:-1]
    message += "."
    return {text: message, closeContext: false}, 200


def get_station_owner_by_id(json_input):  # noqa: E501
    """get_station_owner_by_id

    Returns the information about the Station Owner by Station ID. # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]
    query_string = f"""
        SELECT ?owner ?name WHERE{{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:stationOwner ?owner .
            ?owner foaf:name ?name .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No owner for station {station_id} found.", "closeContext": "false"}, 200
    return {"text": f"Owner for station {station_id}: {parsed[0]} {parsed[1]}.",
            "closeContext": "false"}, 200


def get_station_performance_by_id(json_input):  # noqa: E501
    """get_station_performance_by_id

    Return the perfomances on a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string_cpu = f"""
        SELECT ?train ?usage ?time WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:CPUUsageReportEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            ?ev pht:value ?usage .
            ?ev pht:timestamp ?time .
        }}
    """
    response_cpu = blazegraph_query(query_string_cpu)

    query_string_mem = f"""
        SELECT ?train ?usage ?time WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:MemoryUsageReportEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            ?ev pht:value ?usage .
            ?ev pht:timestamp ?time .
        }}
    """
    response_mem = blazegraph_query(query_string_mem)

    if not (response_mem and response_cpu) or not (response_cpu["results"]["bindings"] and response_mem["results"]["bindings"]):
        return{text: f"No performance information for station {station_id} available.", closeContext: false}, 200
    pdf_encoded = plot.plot_station_performance(
        station_id, response_cpu, response_mem)

    if pdf_encoded == 0:
        return {
            text: "Something went wrong generating the output file.", closeContext: false}, 200

    return {
        "fileBody": str(pdf_encoded),
        "fileName": "station_performance",
        "fileType": "pdf"
    }, 200


def get_station_rejections_by_id(json_input):  # noqa: E501
    """get_station_rejections_by_id

    Return the rejections a train encountered at a station given the stations ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]
    query_string = f"""
        SELECT ?train ?reason WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StationRejectedEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            ?ev pht:message ?reason .
        }}
    """
    result = blazegraph_query(query_string)
    if not result or not result["response"]["bindings"]:
        return {text: f"No rejections for station {station_id} found", closeContext: false}, 200
    message = f"Rejections on station {station_id}:"
    for current in result["response"]["bindings"]:
        train = current["train"]["value"]
        reason = current["reason"]["value"]
        message += f" {train} with reason {reason},"
    message = message[:-1]
    message += '.'
    return {text: message, closeContext: false}, 200


def get_station_resp_by_id(json_input):  # noqa: E501
    """get_station_resp_by_id

    Return the information about the Station Responsible by station_id. # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]
    query_string = f"""
        SELECT ?resp ?name WHERE{{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:responsibleForStation ?resp .
            ?resp foaf:name ?name .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No responsible for station {station_id} found.",
                "closeContext": "false"}, 200
    return {"text": f"Responsible for station {station_id}: {parsed[0]} {parsed[1]}.",
            "closeContext": "false"}, 200


def get_station_rights_by_id(json_input):  # noqa: E501
    """get_station_rights_by_id

    Return a station's rights given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?right WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:right ?right .
        }}
        LIMIT 1
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No rights for station {station_id} found.", "closeContext": "false"}, 200
    return {text: f"Rights for station {station_id}: {parsed[0]}", closeContext: false}, 200


def get_station_started_running_by_id(json_input):  # noqa: E501
    """get_station_started_running_by_id

    Return the the started runs on a station given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StartedRunningAtStationEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            OPTIONAL {{ ?ev pht:timestamp ?time . }}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"On the station {station_id} no runs have started so far.",
                "closeContext": "false"}, 200

    time_train = []
    for current in response["results"]["bindings"]:
        if "time" in current:
            date = current["time"]["value"]
            try:
                converted_time = datetime.datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                try:
                    converted_time = datetime.datetime.strptime(
                        date, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    converted_time = datetime.datetime.fromtimestamp(
                        date.time())
        else:
            converted_time = datetime.datetime.fromtimestamp(time.time())
        train = current["train"]["value"]
        time_train.extend([[converted_time, train]])

    sorted_values = sorted(time_train, key=lambda c: c[0])
    # TODO differ between all started runs an last
    message = f"Last started run on {station_id} on train: {sorted_values[0][1]}"
    return {text: message, closeContext: false}


def get_station_title_by_id(json_input):  # noqa: E501
    """get_station_title_by_id

    Return station's title given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]
    query_string = f"""
        SELECT ?title WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:title ?title .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No title for station {station_id} found.", "closeContext": "false"}, 200
    message = f"Title for station {station_id}: {parsed[0]}"
    return {"text": message, "closeContext": "false"}, 200


def get_train_certificate_by_id(json_input):  # noqa: E501
    """get_train_certificate_by_id

    Return the train's certificates given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?cert WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:certificate ?cert .
            OPTIONAL {{?cert pht:certificateBegins ?begin .}}
            OPTIONAL {{?cert pht:certificateEnd ?end .}}
            OPTIONAL {{?cert pht:certificateData ?certData .}}
            OPTIONAL {{?cert pht:certificateIssuer ?issuer .}}
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"I didn't find any information about the certificate of train {train_id}",
                "closeContext": "false"}, 200
    body = response["results"]["bindings"][0]
    message = f"Certificate information for train {train_id}:"
    # I'm sure there's a more elegant way
    flag = False
    if "begin" in body:
        flag = True
        message += f" certficate begin: {body['begin']['value']},"
    if "end" in body:
        flag = True
        message += f" certficate end: {body['end']['value']},"
    if "issuer" in body:
        flag = True
        message += f" certficate was issued by: {body['issuer']['value']},"
    if "certData" in body:
        flag = True
        message += f" certificate data: {body['certData']['value']}."
    if not flag:
        message = f"I didn't find any certificate information for train {train_id} ."
    if message.endswith(','):
        # I'm also sure there's a more elegent way for this.
        # The returned message should end with a . not with a ,
        message = message[:-1]
        message += '.'

    return {"text": message, "closeContext": "false"}, 200


def get_train_cpu_by_id(json_input):  # noqa: E501
    """get_train_cpu_by_id

    Return the train's CPU usage given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?station ?usage ?time WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:CPUUsageReportEvent .
            ?ev pht:station ?station .
            ?ev pht:value ?usage .
            ?ev pht:timestamp ?time .
        }}
    """
    response = blazegraph_query(query_string)
    print(response)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No CPU Usage for train {train_id} found.",
                "closeContext": "false"}, 200
    pdf_encoded = plot.plot_train_cpu(train_id, response)

    if pdf_encoded == 0:
        return {
            text: "Something went wrong generating the output file.", closeContext: false}, 200

    return {
        "fileBody": str(pdf_encoded),
        "fileName": "train_cpu",
        "fileType": "pdf"
    }, 200


def get_train_creator_by_id(json_input):  # noqa: E501
    """get_train_creator_by_id

    Return the train's creator given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?creator ?name WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:creator ?creator .
            ?creator foaf:name ?name .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No creator for train {train_id} found.",
                "closeContext": "false"}, 200
    message = f"The creator for train {train_id} is the user {parsed[0]}, {parsed[1]}."
    return {"text": message, "closeContext": "false"}, 200


def get_train_data_by_id(json_input):  # noqa: E501
    """get_train_data_by_id

    Return the a train's expected data given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:model ?model .
            ?model pht:expectedDataSet ?dataset .
            OPTIONAL {{?dataset a pht:ExpectedTabularDataSet .
                        BIND("tabular" AS ?setType)}}
            OPTIONAL {{?dataset a pht:ExpectedFileDataSet .
                        BIND("file" AS ?setType)}}
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        # either no dataset is expected, no train with the given ID exists,
        # or the expected dataset matches neither File nor Tabular
        return {"text": f"No expected data set for train {train_id} found.",
                "closeContext": "false"}, 200
    # TODO maybe try here
    result = response["results"]["bindings"][0]["type"]["value"]
    if result == "file":
        query_string_file = f"""
            SELECT ?type WHERE {{
                {ont_pref}:{train_id} a pht:Train .
                {ont_pref}:{train_id} pht:model ?model .
                ?model pht:expectedDataSet ?dataset .
                OPTIONAL {{?dataset pht:fileType ?type . }}
            }}
        """
        response_file = blazegraph_query(query_string_file)
        if not response_file or not response_file["results"]["bindings"]:
            return {"text": f"Train {train_id} expects the data set format File Data Set.",
                    "closeContext": "true"}, 200
        if "type" in response["results"]["bindings"][0]:
            file_type = response["results"]["bindings"][0]["type"]["value"]
            return {"text": f"Train {train_id} expects the data set format File Data Set with the expected file type {file_type}.",
                    "closeContext": "true"}, 200

    if result == "tabular":
        # TODO
        return {"text": f"Train {train_id} expects the data set format Tabular Data Set.",
                "closeContext": "true"}, 200
        # response_tab = blazegraph_query(query_string_tab)
        # if not response_tab or not response_tab["results"]["bindings"]:
        #     return {"text": f"Train {train_id} expects the data set format Tabular Data Set.",
        #         "closeContext": "true"}, 200
        # if "type" in response["results"]["bindings"][0]:
        #     file_type = response["results"]["bindings"][0]["type"]["value"]
        #     return {"text": f"Train {train_id} expects the data set format Tabular Data Set with the expected file type {file_type}.",
        #         "closeContext": "true"}, 200


def get_train_description_by_id(json_input):  # noqa: E501
    """get_train_description_by_id

    Return the train's description given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?desc WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:description ?descr .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No description for train {train_id} found.", "closeContext": "false"}
    return {"text": f"Description for train {train_id}: {parsed[0]}",
            "closeContext": "false"}


def get_train_errors_by_id(json_input):  # noqa: E501
    """get_train_errors_by_id

    Return errors train encountered given its ID. # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT ?station ?error WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StationErrorEvent .
            ?ev pht:station ?station .
            ?ev pht:message ?error .
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No error logs for train {train_id} found.",
                "closeContext": "false"}, 200
    # TODO
    message = f"Error logs for train {train_id}: "
    for current in response["results"]["bindings"]:
        station = current["station"]["value"]
        error = current["error"]["value"]
        message += station + ": " + error
    return {text: message, closeContext: false}, 200


def get_train_finished_running_by_id(json_input):  # noqa: E501
    """get_train_finished_running_by_id

    Return the a train's last finished  given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:FinishedRunningAtStationEvent .
            ?ev pht:station ?station .
            OPTIONAL {{ ?ev pht:timestamp ?time . }}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"The train {train_id} has no so far no finished runs.",
                "closeContext": "false"}, 200
    time_station = []
    for i in range(0, len(response["results"]["bindings"])):
        current = response["results"]["bindings"][i]
        if "time" in current:
            date = current["time"]["value"]
            try:
                converted_time = datetime.datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                try:
                    converted_time = datetime.datetime.strptime(
                        date, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    converted_time = datetime.datetime.fromtimestamp(
                        date.time())
        else:
            converted_time = datetime.datetime.fromtimestamp(time.time())
        station = current["station"]["value"]
        time_station.extend([[converted_time, station]])
    sorted_values = sorted(time_station, key=lambda c: c[0])
    message = f"Last finished run for train {train_id} on station: {sorted_values[-1][1]}"
    return {text: message, closeContext: false}, 200


def get_train_finished_transmission_by_id(json_input):  # noqa: E501
    """get_train_finished_transmission_by_id

    Return the a train's finished transmissons given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:FinishedTransmissionEvent .
            ?ev pht:station ?station .
            OPTIONAL {{ ?ev pht:timestamp ?time . }}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"The train {train_id} has no so far no finished runs.",
                "closeContext": "false"}, 200
    time_station = []
    for current in response["results"]["bindings"]:
        if "time" in current:
            date = current["time"]["value"]
            try:
                converted_time = datetime.datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                try:
                    converted_time = datetime.datetime.strptime(
                        date, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    converted_time = datetime.datetime.fromtimestamp(
                        date.time())
        else:
            converted_time = datetime.datetime.fromtimestamp(time.time())
        station = current["station"]["value"]
        time_station.extend([[converted_time, station]])
    sorted_values = sorted(time_station, key=lambda c: c[0])
    message = f"Last finished transmission for train {train_id} on station: {sorted_values[-1][1]}"
    return {text: message, closeContext: false}, 200


def get_train_future_route_by_id(json_input):  # noqa: E501
    """get_train_future_route_by_id

    Return the train's planned route (stations not yet visited) including current station
    given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?station ?step WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:plannedRouteStep ?plan .
            ?plan pht:station ?station .
            ?plan pht:stepNumber ?step .
            FILTER NOT EXISTS {{
                ?exec pht:event ?ev .
                ?ev a pht:FinishedRunningAtStationEvent.
                ?ev pht:station ?station .
            }}
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No future route for train {train_id} found.",
                "closeContext": "false"}, 200
    step_station = []
    for i in range(0, len(response["results"]["bindings"])):
        current = response["results"]["bindings"][i]
        step = current["step"]["value"]
        station = current["station"]["value"]
        step_station.extend([[step, station]])

    sorted_values = sorted(step_station, key=lambda c: c[0])
    message = f"Future route for train {train_id}: "

    for station, step in sorted_values:
        message += f" {station} ({step}) ->"

    # message should end in full stop
    message = message[:-2]
    message += "."

    return {"text": message, "closeContext": "false"}, 200


def get_train_info_by_id(json_input):  # noqa: E501
    """get_train_info_by_id

    Return the train's information given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:creator ?creator .
            {ont_pref}:{train_id} pht:publisher ?pub .
            OPTIONAL {{{ont_pref}:{train_id} pht:source ?source .}}
            OPTIONAL {{{ont_pref}:{train_id} pht:description ?desription .}}
            {ont_pref}:{train_id} pht:title ?title .
            {ont_pref}:{train_id} pht:version ?version .
            {ont_pref}:{train_id} pht:published ?pubDate .
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No information for train {train_id} found.",
                "closeContext": "false"}, 200

    result = response["results"]["bindings"][0]
    message = f"Information for train {train_id}: "
    message += f"Creator: {result['creator']['value']}. "
    message += f"Publisher : {result['pub']['value']}. "
    if "source" in result:
        message += f"Source: {result['source']['value']}. "
    if "description" in result:
        message += f"Description: {result['description']['value']}. "
    message += f"Title: {result['title']['value']}. "
    message += f"Version: {result['version']['value']}. "
    message += f"Publication date: {result['pubDate']['value']}. "

    query_cert = f"""
        SELECT ?cert WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:certificate ?cert .
            OPTIONAL {{?cert pht:certificateBegins ?begin .}}
            OPTIONAL {{?cert pht:certificateEnd ?end .}}
            OPTIONAL {{?cert pht:certificateData ?certData .}}
            OPTIONAL {{?cert pht:certificateIssuer ?issuer .}}
        }}
    """
    response_cert = blazegraph_query(query_cert)
    if response_cert and response_cert["results"]["bindings"]:
        result_cert = response_cert["results"]["bindings"][0]
        message += "Certificate information: "
        # I'm sure there's a more elegant way
        flag = False
        if "begin" in result_cert:
            flag = True
            message += f"Certficate begin: {result_cert['begin']['value']}. "
        if "end" in result_cert:
            flag = True
            message += f"Certficate end: {result_cert['end']['value']},. "
        if "issuer" in result_cert:
            flag = True
            message += f"Certficate was issued by: {result_cert['issuer']['value']}. "
        if "certData" in result_cert:
            flag = True
            message += f"Certificate data: {result_cert['certData']['value']}. "
        if not flag:
            message += "A certificate is present but no further information about it is available. "

    query_model = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:model ?model .
            ?model pht:identifier ?id .
            ?model pht:creator ?creator .
            OPTIONAL {{?model pht:right ?right .}}
            OPTIONAL {{?model pht:description ?description .}}
            ?model pht:size ?size .
            OPTIONAL {{?model pht:license ?license .}}
            OPTIONAL {{?model pht:modelCharacteristic ?char .}}
            OPTIONAL {{?model pht:preProcessingAlgorithm ?preAlgo .}}
            OPTIONAL {{?model pht:algorithm ?algo .}}
            ?model pht:dataInteractionRead ?read .
            ?model pht:dataInteractionWrite ?write .
            ?model pht:dataInteractionDelete ?delete .
            OPTIONAL {{?model pht:usedAccessProtocol ?proto .}}
            OPTIONAL {{?model pht:minimumEstimatedGFLOPS ?gflops .}}
            OPTIONAL {{?model pht:needCUDASupport ?cuda .}}
        }}
    """

    response_model = blazegraph_query(query_model)
    if response_model and response_model["results"]["bindings"]:
        result_model = response_model["results"]["bindings"][0]
        message += f"Identifier: {result_model['id']['value']}. "
        message += f"Creator: {result_model['creator']['value']}. "
        if "right" in result_model:
            message += f"Rights: {result_model['right']['value']}. "
        if "description" in result_model:
            message += f"Description: {result_model['description']['value']}. "
        message += f"Model size: {result_model['size']['value']}. "
        if "license" in result_model:
            message += f"License: {result_model['license']['value']}. "
        if "char" in result_model:
            message += f"Model characteristic: {result_model['char']['value']}. "
        if "preAlgo" in result_model:
            message += f"Prepocessing algorithm: {result_model['preAlgo']['value']}. "
        if "algo" in result_model:
            message += f"Algorithm: {result_model['algo']['value']}. "
        message += f"Reads data: {result_model['read']['value']}. "
        message += f"Writes data: {result_model['write']['value']}. "
        message += f"Deletes data: {result_model['delete']['value']}. "
        if "proto" in result_model:
            message += f"Used access protocol: {result_model['proto']['value']}. "
        if "gflops" in result_model:
            message += f"Minimum GFLOPS needed: {result_model['gflops']['value']}. "
        if "cuda" in result_model:
            message += f"Needs CUDA support: {result_model['CUDA']['value']}. "

        query_data = f"""
            SELECT * WHERE {{
                {ont_pref}:{train_id} a pht:Train .
                {ont_pref}:{train_id} pht:model ?model .
                ?model pht:expectedDataSet ?dataset .
                OPTIONAL {{?dataset a pht:ExpectedTabularDataSet .
                            BIND("tabular" AS ?setType)}}
                OPTIONAL {{?dataset a pht:ExpectedFileDataSet .
                            BIND("file" AS ?setType)}}
            }}
        """
        response_data = blazegraph_query(query_data)

        if response_data and response_data["results"]["bindings"]:
            # TODO maybe try here
            result_data = response_data["results"]["bindings"][0]["type"]["value"]
            if result_data == "file":
                query_data_file = f"""
                    SELECT ?type WHERE {{
                        {ont_pref}:{train_id} a pht:Train .
                        {ont_pref}:{train_id} pht:model ?model .
                        ?model pht:expectedDataSet ?dataset .
                        OPTIONAL {{?dataset pht:fileType ?type . }}
                    }}
                """
                response_data_file = blazegraph_query(query_data_file)
                if not response_data_file or not response_data_file["results"]["bindings"]:
                    message += f"Train {train_id} expects the data set format File Data Set."
                if "type" in response_data["results"]["bindings"][0]:
                    file_type = response_data["results"]["bindings"][0]["type"]["value"]
                    message += f"Train {train_id} expects the data set format File Data Set with the expected file type {file_type}."

            if result_data == "tabular":
                # TODO
                message += f"Train {train_id} expects the data set format Tabular Data Set."
                # response_data_tab = blazegraph_query(query_data_tab)
                # if not response_data_tab or not response_data_tab["results"]["bindings"]:
                #     return {"text": f"Train {train_id} expects the data set format Tabular Data Set.",
                #         "closeContext": "true"}, 200
                # if "type" in response_data["results"]["bindings"][0]:
                #     file_type = response_data["results"]["bindings"][0]["type"]["value"]
                #     return {"text": f"Train {train_id} expects the data set format Tabular Data Set with the expected file type {file_type}.",
                #         "closeContext": "true"}, 200
    return {text: message, closeContext: false}, 200


def get_train_log_by_id(json_input):  # noqa: E501
    """get_train_log_by_id

    Return the a train's log given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?log ?station WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StationLogEvent .
            ?ev pht:station ?station .
            ?ev pht:message ?log .
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No logs for train {train_id} found.",
                "closeContext": "false"}, 200

    message = f"Logs for train {train_id}:"
    for current in response["results"]["bindings"]:
        station = current["station"]["value"]
        log = current["log"]["value"]
        message += f" {station}: {log},"
    message = message[:-1]
    message += "."
    return {text: message, closeContext: false}, 200


def get_train_memory_by_id(json_input):  # noqa: E501
    """get_train_memory_by_id

    Return the train's memory usage given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?station ?usage ?time WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:MemoryUsageReportEvent .
            ?ev pht:station ?station .
            ?ev pht:value ?usage .
            ?ev pht:timestamp ?time .
        }}
    """
    response = blazegraph_query(query_string)
    print(response)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No Memory Usage for train {train_id} found.",
                "closeContext": "false"}, 200
    pdf_encoded = plot.plot_train_mem(train_id, response)

    if pdf_encoded == 0:
        return {
            text: "Something went wrong generating the output file.", closeContext: false}, 200

    return {
        "fileBody": str(pdf_encoded),
        "fileName": "train_memory.pdf",
        "fileType": "pdf"
    }, 200


def get_train_model_by_id(json_input):  # noqa: E501
    """get_train_model_by_id

    Return the train's model given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:model ?model .
            ?model pht:identifier ?id .
            ?model pht:creator ?creator .
            OPTIONAL {{?model pht:right ?right .}}
            OPTIONAL {{?model pht:description ?description .}}
            ?model pht:size ?size .
            OPTIONAL {{?model pht:license ?license .}}
            OPTIONAL {{?model pht:modelCharacteristic ?char .}}
            OPTIONAL {{?model pht:preProcessingAlgorithm ?preAlgo .}}
            OPTIONAL {{?model pht:algorithm ?algo .}}
            ?model pht:dataInteractionRead ?read .
            ?model pht:dataInteractionWrite ?write .
            ?model pht:dataInteractionDelete ?delete .
            OPTIONAL {{?model pht:usedAccessProtocol ?proto .}}
            OPTIONAL {{?model pht:minimumEstimatedGFLOPS ?gflops .}}
            OPTIONAL {{?model pht:needCUDASupport ?cuda .}}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {text: f"No model information for train {train_id} found.", closeContext: false}, 200
    result = response["results"]["bindings"][0]
    message = f"Information for train {train_id}: "
    message += f"Identifier: {result['id']['value']}. "
    message += f"Creator: {result['creator']['value']}. "
    if "right" in result:
        message += f"Rights: {result['right']['value']}. "
    if "description" in result:
        message += f"Description: {result['description']['value']}. "
    message += f"Model size: {result['size']['value']}. "
    if "license" in result:
        message += f"License: {result['license']['value']}. "
    if "char" in result:
        message += f"Model characteristic: {result['char']['value']}. "
    if "preAlgo" in result:
        message += f"Prepocessing algorithm: {result['preAlgo']['value']}. "
    if "algo" in result:
        message += f"Algorithm: {result['algo']['value']}. "
    message += f"Reads data: {result['read']['value']}. "
    message += f"Writes data: {result['write']['value']}. "
    message += f"Deletes data: {result['delete']['value']}. "
    if "proto" in result:
        message += f"Used access protocol: {result['proto']['value']}. "
    if "gflops" in result:
        message += f"Minimum GFLOPS needed: {result['gflops']['value']}. "
    if "cuda" in result:
        message += f"Needs CUDA support: {result['CUDA']['value']}. "

    query_data = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:model ?model .
            ?model pht:expectedDataSet ?dataset .
            OPTIONAL {{?dataset a pht:ExpectedTabularDataSet .
                        BIND("tabular" AS ?setType)}}
            OPTIONAL {{?dataset a pht:ExpectedFileDataSet .
                        BIND("file" AS ?setType)}}
        }}
    """
    response_data = blazegraph_query(query_data)

    if response_data and response_data["results"]["bindings"]:
        # TODO maybe try here
        result_data = response_data["results"]["bindings"][0]["type"]["value"]
        if result_data == "file":
            query_data_file = f"""
                SELECT ?type WHERE {{
                    {ont_pref}:{train_id} a pht:Train .
                    {ont_pref}:{train_id} pht:model ?model .
                    ?model pht:expectedDataSet ?dataset .
                    OPTIONAL {{?dataset pht:fileType ?type . }}
                }}
            """
            response_data_file = blazegraph_query(query_data_file)
            if not response_data_file or not response_data_file["results"]["bindings"]:
                message += f"Train {train_id} expects the data set format File Data Set."
            if "type" in response_data["results"]["bindings"][0]:
                file_type = response_data["results"]["bindings"][0]["type"]["value"]
                message += f"Train {train_id} expects the data set format File Data Set with the expected file type {file_type}."

        if result_data == "tabular":
            # TODO
            message += f"Train {train_id} expects the data set format Tabular Data Set."
            # response_data_tab = blazegraph_query(query_data_tab)
            # if not response_data_tab or not response_data_tab["results"]["bindings"]:
            #     return {"text": f"Train {train_id} expects the data set format Tabular Data Set.",
            #         "closeContext": "true"}, 200
            # if "type" in response_data["results"]["bindings"][0]:
            #     file_type = response_data["results"]["bindings"][0]["type"]["value"]
            #     return {"text": f"Train {train_id} expects the data set format Tabular Data Set with the expected file type {file_type}.",
            #         "closeContext": "true"}, 200

    return {text: message, closeContext: false}, 200


def get_train_past_route_by_id(json_input):  # noqa: E501
    """get_train_past_route_by_id

    Return the train's past route given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?station ?step WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:plannedRouteStep ?plan .
            ?plan pht:station ?station .
            ?plan pht:stepNumber ?step .
            FILTER EXISTS {{
                ?exec pht:event ?ev .
                ?ev a pht:FinishedRunningAtStationEvent.
                ?ev pht:station ?station .
            }}
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No past route for train {train_id} found.", "closeContext": "false"}, 200

    step_station = []
    for current in response["results"]["bindings"]:
        step = current["step"]["value"]
        station = current["station"]["value"]
        step_station.extend([[step, station]])

    sorted_values = sorted(step_station, key=lambda c: c[0])
    message = f"Past route for train {train_id}: "

    for station, step in sorted_values:
        message += f" {station} ({step}) ->"

    # message should end in full stop
    message = message[:-2]
    message += "."
    return {"text": message, "closeContext": "false"}, 200


def get_train_performance_by_id(json_input):  # noqa: E501
    """get_train_performance_by_id

    Return the train's overall performance given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string_cpu = f"""
        SELECT ?station ?usage ?time WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:CPUUsageReportEvent .
            ?ev pht:station ?station .
            ?ev pht:value ?usage .
            ?ev pht:timestamp ?time .
        }}
    """
    response_cpu = blazegraph_query(query_string_cpu)
    query_string_mem = f"""
        SELECT ?station ?usage ?time WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:MemoryUsageReportEvent .
            ?ev pht:station ?station .
            ?ev pht:value ?usage .
            ?ev pht:timestamp ?time .
        }}
    """
    response_mem = blazegraph_query(query_string_mem)
    if not response_cpu or not response_cpu["results"]["bindings"]:
        if not response_mem or not response_mem["results"]["bindings"]:
            return {"text": f"No performance information for train {train_id} found.",
                    "closeContext": "false"}, 200
        else:
            pdf_encoded = plot.plot_train_mem(train_id, response_mem)
    elif not response_mem or not response_mem["results"]["bindings"]:
        pdf_encoded = plot.plot_train_cpu(train_id, response_cpu)
    else:
        pdf_encoded = plot.plot_train_performance(
            train_id, response_cpu, response_mem)

    if pdf_encoded == 0:
        return {
            text: "Something went wrong generating the output file.", closeContext: false}, 200

    return {
        "fileBody": str(pdf_encoded),
        "fileName": "train_performance",
        "fileType": "pdf"
    }, 200


def get_train_publisher_by_id(json_input):  # noqa: E501
    """get_train_publisher_by_id

    Return the train's publisher given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?pub WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:publisher ?pub .
        }}
    """
    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"I couldn't find a publisher for train {train_id}.",
                "closeContext": "false"}, 200
    return {"text": f"Publisher for train {train_id}: {parsed[0]}.",
            "closeContext": "false"}, 200


def get_train_rejections_by_id(json_input):  # noqa: E501
    """get_train_rejections_by_id

    Return the a train's rejections given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT ?station ?reason WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StationRejectedEvent .
            ?ev pht:station ?station .
            ?ev pht:message ?reason .
        }}
    """
    result = blazegraph_query(query_string)
    if not result or not result["response"]["bindings"]:
        return {text: f"No rejections for train {train_id} found", closeContext: false}, 200
    message = f"Rejections for train {train_id}:"
    for current in result["response"]["bindings"]:
        station = current["station"]["value"]
        reason = current["reason"]["value"]
        message += f" {station} with reason {reason},"
    message = message[:-1]
    message += '.'
    return {text: message, closeContext: false}, 200


def get_train_route_by_id(json_input):  # noqa: E501
    """get_train_route_by_id

    Return the train's full route given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT ?step ?station WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:plannedRouteStep ?plan .
            ?plan pht:station ?station .
            ?plan pht:stepNumber ?step .
        }}
    """
    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No route for train {train_id} found.", "closeContext": "false"}, 200

    step_station = []
    for current in response["results"]["bindings"]:
        step = current["step"]["value"]
        station = current["station"]["value"]
        step_station.extend([[step, station]])

    sorted_values = sorted(step_station, key=lambda c: c[0])

    message = f"Planned route for train {train_id}: "
    for station, step in sorted_values:
        message += f" {station} ({step}) ->"

    # message should end in full stop
    message = message[:-2]
    message += "."

    return {"text": message, "closeContext": "false"}, 200


def get_train_started_running_by_id(json_input):  # noqa: E501
    """get_train_started_running_by_id

    Return the a last started run given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StartedRunningAtStationEvent .
            ?ev pht:station ?station .
            OPTIONAL {{ ?ev pht:timestamp ?time . }}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"The train {train_id} has no so far no started runs.",
                "closeContext": "false"}, 200

    time_station = []
    for current in response["results"]["bindings"]:
        if "time" in current:
            date = current["time"]["value"]
            try:
                converted_time = datetime.datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                try:
                    converted_time = datetime.datetime.strptime(
                        date, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    converted_time = datetime.datetime.fromtimestamp(
                        date.time())
        else:
            converted_time = datetime.datetime.fromtimestamp(time.time())
        station = current["station"]["value"]
        time_station.extend([[converted_time, station]])

    sorted_values = sorted(time_station, key=lambda c: c[0])
    # TODO differ between all started runs an last
    message = f"Last started run for train {train_id} on station: {sorted_values[0][1]}"
    return {text: message, closeContext: false}


def get_train_title_by_id(json_input):  # noqa: E501
    """get_train_title_by_id

    Return the train's title given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]
    query_string = f"""
        SELECT ?title WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:title ?title .
        }}
    """

    response = blazegraph_query(query_string)
    parsed = parse_response(response)
    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    elif parsed == 1:
        return {"text": f"No title for train {train_id} found.", "closeContext": "false"}, 200

    message = f"Title for train {train_id}: {parsed[0]}."

    return {"text": message, "closeContext": "false"}, 200


def get_train_version_by_id(json_input):  # noqa: E501
    """get_train_version_by_id

    Return the train's version given its ID # noqa: E501

    :param json_input: ID of train
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "trainID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    train_id = validation[0]

    query_string = f"""
        SELECT ?ver WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:version ?ver .
        }}
    """

    response = blazegraph_query(query_string)
    parsed = parse_response(response)

    if parsed == 0:
        return {text: """An error occured on the server side while executing your request.
        Unfortunately, there is nothing you can do to fix it.""", closeContext: false}, 200
    if parsed == 1:
        return {"text": f"No version information for train {train_id} found.",
                "closeContext": "false"}, 200

    message = f"Version for train {train_id}: {parsed[0]}."

    return {"text": message, "closeContext": "false"}, 200


def get_trains_at_station_by_id(json_input):  # noqa: E501
    """get_trains_at_stations_by_id

    Return the trains at a station given the station's ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
        SELECT ?train WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event ?ev .
            ?ev a pht:StartedRunningEvent . 
            ?ev pht:station {ont_pref}:{station_id}
            FILTER NOT EXISTS {{
                ?ev a pht:FinishedRunningEvent .
                ?ev pht:station {ont_pref}:{station_id}
            }}
        }}
    """

    response = blazegraph_query(query_string)
    if not response or not response["results"]["bindings"]:
        return {"text": f"No trains at station {station_id} found.", "closeContext": "false"}, 200

    message = f"Trains at station {station_id}:"

    for current in response["results"]["bindings"]:
        train = current["train"]["value"]
        message += f" {train},"

    # Message should end in a full stop
    message = message[:-1]
    message += '.'

    return {text: message, closeContext: false}


def get_upcomming_trains_by_id(json_input):  # noqa: E501
    """get_upcomming_trains_by_id

    Return the trains that will visited a station next given its ID # noqa: E501

    :param json_input: ID of station
    :type json_input: dict | bytes

    :rtype: SBFRes
    """

    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "stationID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    station_id = validation[0]

    query_string = f"""
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

    response = blazegraph_query(query_string)

    if not response or not response["results"]["bindings"]:
        return {"text": f"No incomming trains for station {station_id} found.",
                "closeContext": "false"}, 200

    message = f"Upcoming trains for station {station_id}:"
    for current in response["results"]["bindings"]:
        train = current["train"]["value"]
        message += f" {train},"

    # message should end in a full stop
    message = message[:-1]
    message += '.'

    return {text: message, closeContext: false}


def get_user_by_id(json_input):  # noqa: E501
    """get_user_by_id

    Return name and email of a user by user ID # noqa: E501

    :param json_input: ID of user
    :type json_input: dict | bytes

    :rtype: SBFRes
    """
    if not connexion.request.is_json:
        return {"text": "Something went wrong. Not a JSON request", "closeContext": "false"}, 200

    json_input = SBF.from_dict(connexion.request.get_json())  # noqa: E501
    validation = validate_request(json_input, "userID")
    if validation[1] == 0:
        return {"text": validation[0], "closeContext": "false"}, 200
    user_id = validation[0]

    query_string = f"""
        SELECT * WHERE {{
            OPTIONAL {{ {ont_pref}:{user_id} a foaf:Agent .}}
            OPTIONAL {{ {ont_pref}:{user_id} a foaf:Person .}}
            {ont_pref}:{user_id} foaf:name ?name .
            OPTIONAL {{ {ont_pref}:{user_id} foaf:mbox ?email .}}
        }}
    """
    response = blazegraph_query(query_string)

    if not response or not response["results"]["bindings"]:
        return {"text": f"I didn't find any user information for user {user_id}", "closeContext": "false"}, 200

    body = response["results"]["bindings"][0]
    message = f"Information for user {user_id}: name: {body['name']['value']}"
    if "email" in body:
        message += f", email: {body['email']['value']}."
    else:
        message += "."

    return {"text": message, "closeContext": "false"}, 200
