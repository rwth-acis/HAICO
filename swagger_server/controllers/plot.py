"""Module to plot CPU and memory usage."""

import base64
import datetime
import logging
import time
from typing import Tuple

#import fitz
from PyPDF2 import PdfFileMerger
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
# import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# no GUI backend -> plt.show() etc will not work
matplotlib.use('Agg')


def plot_train_cpu(train_id: str, response: dict) -> Tuple[int, str]:
    """
        Plots the a train's CPU usage
        response: CPU usage response from blazegraph
        returns: success_code, base64 encoded pdf or error message
    """
    pdf_title = plot_usage(train_id, response, "CPU", train_id, "")

    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return 2, encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error(
            "The PDF was not generated module plot function plot_train_cpu.")
        return 0, "Something went wrong: The performance plot could not be generated"


def plot_train_mem(train_id: str, response: str) -> Tuple[int, str]:
    """
        Plots the a train's memory usage
        response: memory usage response from blazegraph
        returns: success_code, base64 encoded pdf or error message
    """
    pdf_title = plot_usage(train_id, response, "Memory", train_id, "")

    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return 2, encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error(
            "The PDF was not generated module plot function plot_train_mem.")
        return 0, "Something went wrong: The performance plot could not be generated"


def plot_train_performance(train_id: str, cpu: bool, mem: bool, response_cpu: bool, response_mem: bool) -> Tuple[int, str]:
    """
        Plots the a train's performance.
        cpu: flag if CPU usage is present
        mem: flag if memory usage is present
        response_cpu: CPU usage response from blazegraph
        response_mem: memory usage response from blazegraph
        returns: success_code, base64 encoded pdf or error message
    """
    if cpu:
        pdf_title_cpu = plot_usage(
            train_id, response_cpu, "CPU", train_id, "")

    if mem:
        pdf_title_mem = plot_usage(
            train_id, response_mem, "Memory", train_id, "")

    if not cpu and not mem:
        return 0, "No information about CPU and Memory Usage present."

    if cpu and mem:
        merger = PdfFileMerger()

        pdfs = [pdf_title_cpu, pdf_title_mem]
        # for pdf in [f"{pdf_title_cpu}", f"{pdf_title_mem}"]:
        #     with fitz.open(pdf) as mfile:
        #         result.insert_pdf(mfile)
        for pdf in pdfs:
            merger.append(pdf)
        current_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%d%m%y%f')
        pdf_title = f"{train_id}_performance_{current_date}.pdf"
        merger.write(pdf_title)
        merger.close()
        # result = fitz.open()

        # for pdf in [f"{pdf_title_cpu}", f"{pdf_title_mem}"]:
        #     with fitz.open(pdf) as mfile:
        #         result.insert_pdf(mfile)

    else:
        pdf_title = pdf_title_cpu if cpu else pdf_title_mem
    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return 2, encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error(
            "The PDF was not generated module plot function plot_train_performance.")
        return 0, "Something went wrong: The performance plot could not be generated"


def plot_station_performance(station_id: str, cpu: str, mem: str, response_cpu: str, response_mem: str) -> Tuple[int, str]:
    """
        Plots the a station's performance.
        cpu: flag if CPU usage is present
        mem: flag if memory usage is present
        response_cpu: CPU usage response from blazegraph
        response_mem: memory usage response from blazegraph
        returns: success_code, base64 encoded pdf or error message
    """
    if cpu:
        pdf_title_cpu = plot_usage(
            station_id, response_cpu, "CPU", "", station_id)

    if mem:
        pdf_title_mem = plot_usage(
            station_id, response_mem, "Memory", "", station_id)

    if not cpu and not mem:
        return 0, "No information about CPU and Memory Usage present."

    if cpu and mem:
        #result = fitz.open()
        merger = PdfFileMerger()

        # pdf_cpu = open(pdf_title_cpu, "rb")
        # pdf_mem = open(pdf_title_mem, "rb")
        pdfs = [pdf_title_cpu, pdf_title_mem]
        # for pdf in [f"{pdf_title_cpu}", f"{pdf_title_mem}"]:
        #     with fitz.open(pdf) as mfile:
        #         result.insert_pdf(mfile)
        for pdf in pdfs:
            merger.append(pdf)
        current_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%d%m%y%f')
        pdf_title = f"{station_id}_performance_{current_date}.pdf"
        merger.write(pdf_title)
        merger.close()

    else:
        pdf_title = pdf_title_cpu if cpu else pdf_title_mem

    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return 2, encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error(
            "The PDF was not generated module plot function plot_station_performance.")
        return 0, "Something went wrong: The performance plot could not be generated"


