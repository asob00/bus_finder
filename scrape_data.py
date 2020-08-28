"""Data scraper

This script downloads all useful data from MPK Kraków website:
http://rozklady.mpk.krakow.pl
And saves it into file "lines_stops_times_dict" as dictionary,
further used to create buss connections graph used in BusFinder app

This tool requiresc that 'bs4' is installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains functions:

* timetable_dict_to_list - convert timetable dict to list
* get_timetable_http_table - converts html table into list of bus stop-times
* generate_timetable - runs get_timetable_http_table function
                       required amount of times (depends on bus type)
* download_timetables - downloads each bus each stop web page,
                        with acquired data runs generate_timetable function
* progress_bar - responsible for showing progress bar
* main - the main function of the script
"""

import requests
import json
import re
from bs4 import BeautifulSoup

headers = {'Host': 'rozklady.mpk.krakow.pl',
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language': 'en-US,en;q=0.5',
           'Accept-Encoding': 'gzip, deflate',
           'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
           'Cookie': 'ROZKLADY_JEZYK=PL; ROZKLADY_WIDTH=2000; ROZKLADY_WIZYTA=21; ROZKLADY_OSTATNIA=1591350104; '
                     'ROZKLADY_AB=0;',
           'Cache-Control': 'max-age=0'}
unicode = "utf-8"
parser = 'html.parser'


def timetable_dict_to_list(timetable):
    """Converts timetable in form of dict into list in specified below format

    :type timetable: dict
    :param timetable: bus timetable keys - hours, values - minutes

    :return: list of bus stop times, in simplified format: hour+minute is represented by number of minutes from midnight
             eg. 12:00 is 12 * 60 + 0 = 720, 15:37 is 15 * 60 + 37 = 937
    """
    times = []

    for hour, value in timetable.items():
        for minutes in value.split(' '):
            if minutes != '':
                times.append(hour * 60 + int(minutes[0:2]))

    return times


def get_timetable_http_table(hours_list, minutes_list, type_of_bus, day, thick_hour=None, thick_minutes=None):
    """
    :type hours_list: list
    :param hours_list: list of <td> parameters in table containing hours

    :type minutes_list: list
    :param minutes_list: list of <td> parameters in table containing minutes

    :type type_of_bus: int
    :param type_of_bus: tells if bus goes only on weekdays or weekdays + saturday or whole week

    :type day: int
    :param day: tells which day of week is currently being processed (0 - weekdays, 1 - saturday, 2 - sunday)

    :type: thick_hour: int
    :param thick_hour: <td> parameter in table containing hour with different CSS style (thicker bottom line)

    :type thick_minutes: list
    :param thick_minutes: <td> parameter in table containing minutes with different CSS style (thicker bottom line)

    :return: list of bus stop times, in simplified format: hour+minute is represented by number of minutes from midnight
             eg. 12:00 is 12 * 60 + 0 = 720, 15:37 is 15 * 60 + 37 = 937
    """
    next_day_flag = False
    timetable = {}

    for i, hour in enumerate(hours_list):

        hour = int(hour.text.strip())
        minutes = minutes_list[i * type_of_bus + day].text.strip()

        if hour == 22 and thick_hour:
            timetable[hour] = minutes
            timetable[thick_hour] = thick_minutes[day].text.strip()
            next_day_flag = True
        else:
            if not next_day_flag:
                timetable[hour] = minutes
            else:
                timetable[hour + 24] = minutes

    return timetable_dict_to_list(timetable)


def generate_timetable(hours_list, minutes_list, thick_hour=None, thick_minutes=None):
    """
        :type hours_list: list
        :param hours_list: list of <td> parameters in table containing hours

        :type minutes_list: list
        :param minutes_list: list of <td> parameters in table containing minutes

        :type: thick_hour: int
        :param thick_hour: <td> parameter in table containing hour with different CSS style (thicker bottom line)

        :type thick_minutes: list
        :param thick_minutes: <td> parameter in table containing minutes with different CSS style (thicker bottom line)

        :return: list of bus stop times for each day bus functions
        """

    # type_of_bus: tells if bus drives only on weekdays or on weekdays + saturdays or whole week
    # based on number of cols in html table - len of minutes_list and len of hours_list
    type_of_bus = int(len(minutes_list) / len(hours_list))
    times = []

    for i in range(type_of_bus):
        times.append(get_timetable_http_table(hours_list, minutes_list, type_of_bus, i, thick_hour, thick_minutes))

    return times


