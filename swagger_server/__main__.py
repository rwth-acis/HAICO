#!/usr/bin/env python3
# type: ignore
# pylint: disable=all
import connexion
from flask import request
from swagger_server.controllers import poll
from swagger_server import encoder


def log_req():
    # This is for debugging purposes to see the payload
    print("New request", flush=True)
    print(request.get_data(), flush=True)


def main():
    poll.start_polling(25)
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.app.url_map.strict_slashes = False
    app.app.before_request(log_req)
    app.add_api('swagger.yaml', arguments={
                'title': 'Swagger Parser Microservice'})
    app.run(port=8081)  # pass debug=True here to enable debug mode


if __name__ == '__main__':
    main()
