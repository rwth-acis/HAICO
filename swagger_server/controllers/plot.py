"""Module to plot CPU and memory usage."""

import base64
import datetime
import logging
import time
from typing import Tuple

import matplotlib
#import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from PIL import Image

# no GUI backend -> plt.show() etc will not work
matplotlib.use('Agg')


def describe_usage(values: dict, title: str, train: bool, cpu: bool):
    """
     Temporary solution.
    """
    single_value = {}
    multi_value = {}
    print(values)
    for key, item in values.items():
        if len(item) == 1:
            single_value[key] = item
        else:
            multi_value[key] = item
    print(single_value)
    print(multi_value)
    if train:
        piece = "station"
        where = "On"
    else:
        piece = "train"
        where = "By"
    if cpu:
        unit = "%"
    else:
        unit = "MB"
    message = title
    if single_value:
        for key, item in single_value.items():
            usage = item[0][1]
            message += f"{where} {key} : {usage}{unit}. "
    if multi_value:
        for key, item in multi_value.items():
            values = []
            for date, val in item:
                values.append(float(val))
            avg = (sum(values) / (len(values)))
            message += f"{where} {key} : {avg}{unit}. "
    print(message)
    return message


def plot_train_cpu(train_id: str, response: dict) -> Tuple[int, str]:
    """
        Plots the a train's CPU usage
        response: CPU usage response from blazegraph
        returns: success_code, base64 encoded png file or error message
    """
    title = f"CPU Usage in % for train {train_id}. "
    message = describe_usage(order_values(
        response, "station"), title, True, True)
    return message
    # image_title = draw_usage(order_values(
    #     response, "station"), f"CPU Usage in % for train {train_id}", True)
    # try:
    #     with open(image_title, "rb") as png:
    #         encoded_string = base64.b64encode(png.read())
    #         return 2, encoded_string
    # except Exception:  # pylint: disable=broad-except
    #     logging.error(
    #         "The png file was not generated module plot function plot_train_cpu.")
    #     return 0, "Something went wrong: The performance plot could not be generated"


def plot_train_mem(train_id: str, response: str) -> Tuple[int, str]:
    """
        Plots the a train's memory usage
        response: memory usage response from blazegraph
        returns: success_code, base64 encoded png file or error message
    """
    title = f"Memory Usage in MB for train {train_id}. "
    message = describe_usage(order_values(
        response, "station"), title, True, False)
    return message
    # image_title = draw_usage(order_values(
    #     response, "station"), f"Memory Usage in MB for train {train_id}", True)

    # try:
    #     with open(image_title, "rb") as png:
    #         encoded_string = base64.b64encode(png.read())
    #         return 2, encoded_string
    # except Exception:  # pylint: disable=broad-except
    #     logging.error(
    #         "The png file was not generated module plot function plot_train_mem.")
    #     return 0, "Something went wrong: The performance plot could not be generated"


def plot_train_performance(train_id: str, cpu: bool, mem: bool, response_cpu: bool, response_mem: bool) -> Tuple[int, str]:
    """
        Plots the a train's performance.
        cpu: flag if CPU usage is present
        mem: flag if memory usage is present
        response_cpu: CPU usage response from blazegraph
        response_mem: memory usage response from blazegraph
        returns: success_code, base64 encoded png file or error message
    """
    message = ""
    if cpu:
        # print(response_cpu)
        title = f"CPU Usage in % for train {train_id}. "
        message += describe_usage(order_values(response_cpu, "station"),
                                  title, True, True)
        # image_title_cpu = image_title = draw_usage(order_values(
        #     response_cpu, "station"), f"CPU Usage in % for train {train_id}", True)

    if mem:
        title = f"Memory Usage in MB for train {train_id}. "
        message += describe_usage(order_values(response_mem, "station"),
                                  title, True, False)
        # image_title_mem = draw_usage(order_values(response_mem, "station"),
        #                              f"Memory Usage in MB for train {train_id}", True)

    if not cpu and not mem:
        return 0, "No information about CPU and Memory Usage present."

    return 2, message
    # if cpu and mem:
    #     current_date = datetime.datetime.strftime(
    #         datetime.datetime.now(), '%d%m%y%f')
    #     image_title = f"{train_id}_performance_{current_date}.png"
    #     images = [Image.open(x) for x in [image_title_mem, image_title_cpu]]
    #     widths, heights = zip(*(i.size for i in images))

    #     total_width = sum(widths)
    #     max_height = max(heights)

    #     new_image = Image.new('RGB', (total_width, max_height))

    #     x_offset = 0
    #     for image in images:
    #         new_image.paste(image, (x_offset, 0))
    #         x_offset += image.size[0]

    #     new_image.save(image_title)

    # else:
    #     image_title = image_title_cpu if cpu else image_title_mem
    # try:
    #     with open(image_title, "rb") as png:
    #         encoded_string = base64.b64encode(png.read())
    #         return 2, encoded_string
    # except Exception:  # pylint: disable=broad-except
    #     logging.error(
    #         "The png file was not generated module plot function plot_train_performance.")
    #     return 0, "Something went wrong: The performance plot could not be generated"