def download_timetables(a, stop, date, stops_times_dict=None):
    """
    :type a: str
    :param a: <a> param of previous bus stop

    :type stop: str
    :param stop: current bus stop

    :type stops_times_dict: dict
    :param stops_times_dict: dictionary containing line data

    :return: dict
    """

    if not stops_times_dict:
        stops_times_dict = {}

    link = a['href']
    response = requests.get("http://rozklady.mpk.krakow.pl{}".format(link), headers=headers)
    soup = BeautifulSoup(response.text, parser)
    next_link = a.find_next('a', href=re.compile("lang=PL&rozklad={}&linia=".format(date)))

    if next_link is None:
        last_stop = a.find_next('td', style=re.compile("text-align: right;"))
        last_stop_name = last_stop.text.strip()
        if last_stop_name in stops_times_dict.keys():
            last_stop_name = last_stop_name + " 2"
        stops_times_dict[last_stop_name] = []
        return stops_times_dict

    next_stop = next_link.find('span').contents[0].strip()

    hour_thick_style = "border-right: dotted black 1px; font-weight: bold; white-space: nowrap;  border-bottom: solid" \
                       " black 2px; padding-right: 10px;"
    hour_thin_style = "border-right: dotted black 1px; font-weight: bold; white-space: nowrap;  border-bottom: solid " \
                      "black 1px; padding-right: 10px;"
    minute_thin_style = "border-right: solid black 1px;  text-align: left; white-space: nowrap;  border-bottom: solid" \
                        " black 1px; padding-right: 10px;"
    minute_thick_style = "border-right: solid black 1px;  text-align: left; white-space: nowrap;  border-bottom: " \
                         "solid black 2px; padding-right: 10px;"

    tmp_hours = soup.find_all('td', attrs={'style': re.compile(hour_thin_style)})
    tmp_minutes = soup.find_all('td', attrs={'style': re.compile(minute_thin_style)})
    thick_hour_in_timetable = soup.find_all('td', attrs={'style': re.compile(hour_thick_style)})
    thick_minutes_in_timetable = soup.find_all('td', attrs={'style': re.compile(minute_thick_style)})

    if thick_hour_in_timetable:
        thick_hour = int(thick_hour_in_timetable[0].text.strip())
        hours = generate_timetable(tmp_hours, tmp_minutes, thick_hour, thick_minutes_in_timetable)
    else:
        hours = generate_timetable(tmp_hours, tmp_minutes)

    if stop in stops_times_dict.keys():
        stop = stop + " 2"

    stops_times_dict[stop] = hours

    return download_timetables(next_link, next_stop, date, stops_times_dict)


def progress_bar(current_line, total):

    percent = ("{0:.1f}").format(100 * (current_line / float(total)))
    filled_length = int(100 * current_line // total)
    bar = "$" * filled_length + '-' * (100 - filled_length)

    print(f'\r Progress: |{bar}| {percent} % Complete', end='\r')

    if current_line == total:
        print()


def main():

    response = requests.get("http://rozklady.mpk.krakow.pl", headers=headers)
    soup = BeautifulSoup(response.text, parser)

    lines = soup.find_all('a', attrs={'class': ["linia", "liniaZ", "liniaO", "liniaN"]})
    current_date = lines[0]["href"].split('&')[1].split('=')[1]

    progress_bar(0, len(lines))

    main_link = "http://rozklady.mpk.krakow.pl/?lang=PL&rozklad={}&linia=".format(current_date)
    timetable = {}

    for i, line in enumerate(lines):

        line = line.text.strip()
        # Get each bus line web-page
        response = requests.get(main_link + "{}".format(line), headers=headers)
        soup = BeautifulSoup(response.text, parser)
        number_of_bus_routes = len(soup.find_all('table', attrs={'style': ' vertical-align: top; '})[0].find_all('a'))

        for route in range(1, number_of_bus_routes + 1):

            # For each bus route get it's web-page
            response = requests.get(main_link + "{}__{}".format(line, route), headers=headers)
            soup = BeautifulSoup(response.text, parser)

            # Get first bus stop
            first_link = soup.find('a', href=re.compile(re.escape(r"/?lang=PL&rozklad={}&linia={}__{}".format(current_date, line, route))))
            first_stop = first_link.find('span').contents[0].strip()

            # Get next stops recursively
            timetable["{}_{}".format(line, route)] = download_timetables(first_link, first_stop, current_date)

        progress_bar(i, len(lines))

    with open("lines_stops_times_dict", "a") as file:
        file.write(json.dumps(timetable))


# Get current bus lines in Kraków
if __name__ == "__main__":
    main()