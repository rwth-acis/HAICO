import json


def simple_text(message: str):
    block = {
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'plain_text',
                    'text': message,
                    'emoji': "true",
                },
            },
        ],
    }
    return block


def hello_buttons():
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
                        "emoji": "true"
                    },
                    "value": "info_about_stations",
                    "action_id": "info_about_stations"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚂 Information about trains",
                        "emoji": "true"
                    },
                    "value": "info_about_trains",
                    "action_id": "info_about_trains"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍Show all stations",
                        "emoji": "true"
                    },
                    "value": "get_all",
                    "action_id": "all_stations"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍Show all trains",
                        "emoji": "true"
                    },
                    "value": "get_all",
                    "action_id": "all_trains"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚇 Request train",
                        "emoji": "true"
                    },
                    "value": "information",
                    "action_id": "train_request"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "ℹ️ Tell me more",
                        "emoji": "true"
                    },
                    "value": "information",
                    "action_id": "information"
                }
            ]
        }
    ]
    return block


def station_selection():
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
                            "text": "Bruegel",
                            "emoji": "true"
                        },
                        "value": "station_bruegel"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Privat-Weber",
                            "emoji": "true"
                        },
                        "value": "station_privat-weber"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Privat-TEST",
                            "emoji": "true"
                        },
                        "value": "station_privat-test"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Private-Weber2",
                            "emoji": "true"
                        },
                        "value": "station_privat-weber2"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Private-Welten",
                            "emoji": "true"
                        },
                        "value": "station_privat-welten"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "HSMW",
                            "emoji": "true"
                        },
                        "value": "station_HSMW"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Melanoma Station",
                            "emoji": "true"
                        },
                        "value": "station_melanoma"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "MDS Station",
                            "emoji": "true"
                        },
                        "value": "station_mds"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "PHT MDS Leipzig",
                            "emoji": "true"
                        },
                        "value": "station_pht_leipzig"
                    }
                ],
                "action_id": "station_selection_1"
            }
        },
        {
            "type": "section",
            "text": {
                    "type": "mrkdwn",
                    "text": " "
            },
            "accessory": {
                "type": "radio_buttons",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "PHT IMISE LEIPZIG",
                            "emoji": "true"
                        },
                        "value": "station_imise_leipzig"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station-UKA",
                            "emoji": "true"
                        },
                        "value": "station_uka"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station-UKK",
                            "emoji": "true"
                        },
                        "value": "station_ukk"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station-UMG",
                            "emoji": "true"
                        },
                        "value": "station_umg"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Station-UMG_temp",
                            "emoji": "true"
                        },
                        "value": "station_umg_tmp"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "aachenbeeck",
                            "emoji": "true"
                        },
                        "value": "station_aachenbeeck"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "aachenmenzel",
                            "emoji": "true"
                        },
                        "value": "station_aachenmenzel"
                    }
                ],
                "action_id": "station_selection_2"
            }
        }
    ]
    return block


def train_selection():
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
                            "emoji": "true"
                        },
                        "value": "train_breast_cancer"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Melanoma Study",
                            "emoji": "true"
                        },
                        "value": "train_melanoma"
                    }
                ],
                "action_id": "train_selection"
            }
        }
    ]
    return block


def station_block(station_name: str, station_id: str):
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🚉 So you want to know more about station {station_name}!"
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
                        "emoji": "true"
                    },
                    "value": station_id,
                    "action_id": "station_info"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚂 Current train @ station",
                        "emoji": "true"
                    },
                    "value": station_id,
                    "action_id": "current_at_station"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🕰 Next trains",
                        "emoji": "true"
                    },
                    "value": station_id,
                    "action_id": "upcomming_trains"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📈 Average performance ",
                        "emoji": "true"
                    },
                    "value": station_id,
                    "action_id": "station_performance_avg"
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


def train_block(train_name: str, train_id: str):
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
                        "emoji": "true"
                    },
                    "value": train_id,
                    "action_id": "train_info"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚉 Current station",
                        "emoji": "true"
                    },
                    "value": train_id,
                    "action_id": "current_station"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🗺 Future route",
                        "emoji": "true"
                    },
                    "value": train_id,
                    "action_id": "future_route"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📈 Average performance ",
                        "emoji": "true"
                    },
                    "value": train_id,
                    "action_id": "train_performance_avg"
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


def train_request_modal():
    modal = {
        "type": "modal",
        "title": {
                "type": "plain_text",
                "text": "🚂 Request a new train",
                "emoji": "true"
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": "true"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": "true"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Please note: currently you can only select a train route. \n Requesting a different train than the default is not yet supported."
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select options",
                        "emoji": "true"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Bruegel",
                                "emoji": "true"
                            },
                            "value": "station_bruegel"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Privat-Weber",
                                "emoji": "true"
                            },
                            "value": "station_privat-weber"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Privat-TEST",
                                "emoji": "true"
                            },
                            "value": "station_privat-test"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Private-Weber2",
                                "emoji": "true"
                            },
                            "value": "station_privat-weber2"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Private-Welten",
                                "emoji": "true"
                            },
                            "value": "station_privat-welten"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "HSMW",
                                "emoji": "true"
                            },
                            "value": "station_HSMW"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Melanoma Station",
                                "emoji": "true"
                            },
                            "value": "station_melanoma"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "MDS Station",
                                "emoji": "true"
                            },
                            "value": "station_mds"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "PHT MDS Leipzig",
                                "emoji": "true"
                            },
                            "value": "station_pht_leipzig"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "PHT IMISE LEIPZIG",
                                "emoji": "true"
                            },
                            "value": "station_imise_leipzig"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Station-UKA",
                                "emoji": "true"
                            },
                            "value": "station_uka"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Station-UKK",
                                "emoji": "true"
                            },
                            "value": "station_ukk"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Station-UMG",
                                "emoji": "true"
                            },
                            "value": "station_umg"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Station-UMG_temp",
                                "emoji": "true"
                            },
                            "value": "station_umg_tmp"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "aachenbeeck",
                                "emoji": "true"
                            },
                            "value": "station_aachenbeeck"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "aachenmenzel",
                                "emoji": "true"
                            },
                            "value": "station_aachenmenzel"
                        }
                    ],
                    "action_id": "multi_static_select-action"
                },
                "label": {
                    "type": "plain_text",
                            "text": "Please select a train route:",
                    "emoji": "true"
                }
            }
        ]

    }
    return modal