def plot_station_performance(station_id: str, cpu: str, mem: str, response_cpu: str, response_mem: str) -> Tuple[int, str]:
    """
        Plots the a station's performance.
        cpu: flag if CPU usage is present
        mem: flag if memory usage is present
        response_cpu: CPU usage response from blazegraph
        response_mem: memory usage response from blazegraph
        returns: success_code, base64 encoded png file or error message
    """
    message = ""
    if cpu:
        title = f"CPU Usage in % for station {station_id}. "
        message += describe_usage(order_values(response_cpu, "train"),
                                  title, False, True)
        # image_title_cpu = draw_usage(order_values(response_cpu, "train"),
        #                              f"CPU Usage in % on station {station_id}", False)

    if mem:
        title = f"CPU Usage in % for station {station_id}. "
        message += describe_usage(order_values(response_mem, "train"),
                                  title, False, False)
        # image_title_mem = draw_usage(order_values(response_mem, "train"),
        #                              f"Memory Usage in MB on station {station_id}", False)

    if not cpu and not mem:
        return 0, "No information about CPU and Memory Usage present."

    return 2, message
    # if cpu and mem:
    #     current_date = datetime.datetime.strftime(
    #         datetime.datetime.now(), '%d%m%y%f')
    #     image_title = f"{station_id}_performance_{current_date}.png"
    #     images = [Image.open(x) for x in [image_title_mem, image_title_cpu]]
    #     widths, heights = zip(*(i.size for i in images))

    #     total_width = sum(widths)
    #     max_height = max(heights)

    #     new_image = Image.new('RGB', (total_width, max_height))

    #     x_offset = 0
    #     for image in images:
    #         new_image.paste(image, (x_offset, 0))
    #         x_offset += image.size[0]

    #     new_image.save(image_title)

    # else:
    #     image_title = image_title_cpu if cpu else image_title_mem

    # try:
    #     with open(image_title, "rb") as png:
    #         encoded_string = base64.b64encode(png.read())
    #         return 2, encoded_string
    # except Exception:  # pylint: disable=broad-except
    #     logging.error(
    #         "The png file was not generated module plot function plot_station_performance.")
    #     return 0, "Something went wrong: The performance plot could not be generated"


def draw_usage(values: dict, plot_title: str, train: bool) -> str:
    """
        Plots usage as a half donut or time - usage diagram.
        values: ordered dict of station/ train - data - usage pairs
        plot_title: Title of the created plot
        train: indicates whether a station's(False) or a train's(True) performance is plotted
        returns: title of the created png file
    """
    # note: this is very stupid but matplotlib is not making me very happy so I gotta live with that
    amount_subplots = 1
    # note: this is just as stupid but(!) I cannot think math right now
    rows = 1
    cols = 1
    single_value = {}
    multi_value = {}
    for key, item in values.items():
        if len(item) == 1:
            amount_subplots += 1
            if (rows * cols) / amount_subplots < 1:
                if rows <= cols:
                    rows += 1
                else:
                    cols += 1
            single_value[key] = item
        else:
            multi_value[key] = item
    # TODO maybe change figsize later on
    fig, axs = plt.subplots(nrows=rows, ncols=cols,
                            figsize=(7, 7), squeeze=False)
    fig.suptitle(plot_title, fontsize=16)
    # axs[0,0] is the only plot with multiple lines
    if multi_value:
        axs[0, 0].set_title(plot_title)
        axs[0, 0].set_ylabel("Usage")  # TODO
        for key, item in multi_value.items():
            x_values = []
            y_values = []
            sorted_date_values = sorted(item, key=lambda c: c[0])
            for date, val in sorted_date_values:
                x_values.append(date)
                y_values.append(val)
            axs[0, 0].plot(x_values, y_values, '-o', label=f'{key}')
        axs[0, 0].legend(prop={'size': 6})

    row_index = 1 if multi_value else 0
    col_index = 0

    for key, item in single_value.items():
        usage = float(item[0][1])
        rest = 100.0 - usage
        # we do not need labels here
        label = ["", "", ""]
        # 50% of the donut shall be blanc
        values = [rest, usage, rest + usage]

        # color = [rest(lightgrey), usage(darkgreen), blanc(white)]
        color = ['#d3d3d3', '#006b3c', 'w']
        axs[row_index, col_index].set_title(
            f"{plot_title} for {key} ({usage})", fontsize=10)
        wedges, labels = axs[row_index, col_index].pie(values, wedgeprops=dict(
            width=0.3, edgecolor='w'), labels=label, colors=color)
        wedges[-1].set_visible(False)
        if row_index == rows:
            col_index += 1
            row_index = 0

    # save
    current_date = datetime.datetime.strftime(
        datetime.datetime.now(), '%d%m%y%f')

    part = "train" if train else "station"
    image_title = f"{part}_{current_date}.png"
    plt.savefig(image_title, bbox_inches='tight', dpi=500)
    plt.close()

    return image_title


def order_values(response: dict, target_str: str) -> dict:
    """
        Orders the response into a a dict by timestamp.
        If a timestamp is missing the default will be set to now.
        reponse: blazegraph response
        target_str: station if a train's usage is ploted, train if a station's usage is plotted
        returns: a dict ordered by timestamps

    """
    values = {}
    tmp = response["results"]["bindings"]
    print(tmp)
    for current in tmp:
        print(current)
        target = current[target_str]["value"]
        date = current["time"]["value"]

        # artifact from testing
        if date.startswith("220"):
            date = date[1:]

        # converting dates to datetime objects
        try:
            converted_date = datetime.datetime.strptime(
                date, '%Y-%m-%dT%H:%M:%S.%f%z')
        except Exception:  # pylint: disable=broad-except
            logging.info("Date does not have the expected format")
            try:
                converted_date = datetime.datetime.strptime(
                    date, '%Y-%m-%d%H:%M:%S.%f%z')
            except Exception:  # pylint: disable=broad-except
                logging.warning(
                    "Date does not conform to any format")
                converted_date = datetime.datetime.fromtimestamp(
                    time.time())
        usage = float(current["usage"]["value"])
        if target not in values:
            values[target] = [[converted_date, usage]]
        else:
            values[target].extend([[converted_date, usage]])
    print(values)
    return values
