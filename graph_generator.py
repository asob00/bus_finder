import json
import scrape_data

try:
    with open('lines_stops_times_dict', 'r') as timetable_dict:
        json_timetable = timetable_dict.read()
        timetable = json.loads(json_timetable)
except FileNotFoundError:
    scrape_data.main()
    with open('lines_stops_times_dict', 'r') as timetable_dict:
        json_timetable = timetable_dict.read()
        timetable = json.loads(json_timetable)


def generate_graph(timetable: dict) -> dict:
    """Generates connections graph, using timetable downloaded with scrape_data.py

    Parameters
    ----------
    :type timetable : dict, required
        Dictionary containing, data about each bus, stop and bus timetables in Krakow

    Returns:
    --------
    :return graph : dict
        Dictionary reflecting bus connections (routes)
    """

    graph = {}
    for line, stops_times_dict in timetable.items():
        for idx, stop in enumerate(list(stops_times_dict.keys())[:-1], start=1):

            next_stop = list(stops_times_dict.keys())[idx]

            if stop not in graph.keys():
                graph[stop] = {next_stop: [line]}

            else:
                currently_in_graph = graph[stop]

                if next_stop in currently_in_graph.keys():
                    currently_in_graph[next_stop].append(line)
                    graph[stop] = currently_in_graph

                else:
                    graph[stop][next_stop] = [line]
    return graph


with open("graph", 'w') as graph_file:
    graph_file.write(json.dumps(generate_graph(timetable)))
