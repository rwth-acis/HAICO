# HAICO

## Overview

This server was generated by the [swagger-codegen](https://github.com/swagger-api/swagger-codegen) project.

This server uses the [Connexion](https://github.com/zalando/connexion) library on top of Flask.

## Getting Started

### Prerequisites

Python 3.5.2+

### Installation

To install the requirements, please execute the following from the root directory:

```bash
pip3 install -r requirements.txt
BLAZEGRAPHURL=$blazegraph_endpoint LOGINNAME=$username PASSWORD=$password REQUESTURL=$train_request_endpoint TOKEN=$slack_token
HOST=$host_url
python3 -m swagger_server
```

BLAZEGRAPHURL: Endpoint of the blazegraph database (required)
LOGINNAME: User name for the train request endpoint (optional, for train requests)
PASSWORD: Password for the train request endpoint (optional, for train requests)
REQUESTURL: Request endpoint (optional, for train requests)
TOKEN: Slack token (optional, for user notifications)
HOST: The base address of your host (optional, for serving images)
E.g:

```
BLAZEGRAPHURL=http://blazegraph.ba-kunz:9999/bigdata/sparql
LOGINNAME=testname
PASSWORD=testpasswort
REQUESTURL=https://padme-analytics.de
TOKEN=xoxb-etc-bla-bla
HOST=https://milki-psy.dbis.rwth-aachen.de
```

The Swagger definition lives here:

```
http://localhost:8081/api/swagger.json
```

### Running with Docker

To run the server on a Docker container, please execute the following from the root directory:

```bash
# building the image
docker build -t swagger_server .

# starting up a container
docker run -p 8081:8081 -e BLAZEGRAPHURL=$blazegraph_endpoint -e LOGINNAME=$username -e PASSWORD=$password -e REQUESTURL=$train_request_endpoint swagger_server
```

### Usage as a Bot

This server can also be used as a bot. Please note, that this server requires -- as is -- the SBF and Blazegraph to run. 
Test data for the Blazegraph database and training data for the Rasa NLU can be found in the directory `/bot`. 
The final bot model can be found there, too.

## Evaluation Results
Table 1: Results of the SUS and transparency questionnaire.
The score is an ordinal scale where 1 = "strongly disagree" and 5 = "strongly agree" (n=50).

| #   | Questions of the SUS questionnaire                                                   | Avg  | SD     |
| --- | ------------------------------------------------------------------------------------ | ---- | ------ |
| 1   | I think that I would like to use HAICO frequently.                                   | 3.42 | ± 1.13 |
| 2   | I found HAICO unnecessarily complex.                                                 | 1.8  | ± 0.85 |
| 3   | I thought HAICO was easy to use.                                                     | 4.24 | ± 0.74 |
| 4   | I think that I would need the support of a technical person to be able to use HAICO. | 1.72 | ± 0.92 |
| 5   | I found the various functions in HAICO were well integrated.                         | 3.94 | ± 0.81 |
| 6   | I thought there was too much inconsistency in HAICO.                                 | 1.86 | ± 0.94 |
| 7   | I would imagine that most people would learn to use HAICO very quickly.              | 4.26 | ± 0.87 |
| 8   | I found HAICO very cumbersome to use.                                                | 1.94 | ± 1.05 |
| 9   | I felt very confident using HAICO.                                                   | 3.74 | ± 0.93 |
| 10  | I needed to learn a lot of things before I could get going with HAICO.               | 1.84 | ± 0.88 |

| #   | Questions of the transparency questionnaire                               | Avg  | SD     |
| --- | ------------------------------------------------------------------------- | ---- | ------ |
| 11  | I understood the bot's responses.                                         | 4.2  | ± 0.81 |
| 12  | When the bot encountered an error, its error messages were helpful.       | 3.36 | ± 0.98 |
| 13  | I found the information I was looking for.                                | 4    | ± 0.97 |
| 14  | Using the bot gave me a better overview of the PHT.                       | 3.66 | ± 0.94 |
| 15  | Using the bot, I understood what`s currently happening in the PHT system. | 3.66 | ± 1    |
| 16  | The bot created more transparency for the PHT.                            | 3.84 | ± 1.04 |