def plot_usage(context_id: str, response: dict, resource: str, train_id: str, station_id: str) -> str:
    """
        Plots usage as a half donut or time - usage diagram.
        context_id: station or train ID
        reponse: blazegraph response (should not be empty)
        resource: Train or Station
        train_id: ID of train. "" if a station's performance should be plotted.
        station_id: ID of station. "" if a train's performance should be plotted.
        returns: title of the created PDF
    """
    if (not train_id and not station_id) or (train_id and station_id):
        logging.warning(
            f"train_id: {train_id}, station_id: {station_id}. Output may be unexpected.")
    current_date = datetime.datetime.strftime(
        datetime.datetime.now(), '%d%m%y%f')
    pdf_title = f"{context_id}_{resource}_{current_date}.pdf"

    if train_id:
        in_response = "station"
    else:
        in_response = "train"

    values = order_values(response, in_response)

    with PdfPages(pdf_title) as pdf:
        for key, item in values.items():
            plot_title = f"{resource} usage for train {context_id} on station {key} "
            if not train_id:
                plot_title = f"{resource} usage for train {key} on station {context_id} "
            if len(item) == 1:
                # there's only one pair (time, usage) hence there's no use in displaying
                # that on a time scale
                # produces a half donut diagram

                usage = int(item[0][1])
                rest = 100 - usage
                # we do not need labels here
                label = ["", "", ""]
                # 50% of the donut shall be blanc
                values = [rest, usage, rest+usage]

                # color = [rest(lightgrey), usage(darkgreen), blanc(white)]
                color = ['#d3d3d3', '#006b3c', 'w']
                fig, ax = plt.subplots(figsize=(5, 5))
                x1, y1 = -0.4, -0.05
                ax.annotate(f"{resource} usage: {usage} %", xy=(x1, y1))
                wedges, labels = plt.pie(values, wedgeprops=dict(
                    width=0.3, edgecolor='w'), labels=label, colors=color)
                # for the invisble part of the donut
                wedges[-1].set_visible(False)

                plt.rcParams["axes.titlesize"] = 8
                date = item[0][0]
                plt.title(
                    plot_title + f" at {date.strftime('%d.%m.%Y %H:%M:%S')}", loc='center', wrap=True)

                pdf.savefig()
            else:
                x_values = []
                y_values = []
                sorted_date_values = sorted(item, key=lambda c: c[0])
                for date, val in sorted_date_values:
                    x_values.append(date)
                    y_values.append(val)

                fig, ax = plt.subplots()
                plt.plot(x_values, y_values, '-o')
                plt.rcParams["axes.titlesize"] = 8
                plt.xlabel("Date and Time")
                unit = "MB"
                if resource.lower() == "cpu":
                    unit = "%"
                plt.ylabel(f"{resource} Usage in {unit}")
                plt.title(plot_title)
                plt.gcf().autofmt_xdate()
                ax.set_ylim(ymin=0)
                date_format = mdates.DateFormatter('%d.%m. %H:%M')
                plt.gca().xaxis.set_major_formatter(date_format)
                pdf.savefig()
        plt.close()
    return pdf_title


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
    for current in tmp:
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
    return values
