"""
    Module to retrieve information from the blazegraph server.
    Parses response into natural language messages.
"""
# pylint: disable=E1136  # pylint/issues/3139
# pylint: disable=unused-argument

import datetime
import logging
import time
import os
from typing import Tuple
from SPARQLWrapper import JSON, SPARQLWrapper  # type: ignore

# ex only used in tests
ont_pref = "ex"  # pylint: disable=C0103


def blazegraph_query(query_str: str) -> dict:
    """
        Queries the blazegraph server.
        query_str: the query. prefix is added
        returns: response or None if query failed
    """
    prefix = """
        PREFIX pht: <http://www.personalhealthtrainmetadata.org/#> 
        PREFIX mock: <http://phtmetadatamock.org#>  
        PREFIX dmop: <http://www.e-lico.eu/ontologies/dmo/DMOP/DMKB.owl> 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        PREFIX ex: <http://www.example.org/pht_examples#> 
    """
    url = os.environ["BLAZEGRAPHURL"]

    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(prefix + query_str)

    try:
        response = sparql.queryAndConvert()
        return response
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Query failed in query blazegraph_query")
        print(exc, flush=True)
        return {}


def get_user_info(user_id: str) -> Tuple[int, str]:
    """
        Queries blazegraph server for a users name(s) and email(s)
        user_id: user ID string
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT * WHERE {{
            OPTIONAL {{ {ont_pref}:{user_id} a foaf:Agent .}}
            OPTIONAL {{ {ont_pref}:{user_id} a foaf:Person .}}
            {ont_pref}:{user_id} foaf:name ?name .
            OPTIONAL {{ {ont_pref}:{user_id} foaf:mbox ?email .}}
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_user_info")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No user information for {user_id} found."
    message = f"Information for {user_id}: "
    tmp_name = ""
    tmp_email = ""
    for item in response["results"]["bindings"]:
        name = item["name"]["value"]
        if not name == tmp_name:
            tmp_name = name
            message += f"Name: {name} "
            if "email" in item:
                email = item["email"]["value"]
                tmp_email = email
                message += f"Email: {email} "
        elif "email" in item:
            email = item["email"]["value"]
            if not email == tmp_email:
                tmp_email = email
                message += f" {email} "
    message += "."
    return 2, message


def get_title(target_id: str, piece: str) -> Tuple[int, str]:
    """
        Queries blazegraph server for title(s)
        If piece = "Train" only one title will be return by schema definition.
        target_id: station or train ID
        piece: Station or Train
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?title WHERE {{
            {ont_pref}:{target_id} a pht:{piece} .
            {ont_pref}:{target_id} pht:title ?title .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_title")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No title for {target_id} found."
    if piece == "Train":
        return 2, f"🪧 Title: {response['results']['bindings'][0]['title']['value']}"
    message = "🪧 Title: "
    for item in response["results"]["bindings"]:
        message += f" {item['title']['value']} "
    message += "."
    return 2, message


def get_description(target_id: str, piece: str) -> Tuple[int, str]:
    """
        Queries blazegraph server for descriptions(s)
        target_id: station or train ID
        piece: Station or Train
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?description WHERE {{
            {ont_pref}:{target_id} a pht:{piece} .
            {ont_pref}:{target_id} pht:description ?description .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_description")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No description for {target_id} found."
    message = "Description: "
    for item in response["results"]["bindings"]:
        message += f" {item['description']['value']} "
    message += "."
    return 2, message


def get_location(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a station's location
        station_id: station ID string
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?long ?lat WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:longitude ?long .
            {ont_pref}:{station_id} pht:latitude ?lat .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_location")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No location for {station_id} found."
    message = f"Longitude: {response['results']['bindings'][0]['long']['value']}, latitude: {response['results']['bindings'][0]['lat']['value']}"  # pylint: disable=line-too-long
    return 2, message


def get_comp_env(station_id: str,  piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a station's computational environment
        station_id: station ID string
        returns: success_code, information as string or error_message
    """
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
    """

    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_comp_env")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"""No information about the computational environment of station {station_id} found"""

    body = response["results"]["bindings"][0]
    message = f"🖥️ Computational environment for station {station_id}:"
    flag = False
    if "gflop" in body:
        flag = True
        message += f" GFLOPS: {body['gflop']['value']}."
    if "OCI" in body:
        flag = True
        message += f" Has OCI support: {body['OCI']['value']}."
    if "CUDA" in body:
        flag = True
        message += f" Has CUDA support: {body['CUDA']['value']}."
    if "maxModels" in body:
        flag = True
        message += f" Maximum number of models that are supported: {body['maxModels']['value']}."
    if "maxSize" in body:
        flag = True
        message += f" Maximum supported model size: {body['maxSize']['value']} KB."
    if "language" in body:
        # no maxCount, station can support multiple languages
        flag = True
        message += " Supported programming languages:"
        for item in response["results"]["bindings"]:
            message += f" {item['language']['value']} "
    if not flag:
        return 1, f"""No information about the computational environment of station {station_id} found."""

    return 2, message


def get_all(piece: str) -> Tuple[int, str]:
    """
        Queries blazegraph server for all trains or stations
        piece: Train or Station
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?{piece} WHERE {{
            ?{piece} a pht:{piece} .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_all")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No {piece}s found"
    body = response["results"]["bindings"]
    print(body)
    if len(body) == 1:
        return 2, f"I found one {piece}: {body[0][{piece}]['value']}."
    if len(body) == 2:
        return 2, f"I found two {piece}s: {body[0][{piece}]['value']} and {body[1][{piece}]['value']}."
    else:
        message = f"I found {(len(body))} {piece}s: "
        # ensuring a grammatically correct message: I found 3 x: a, b, and c
        for i, item in enumerate(body):
            message += item[f"{piece}"]["value"]
            if i == len(body) - 1:
                message += "."
            elif i == len(body) - 2:
                message += ", and "
            else:
                message += ", "
    return 2, message


def get_station_owner(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a station owner
        station_id: station ID string
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?owner ?name WHERE{{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:stationOwner ?owner .
            ?owner foaf:name ?name .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_station_owner")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No owner for station {station_id} found."

    message = f"👷 Owner for station {station_id}: "
    for i, item in enumerate(response["results"]["bindings"]):
        owner = item["owner"]["value"]
        name = item["name"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {name} ({owner})."
        else:
            message += f" {name} ({owner}),"
    return 2, message


def get_station_responsible(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a station responsible
        station_id: station ID string
        responsible: Owner or Responsible
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?responsible ?name WHERE{{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:stationResponsible ?responsible .
            ?responsible foaf:name ?name .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_station_responsible")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No responsible for station {station_id} found."

    message = f"👷 Responsible for station {station_id}: "
    for i, item in enumerate(response["results"]["bindings"]):
        responsible = item["responsible"]["value"]
        name = item["name"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {name} ({responsible})."
        else:
            message += f" {name} ({responsible}),"
    return 2, message


def get_train_creator(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's creator
        train_id: train ID string
        creator: publisher or creator
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?creator ?name WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:creator ?creator .
            ?creator foaf:name ?name . 
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_train_creator")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No creator for train {train_id} found."
    message = f"Creator for train {train_id}: "
    for i, item in enumerate(response["results"]["bindings"]):
        creator = item["creator"]["value"]
        name = item["name"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {name} ({creator})."
        else:
            message += f" {name} ({creator}),"
    return 2, message


def get_train_publisher(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's publisher
        train_id: train ID string
        publisher: publisher or creator
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?publisher ?name WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:publisher ?publisher .
            ?publisher foaf:name ?name . 
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_train_publisher")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No publisher for train {train_id} found."
    # max one publisher
    return 2, f"👷 Publisher for train {train_id}: {response['results']['bindings'][0]['name']['value']} ({response['results']['bindings'][0]['publisher']['value']})"  # pylint: disable=line-too-long


def get_certificate(target_id: str, piece: str) -> Tuple[int, str]:
    """
        Queries blazegraph server for a certificate
        target_id: station or train ID
        piece: Station or Train
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT * WHERE {{
            {ont_pref}:{target_id} a pht:{piece} .
            {ont_pref}:{target_id} pht:certificate ?cert .
            OPTIONAL {{?cert pht:certificateBegins ?begin .}}
            OPTIONAL {{?cert pht:certificateEnd ?end .}}
            OPTIONAL {{?cert pht:certificateData ?certData .}}
            OPTIONAL {{?cert pht:certificateIssuer ?issuer .}}
        }}
    """

    response = blazegraph_query(query_string)
    if not response:
        logging.error("Query failed in module query function get_certificate")
        return 0, "Something went wrong querying the server."
    if response["results"]["bindings"]:
        return 1, "No certificate found."

    message = "📜 Certificate: "

    flag = False
    for item in response["results"]["bindings"]:
        if "begin" in item:
            flag = True
            message += f" Certficate begin: {item['begin']['value']}."
        if "end" in item:
            flag = True
            message += f" Certficate end: {item['end']['value']}."
        if "issuer" in item:
            flag = True
            message += f" Certficate was issued by: {item['issuer']['value']}."
        if "certData" in item:
            flag = True
            message += f" Certificate data: {item['certData']['value']}."
    if not flag:
        return 1, f"No certificate information for {piece} {target_id} found."

    return 2, message


def get_running_trains() -> Tuple[int, str]:
    """
        Queries blazegraph server for all running trains
        returns: success_code, information as string or error_message
    """
    query_string = """
        SELECT ?train WHERE {
            ?train a pht:Train .
            ?train pht:execution ?exec .
            ?exec pht:event pht:StartedRunningAtStationEvent .
            FILTER NOT EXISTS {
                ?exec pht:event ?ev .
                ?ev a pht:FinishedRunningAtStationEvent .
            }
        }
    """

    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_running_trains")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, "No running trains found."

    trains = response["results"]["bindings"]
    if len(trains) == 1:
        message = f"I found one running train: {trains[0]['train']['value']} "
        return 2, message
    if len(trains) == 2:
        message = f"I found two running trains: {trains[0]['train']['value']} and {trains[1]['train']['value']} "
        return 2, message
    message += f"I found {len(trains)} running trains: "
    for i, item in enumerate(trains):
        message += f"{item['train']['value']}"
        if i == len(trains) - 1:
            message += "."
        elif i == len(trains) - 2:
            message += ", and "
        else:
            message += ", "

    return 2, message


def get_current_station(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for at what station a train is currently at
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?station WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
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
    if not response:
        logging.error(
            "Query failed in module query function get_current_station")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"The train with ID {train_id} is currently not running at any station."

    message = f"🚉 The train {train_id} is currently running at station {response['results']['bindings'][0]['station']['value']}."  # pylint: disable=line-too-long
    return 2, message


def get_current_trains(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for which train is currently at a station
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_current_trains")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No trains at station {station_id} found."

    message = f"🚆 Trains at station {station_id}:"

    for i, current in enumerate(response["results"]["bindings"]):
        train = current["train"]["value"]
        # Message should end in a full stop
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {train}."
        else:
            message += f" {train},"
    return 2, message


def get_station_errors(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for which errors occured at a station
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?error ?train WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            ?train a pht:Train .
            ?train pht:event ?ev .
            ?ev a pht:StationErrorEvent .
            ?ev pht:station {ont_pref}:{station_id} .
            ?ev pht:message ?error .
        }}
    """

    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_station_errors")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No error logs for station {station_id} found."
    # TODO ?
    message = f"🚫 Error logs for station {station_id}: "
    for current in response["results"]["bindings"]:
        train = current["train"]["value"]
        error = current["error"]["value"]
        message += f"{train} : {error} ."
    return 2, message


def get_train_errors(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for which errors occured at a train
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?station ?error WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:event ?ev .
            ?ev a pht:StationErrorEvent .
            ?ev pht:station ?station .
            ?ev pht:message ?error .
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_train_errors")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No error logs for train {train_id} found."
    # TODO ?
    message = f"🚫 Error logs for train {train_id}: "
    for current in response["results"]["bindings"]:
        station = current["station"]["value"]
        error = current["error"]["value"]
        message += f"{station}: {error}. "
    return 2, message


def get_train_rejections(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for which stations rejected a given train
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_train_rejections")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No rejections for train {train_id} found."
    message = f"Train {train_id} rejections: "
    for i, current in enumerate(response["response"]["bindings"]):
        station = current["station"]["value"]
        reason = current["reason"]["value"]
        if i == len(response["response"]["bindings"]) - 1:
            message += f" by {station} with reason {reason}."
        else:
            message += f" by {station} with reason {reason},"
    return 2, message


def get_station_rejections(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for which trains a station rejected
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_station_rejections")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No rejections for station {station_id} found."
    message = f"Rejections on station {station_id}:"
    for i, current in enumerate(response["response"]["bindings"]):
        train = current["train"]["value"]
        reason = current["reason"]["value"]
        if i == len(response["response"]["bindings"]) - 1:
            message += f" {train} with reason {reason}."
        else:
            message += f" {train} with reason {reason},"
    return 2, message


def get_train_version(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's version
        train_id: train ID str
        returns: success_code, information as string or error_message
    """

    query_string = f"""
        SELECT ?version WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:version ?version .
        }}
    """

    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_train_version")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No version information for train {train_id} found."

    message = f"Version for train {train_id}: {response['results']['bindings'][0]['version']['value']}."
    return 2, message


def get_station_dataset(station_id: str, piece: str = None):
    """
        Queries blazegraph server for a station's dataset
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?setType WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:dataSet ?dataset .
            OPTIONAL {{?dataset a pht:TabularDataSet .
                        BIND("tabular" AS ?setType)}}
            OPTIONAL {{?dataset a pht:FileDataSet .
                        BIND("file" AS ?setType)}}
        }}
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_station_dataset")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No data set for station {station_id} found."

    # TODO
    result = response["results"]["bindings"][0]["setType"]["value"]
    if result == "file":
        message = f"🗄️ Station {station_id} has the data set format File Data Set. "
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
        message = f"🗄️ Station {station_id} has the data set format Tabular Data Set. "
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
            message += f"Data set theme: {result['theme']['value']}"
        if "pid" in result:
            message += f"Data set identifier: {result['pid']['value']}"
        if "license" in result:
            message += f"Data set license: {result['license']['value']}"
        if "right" in result:
            message += f"Data set right: {result['right']['value']}"
        if "url" in result:
            message += f"Data set access URL: {result['url']['value']}"
        if "char" in result:
            message += f"Data set characteristic: {result['char']['value']}"

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
            message += "Request needed. " if access_constrain == "R" else ("No Access. " if access_constrain == "N" else (  # pylint: disable=line-too-long
                "Unconstrained. " if access_constrain == "U" else "Not Specified. "))
        if "privacy" in result:
            message += "Used Differential Privacy: "
            privacy = result["privacy"]["value"]
            message += "K Anonymity." if privacy == "K" else ("L Diversity." if privacy == "L" else (
                "T Closeness." if privacy == "T" else ("Differntial Privacy." if privacy == "O" else "Undefined.")))

    return 2, message


def get_train_model(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's model
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_train_model")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No model information for train {train_id} found."
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

    if not response_data:
        logging.error(
            "Query failed in module query function get_train_module query_data")
    if response_data["results"]["bindings"]:
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
                message += f"Train {train_id} expects the data set format File Data Set with the expected file type {file_type}."  # pylint: disable=line-too-long

        if result_data == "tabular":
            message += f"Train {train_id} expects the data set format Tabular Data Set."
    return 2, message


def get_station_performance(station_id: str, piece: str = None) -> Tuple[int, bool, bool, dict, dict, str]:
    """
        Queries blazegraph server for memory and CPU usage on a station
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    cpu = True
    mem = True
    if not response_cpu:
        cpu = False
        logging.error(
            "Query failed in module query function get_station_performance query_cpu")
        response_cpu = {}
    if not response_mem:
        mem = False
        logging.error(
            "Query failed in module query function get_station_performance query_mem")
        response_mem = {}
    if not (cpu and mem):
        return 0, cpu, mem, {}, {}, "Something went wrong querying the server."
    if cpu and not response_cpu["results"]["bindings"]:
        cpu = False
    if mem and not response_mem["results"]["bindings"]:
        mem = False
    if not cpu and not mem:
        return 1, cpu, mem, {}, {}, f"No performance for station {station_id} found."
    return 2, cpu, mem, response_cpu, response_mem, ""


def get_train_performance(train_id: str, piece: str = None) -> Tuple[int, bool, bool, dict, dict, str]:
    """
        Queries blazegraph server for memory and CPU usage of a train
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    cpu = True
    mem = True
    if not response_cpu:
        cpu = False
        logging.error(
            "Query failed in module query function get_train_performance query_cpu")
        response_cpu = {}
    if not response_mem:
        mem = False
        logging.error(
            "Query failed in module query function get_train_performance query_mem")
        response_mem = {}
    if not (cpu and mem):
        return 0, cpu, mem, {}, {}, "Something went wrong querying the server."
    if cpu and not response_cpu["results"]["bindings"]:
        cpu = False
    if mem and not response_mem["results"]["bindings"]:
        mem = False
    if not cpu and not mem:
        return 1, cpu, mem, {}, {}, f"No performance for train {train_id} found."
    return 2, cpu, mem, response_cpu, response_mem, ""


def get_train_average(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for average statistics of a train:
        average memory consumption, CPU usage, runtime per station, and the amount of stations visited.
        returns: succes_code, information as string or error message.
    """
    # TODO
    query_string_cpu = f"""
        SELECT ?station ?usage WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:CPUUsageReportEvent .
            ?ev pht:station ?station .
            ?ev pht:value ?usage .
        }}
    """
    response_cpu = blazegraph_query(query_string_cpu)
    query_string_mem = f"""
        SELECT ?station ?usage WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?ev a pht:MemoryUsageReportEvent .
            ?ev pht:station ?station .
            ?ev pht:value ?usage .
        }}
    """
    response_mem = blazegraph_query(query_string_mem)
    query_string_runtime = f"""
        SELECT ?station ?start ?end WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?execution .
            ?execution pht:event ?ev .
            ?evStart a pht:StartedRunningAtStationEvent .
            ?evStart pht:station ?station .
            ?evStart pht:timestamp ?start .
            ?evEnd a pht:FinishedRunningAtStationEvent .
            ?evEnd pht:station ?station .
            ?evEnd pht:timestamp ?end .
        }}
    """
    response_runtime = blazegraph_query(query_string_runtime)
    query_string_route = f"""
        SELECT ?station WHERE {{
            {ont_pref}:{train_id} a pht:Train .
            {ont_pref}:{train_id} pht:execution ?exec .
            ?exec pht:plannedRouteStep ?plan .
            ?plan pht:station ?station .
        }}
    """
    response_route = blazegraph_query(query_string_route)
    cpu = True
    mem = True
    runtime = True
    if not response_cpu:
        cpu = False
        logging.error(
            "Query failed in module query function get_train_average query_cpu")
    if not response_mem:
        mem = False
        logging.error(
            "Query failed in module query function get_train_average query_mem")
    if not response_runtime:
        runtime = False
        logging.error(
            "Query failed in module query function get_train_average query_runtime")
    if not cpu and not mem and not runtime:
        return 0, "Something went wrong querying the server."
    if cpu and not response_cpu["results"]["bindings"]:
        cpu = False
    if mem and not response_mem["results"]["bindings"]:
        mem = False
    if runtime and not response_runtime["results"]["bindings"]:
        runtime = False
    if not cpu and not mem and not runtime:
        return 1, "No average statistics found."

    # get average of cpu and memory usage
    message = f"On average train {train_id}: "
    if cpu:
        total_cpu = 0.0
        total_values = 0
        for i, current in enumerate(response_cpu["results"]["bindings"]):
            usage = float(current["usage"]["value"])
            total_cpu += usage
            total_values = i
        avg_cpu = (total_cpu/total_values)
        if mem or runtime:
            message += f"Had a CPU usage of {avg_cpu} %, "
        else:
            message += f"Had a CPU usage of {avg_cpu} %."
    if mem:
        total_mem = 0.0
        total_values = 0
        for i, current in enumerate(response_mem["results"]["bindings"]):
            usage = float(current["usage"]["value"])
            total_mem += usage
            total_values = i
        avg_mem = (total_mem/total_values)
        if not cpu:
            message += f"Used {avg_mem} MB of memory."
        else:
            message += f"and used {avg_mem} MB of memory."

    # get amount of visited stations + time spent there
    if runtime:
        visited = {}
        for current in response_runtime["results"]["bindings"]:
            station = current["station"]["value"]
            if not station in visited:
                start = current["start"]["value"]
                end = current["end"]["value"]
                visited[station] = {"start": start, "end": end}
        elapsed = []
        for station in visited:
            start = current["start"]["value"]
            # artifact from testing
            if start.startswith("220"):
                start = start[1:]
            # converting dates to datetime objects
            try:
                converted_start = datetime.datetime.strptime(
                    start, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                logging.info("Date does not have the expected format")
                try:
                    converted_start = datetime.datetime.strptime(
                        start, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    logging.warning(
                        "Date does not conform to any format")

            end = current["end"]["value"]
            # artifact from testing
            if end.startswith("220"):
                end = end[1:]
            # converting dates to datetime objects
            try:
                converted_end = datetime.datetime.strptime(
                    end, '%Y-%m-%dT%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                logging.info("Date does not have the expected format")
                try:
                    converted_end = datetime.datetime.strptime(
                        end, '%Y-%m-%d%H:%M:%S.%f%z')
                except Exception:  # pylint: disable=broad-except
                    logging.warning(
                        "Date does not conform to any format")
            delta = converted_end - converted_start
            elapsed_seconds = delta.total_seconds()
            elapsed.append(elapsed_seconds)
        total_stations = len(elapsed)
        avg_time = str(datetime.timedelta(sum(elapsed)/total_stations))
        message += f"The train visited {total_stations} stations in total and spend {avg_time} per station."
        if response_route and response_route["results"]["bindings"]:
            planned_stations = []
            for current in response_route["results"]["bindings"]:
                planned_stations.append(current["station"]["value"])
            non_visited = []
            for station in planned_stations:
                if station not in visited:
                    non_visited.append(station)
            if non_visited:
                message += f"The following stations were scheduled but the train did not run on them (yet): {' '.join(non_visited)}"  # pylint: disable=line-too-long

    return 2, message


def get_station_rights(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a station's rights
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
    query_string = f"""
        SELECT ?right WHERE {{
            {ont_pref}:{station_id} a pht:Station .
            {ont_pref}:{station_id} pht:right ?right .
        }}
        LIMIT 1
    """
    response = blazegraph_query(query_string)
    if not response:
        logging.error(
            "Query failed in module query function get_station_rights")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No rights for station {station_id} found."
    message = f"Rights for station {station_id}:"
    for i, item in enumerate(response["results"]["bindings"]):
        right = item["right"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {right}."
        else:
            message += f" {right},"
    return 2, message


def get_full_route(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's complete planned route
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_full_route")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No route for train {train_id} found."
    route = get_route(response)
    if route[0] == 2:
        return 2, f"Route for train {train_id}: {route[1]}"
    return 1, f"No route for train {train_id} found."


def get_future_route(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's future planned route
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_future_route")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No future route for train {train_id} found."
    route = get_route(response)
    if route[0] == 2:
        return 2, f"Future route for train {train_id}: {route[1]}"
    return 1, f"No future route for train {train_id} found."


def get_past_route(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's past planned route
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_past_route")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No past route for train {train_id} found."
    route = get_route(response)
    if route[0] == 2:
        return 2, f"Past route for train {train_id}: {route[1]}"
    return 1, f"No past route for train {train_id} found."


def get_upcomming_trains(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for which trains are scheduled to visit a given station next
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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

    if not response:
        logging.error(
            "Query failed in module query function get_upcomming_trains")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No scheduled trains for station {station_id} found."

    message = f"Upcoming trains for station {station_id}:"
    for i, current in enumerate(response["results"]["bindings"]):
        train = current["train"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {train}."
        else:
            message += f" {train},"
    return 2, message


def get_station_log(station_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a station's logs
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_station_log")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No logs for station {station_id} found."

    message = f"Logs for station {station_id}:"
    for i, current in enumerate(response["results"]["bindings"]):
        train = current["train"]["value"]
        log = current["log"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {train}: {log}."
        else:
            message += f" {train}: {log},"
    return 2, message


def get_train_log(train_id: str, piece: str = None) -> Tuple[int, str]:
    """
        Queries blazegraph server for a train's logs
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_train_log")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No logs for train {train_id} found."

    message = f"Logs for train {train_id}:"
    for i, current in enumerate(response["results"]["bindings"]):
        station = current["station"]["value"]
        log = current["log"]["value"]
        if i == len(response["results"]["bindings"]) - 1:
            message += f" {station}: {log}."
        else:
            message += f" {station}: {log},"
    return 2, message


def get_station_started_runs(station_id: str, piece: str = None) -> Tuple[int, str]:
    # TODO last vs all
    """
        Queries blazegraph server for started runs on a station
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_station_started_runs")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No started runs for station {station_id} found."

    sorted_values = sort_time_values(response)
    # TODO differ between all started runs an last
    message = f"Last started run on {station_id} on train: {sorted_values[0][1]}"
    return 2, message


def get_train_started_runs(train_id: str, piece: str = None) -> Tuple[int, str]:
    # TODO last vs all
    """
        Queries blazegraph server for a train's started runs
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_train_started_runs")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No started runs for train {train_id} found."

    sorted_values = sort_time_values(response)
    # TODO differ between all started runs an last
    message = f"Last started run for train {train_id} on station: {sorted_values[0][1]}"
    return 2, message


def get_station_finished_runs(station_id: str, piece: str = None) -> Tuple[int, str]:
    # TODO last vs all
    """
        Queries blazegraph server for finished runs on a station
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_station_finished_runs")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No finished runs for station {station_id} found."

    sorted_values = sort_time_values(response)
    return 2, f"Last finished run on station {station_id} by train: {sorted_values[-1][1]}"


def get_train_finished_runs(train_id: str, piece: str = None) -> Tuple[int, str]:
    # TODO last vs all
    """
        Queries blazegraph server for a train's finsished runs
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_train_finished_runs")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No finished runs for train {train_id} found."

    sorted_values = sort_time_values(response)
    message = f"Last finished run for train {train_id} on station: {sorted_values[-1][1]}"
    return 2, message


def get_station_finished_transmission(station_id: str, piece: str = None) -> Tuple[int, str]:
    # TODO last vs all
    """
        Queries blazegraph server for finished transmissions on a station
        station_id: station ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_station_finished_transmissions")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No finished transmissions for station {station_id} found."

    sorted_values = sort_time_values(response)
    message = f"Last finished transmission on station {station_id} by train: {sorted_values[-1][1]}"
    return 2, message


def get_train_finished_transmission(train_id: str, piece: str = None) -> Tuple[int, str]:
    # TODO last vs all
    """
        Queries blazegraph server for a train's finished transmissions
        train_id: train ID str
        returns: success_code, information as string or error_message
    """
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
    if not response:
        logging.error(
            "Query failed in module query function get_train_finished_transmission")
        return 0, "Something went wrong querying the server."
    if not response["results"]["bindings"]:
        return 1, f"No finished transmissions for train {train_id} found."
    sorted_values = sort_time_values(response)
    message = f"Last finished transmission for train {train_id} on station: {sorted_values[-1][1]}"
    return 2, message


def get_route(response: dict) -> Tuple[int, str]:
    """
        Returns a route ordered by steps.
        resonse: blazegraph response for route query.
        returns: success_code, information as string
    """
    step_station = []
    for current in response["results"]["bindings"]:
        step = current["step"]["value"]
        station = current["station"]["value"]
        step_station.extend([[step, station]])

    sorted_values = sorted(step_station, key=lambda c: c[0])

    message = ""

    # TODO: kick out doubles!
    for i, (station, step) in enumerate(sorted_values):
        if i == len(sorted_values) - 1:
            message += f" {station} ({step})."
        else:
            message += f" {station} ({step}) ->"

    return 2, message


def sort_time_values(response: dict) -> list:
    """
        Orders a dict of timestamps and values
        If no timestamp is given it defaults to now
        resonse: blazegraph response for route query.
        returns: ordered list
    """
    time_value = []
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
        value = current["train"]["value"]
        time_value.extend([[converted_time, value]])
    sorted_values = sorted(time_value, key=lambda c: c[0])
    return sorted_values
