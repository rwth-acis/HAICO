# pylint: disable=line-too-long
"""
     Stores Slack "interactive" blocks to be returned.
"""
# For some reason jinja didn't really work.
# I also kinda prefer this tbh.

# This made it easier to simply copy the Slack blocks from the block kit.
from typing import List, Dict, Collection
true = True  # pylint: disable=invalid-name


def simple_text(message: str) -> List[Dict[str, Collection[str]]]:
    """
        No decorations or anything just a simple text block.
        returns: Block as list
    """
    block = [
        {
            'type': 'section',
            'text': {
                    'type': 'plain_text',
                    'text': message,
                    'emoji': true,
            },
        },
    ]

    return block


def hello_buttons() -> List[object]:
    """
        Overview buttons.
        To be returned with an intent at the beginning of the conversation.
        returns: Block as list
    """
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hello there! 👋 What would you like to do? I can retrieve information about stations and trains for you."
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚉 Information about stations",
                        "emoji": true
                    },
                    "value": "info_about_stations",
                    "action_id": "info_about_stations"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚂 Information about trains",
                        "emoji": true
                    },
                    "value": "info_about_trains",
                    "action_id": "info_about_trains"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍Show all stations",
                        "emoji": true
                    },
                    "value": "get_all",
                    "action_id": "all_stations"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍Show all trains",
                        "emoji": true
                    },
                    "value": "get_all",
                    "action_id": "all_trains"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚇 Request train",
                        "emoji": true
                    },
                    "value": "information",
                    "action_id": "train_request"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "ℹ️ Tell me more",
                        "emoji": true
                    },
                    "value": "information",
                    "action_id": "information"
                }
            ]
        }
    ]
    return block


def station_selection() -> List[Dict[str, Collection[str]]]:
    """
        Radio buttons to select a station.
        returns: Block as list
    """
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Please select a station."
            },
            "accessory": {
                "type": "radio_buttons",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station UKA",
                            "emoji": true
                        },
                        "value": "station_aachen"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station UKK",
                            "emoji": true
                        },
                        "value": "station_cologne"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Göttingen",
                            "emoji": true
                        },
                        "value": "station_goettingen"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Leipzig",
                            "emoji": true
                        },
                        "value": "station_leipzig"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Leipzig IMISE",
                            "emoji": true
                        },
                        "value": "station_leipzig_imise"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Mittweida",
                            "emoji": true
                        },
                        "value": "station_mittweida"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Beeck",
                            "emoji": true
                        },
                        "value": "station_beeck"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Menzel",
                            "emoji": true
                        },
                        "value": "station_menzel"
                    }
                ],
                "action_id": "station_selection"
            }
        }
    ]

    return block


def train_selection() -> List[Dict[str, Collection[str]]]:
    """
        Radio buttons to select a train.
        returns: Block as list
    """
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚂Please select a train."
            },
            "accessory": {
                "type": "radio_buttons",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Breast Cancer Study",
                            "emoji": true
                        },
                        "value": "train_breast_cancer"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Melanoma Study",
                            "emoji": true
                        },
                        "value": "train_melanoma"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Hello World Train",
                            "emoji": true
                        },
                        "value": "train_hello_world"
                    }
                ],
                "action_id": "train_selection"
            }
        }
    ]
    return block


def station_block(station_id: str, station_name: str = "") -> List[object]:
    """
        Buttons to select which station information (in action_id) to retrieve.
        station_name: Name of the station, can be empty
        station_id: Station ID, will be set as value so it is necessary
        returns: blocks as dict
    """
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🚉 So you want to know more about the station {station_name}!"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "ℹ️ General info",
                        "emoji": true
                    },
                    "value": station_id,
                    "action_id": "station_info"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚂 Current train @ station",
                        "emoji": true
                    },
                    "value": station_id,
                    "action_id": "current_at_station"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🕰 Next trains",
                        "emoji": true
                    },
                    "value": station_id,
                    "action_id": "upcomming_trains"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📈 Performance ",
                        "emoji": true
                    },
                    "value": station_id,
                    "action_id": "station_performance"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⛔️ Errors"
                    },
                    "value": station_id,
                    "action_id": "station_errors"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🗄 Dataset"
                    },
                    "value": station_id,
                    "action_id": "station_dataset"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "💻 Computational Environment"
                    },
                    "value": station_id,
                    "action_id": "comp_env"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "👷 Owner"
                    },
                    "value": station_id,
                    "action_id": "station_owner"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🤵 Responsible"
                    },
                    "value": station_id,
                    "action_id": "station_responsible"
                }
            ]
        }
    ]
    return block


def train_block(train_id: str, train_name: str = "") -> List[object]:
    """
        Buttons to select which train information (in action_id) to retrieve.
        train_name: Name of the train, can be empty
        train_id: Train ID, will be set as value so it is necessary
        returns: blocks as dict
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🚂 So you want to know more about station {train_name}!"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "ℹ️ General info",
                        "emoji": true
                    },
                    "value": train_id,
                    "action_id": "train_info"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚉 Current station",
                        "emoji": true
                    },
                    "value": train_id,
                    "action_id": "current_station"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🗺 Future route",
                        "emoji": true
                    },
                    "value": train_id,
                    "action_id": "future_route"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📈 Performance ",
                        "emoji": true
                    },
                    "value": train_id,
                    "action_id": "train_performance"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⛔️ Errors"
                    },
                    "value": train_id,
                    "action_id": "train_errors"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🗄 Model"
                    },
                    "value": train_id,
                    "action_id": "train_model"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📚 Logs"
                    },
                    "value": train_id,
                    "action_id": "train_log"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "👷 Creator"
                    },
                    "value": train_id,
                    "action_id": "train_creator"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🤵 Publisher"
                    },
                    "value": train_id,
                    "action_id": "train_publisher"
                }
            ]
        }
    ]
    return blocks


def train_request_block() -> List[Dict[str, Collection[str]]]:
    """
        Modal block of the train request
        returns: Block as list
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚏 Please select a route for the train Hello World. "
            },
            "accessory": {
                "type": "multi_static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select options",
                    "emoji": true
                },
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station UKA",
                            "emoji": true
                        },
                        "value": "station_aachen"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station UKK",
                            "emoji": true
                        },
                        "value": "station_cologne"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Göttingen",
                            "emoji": true
                        },
                        "value": "station_goettingen"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Leipzig",
                            "emoji": true
                        },
                        "value": "station_leipzig"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Leipzig IMISE",
                            "emoji": true
                        },
                        "value": "station_leipzig_imise"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Mittweida",
                            "emoji": true
                        },
                        "value": "station_mittweida"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Beeck",
                            "emoji": true
                        },
                        "value": "station_beeck"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station Menzel",
                            "emoji": true
                        },
                        "value": "station_menzel"
                    }
                ],
                "action_id": "train_route"
            }
        }
    ]
    return blocks


def image_block(url: str, piece_id: str) -> List[Dict[str, Collection[str]]]:
    blocks = [
        {
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": f"Performance details for {piece_id}",
                "emoji": true
            },
            "image_url": url,
            "alt_text": "performance graph"
        }
    ]

    return blocks
