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
unicode = "utf=8"
parser = 'html.parser'


def timetable_dict_to_list(timetable):
    times = []
    for i in timetable.keys():
        for j in timetable[i].split(' '):
            if j != '':
                times.append(i * 60 + int(j[0:2]))
    return times


def timetable_normal(tmp_hours, tmp_minutes, type_of_bus, thick_hour=None, thick_minutes=None):
    timetable = {}
    if thick_hour is not None:
        flag = False
        for i in range(len(tmp_hours)):
            hour = int(tmp_hours[i].text.strip())
            minutes = tmp_minutes[i * type_of_bus].text.strip()

            if hour == 22:
                timetable[hour] = minutes
                timetable[thick_hour] = thick_minutes[0].text.strip()
                flag = True
            else:
                if not flag:
                    timetable[hour] = minutes
                else:
                    timetable[hour + 24] = minutes
    else:
        for i in range(len(tmp_hours)):
            hour = int(tmp_hours[i].text.strip())
            minutes = tmp_minutes[i * type_of_bus].text.strip()
            timetable[hour] = minutes
    return timetable_dict_to_list(timetable)


def timetable_saturday(tmp_hours, tmp_minutes, type_of_bus, thick_hour=None, thick_minutes=None):
    timetable = timetable_normal(tmp_hours, tmp_minutes, type_of_bus, thick_hour, thick_minutes)
    timetable_sat = {}
    if thick_hour is not None:
        flag = False
        for i in range(len(tmp_hours)):
            hour = int(tmp_hours[i].text.strip())
            minutes = tmp_minutes[i * type_of_bus + 1].text.strip()

            if hour == 22:
                timetable_sat[hour] = minutes
                timetable_sat[thick_hour] = thick_minutes[1].text.strip()
                flag = True
            else:
                if not flag:
                    timetable_sat[hour] = minutes
                else:
                    timetable_sat[hour + 24] = minutes
    else:
        for i in range(len(tmp_hours)):
            hour = int(tmp_hours[i].text.strip())
            minutes = tmp_minutes[i * type_of_bus + 1].text.strip()
            timetable_sat[hour] = minutes
    return timetable, timetable_dict_to_list(timetable_sat)


def timetable_sunday(tmp_hours, tmp_minutes, type_of_bus, thick_hour=None, thick_minutes=None):
    timetable, timetable_sat = timetable_saturday(tmp_hours, tmp_minutes, type_of_bus, thick_hour, thick_minutes)
    timetable_sun = {}
    if thick_hour is not None:
        flag = False
        for i in range(len(tmp_hours)):
            hour = int(tmp_hours[i].text.strip())
            minutes = tmp_minutes[i * type_of_bus + 2].text.strip()

            if hour == 22:
                timetable_sun[hour] = minutes
                timetable_sun[thick_hour] = thick_minutes[2].text.strip()
                flag = True
            else:
                if not flag:
                    timetable_sun[hour] = minutes
                else:
                    timetable_sun[hour + 24] = minutes
    else:
        for i in range(len(tmp_hours)):
            hour = int(tmp_hours[i].text.strip())
            minutes = tmp_minutes[i * type_of_bus + 2].text.strip()
            timetable_sun[hour] = minutes
    return timetable, timetable_sat, timetable_dict_to_list(timetable_sun)


def generate_timetable(tmp_hours, tmp_minutes, thick_hour=None, thick_minutes=None):
    type_of_bus = int(len(tmp_minutes) / len(tmp_hours))

    if type_of_bus == 1:
        return timetable_normal(tmp_hours, tmp_minutes, type_of_bus, thick_hour, thick_minutes)
    elif type_of_bus == 2:
        return timetable_saturday(tmp_hours, tmp_minutes, type_of_bus, thick_hour, thick_minutes)
    elif type_of_bus == 3:
        return timetable_sunday(tmp_hours, tmp_minutes, type_of_bus, thick_hour, thick_minutes)


def download_timetables(a, stop, stops_times_dict=None):
    """
    :param a: <a> param of previous bus stop
    :type a: str
    :param stop: current bus stop
    :type stop: str
    :param stops_times_dict: dictionary containing line data
    :type stops_times_dict: dict
    :return: dict
    """

    if stops_times_dict is None:
        stops_times_dict = {}

    link = a['href']
    response = requests.get("http://rozklady.mpk.krakow.pl{}".format(link), headers=headers)
    soup = BeautifulSoup(response.text, parser)
    next_link = a.find_next('a', href=re.compile("lang=PL&rozklad=20200823&linia="))

    if next_link is None:
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
    stops_times_dict[stop] = list(hours)

    return download_timetables(next_link, next_stop, stops_times_dict)


# Get current bus lines in Kraków
# response = requests.get("http://rozklady.mpk.krakow.pl", headers=headers)
# soup = BeautifulSoup(response.text, parser)
# lines = soup.find_all('a', attrs={'class': ["linia", "liniaZ", "liniaO", "liniaN"]})
lines = [213]
main_link = "http://rozklady.mpk.krakow.pl/?lang=PL&rozklad=20200823&linia="
for i in lines:

    # Get each bus line web-page
    response = requests.get(main_link + "{}".format(i), headers=headers)
    soup = BeautifulSoup(response.text, parser)
    number_of_bus_routes = len(soup.find_all('table', attrs={'style': ' vertical-align: top; '})[0].find_all('a'))
    for j in range(1, number_of_bus_routes + 1):
        # For each bus route get it's web-page
        response = requests.get(main_link + "{}__{}".format(i, j), headers=headers)
        soup = BeautifulSoup(response.text, parser)

        # Get first bus stop
        first_link = soup.find('a', href=re.compile(re.escape(r"/?lang=PL&rozklad=20200823&linia={}__{}".format(i, j))))
        first_stop = first_link.find('span').contents[0].strip()

        # Get next stops recursively
        print(download_timetables(first_link, first_stop))
