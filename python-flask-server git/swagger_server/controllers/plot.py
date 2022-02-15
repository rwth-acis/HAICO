import base64
import datetime
import logging
import time

import fitz
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
#import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# no GUI backend -> plt.show() etc will not work
matplotlib.use('Agg')


def plot_train_cpu(train_id, response):
    pdf_title = plot_usage(train_id, response, "CPU", train_id, "")

    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error("The PDF was not generated.")
        return 0


def plot_train_mem(train_id, response):
    pdf_title = plot_usage(train_id, response, "Memory", train_id, "")

    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error("The PDF was not generated.")
        return 0


def plot_train_performance(train_id, response_cpu, response_mem):
    # inelegant but whatever
    cpu = False
    mem = False
    if response_cpu and response_cpu["results"]["bindings"]:
        cpu = True
        pdf_title_cpu = plot_usage(
            train_id, response_cpu, "CPU", "", train_id)

    if response_mem and response_mem["results"]["bindings"]:
        mem = True
        pdf_title_mem = plot_usage(
            train_id, response_mem, "Memory", "", train_id)

    if not cpu and not mem:
        return 0

    if cpu and mem:
        result = fitz.open()

        for pdf in [f"{pdf_title_cpu}.pdf", f"{pdf_title_mem}.pdf"]:
            with fitz.open(pdf) as mfile:
                result.insertPDF(mfile)
        current_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%d%m%y%f')
        pdf_title = f"{train_id}_performance_{current_date}.pdf"
        result.save(pdf_title)

    else:
        pdf_title = pdf_title_cpu if cpu else pdf_title_mem
    try:
        with open("pdf_title", "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error("The PDF was not generated")
        return 0


def plot_station_performance(station_id, response_cpu, response_mem):

    # inelegant but whatever
    cpu = False
    mem = False
    if response_cpu and response_cpu["results"]["bindings"]:
        cpu = True
        pdf_title_cpu = plot_usage(
            station_id, response_cpu, "CPU", "", station_id)

    if response_mem and response_mem["results"]["bindings"]:
        mem = True
        pdf_title_mem = plot_usage(
            station_id, response_mem, "Memory", "", station_id)

    if not cpu and not mem:
        return 0

    if cpu and mem:
        result = fitz.open()

        for pdf in [f"{pdf_title_cpu}.pdf", f"{pdf_title_mem}.pdf"]:
            with fitz.open(pdf) as mfile:
                result.insertPDF(mfile)
        current_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%d%m%y%f')
        pdf_title = f"{station_id}_performance_{current_date}.pdf"
        result.save(pdf_title)

    else:
        pdf_title = pdf_title_cpu if cpu else pdf_title_mem

    try:
        with open(pdf_title, "rb") as pdf:
            encoded_string = base64.b64encode(pdf.read())
            return encoded_string
    except Exception:  # pylint: disable=broad-except
        logging.error("The PDF was not generated.")
        return 0


def plot_usage(context_id: str, response: dict, resource: str, train_id="", station_id=""):
    if not (train_id and not station_id) or (train_id and station_id):
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
    for item, x in values.items():
        print(item, x)

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
