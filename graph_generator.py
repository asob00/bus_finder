import json

with open('lines_stops_times_dict', 'r') as timetable_dict:
    json_timetable = timetable_dict.read()
    timetable = json.loads(json_timetable)


def generate_graph(timetable: dict) -> dict:
    """Generates connections graph, using timetable downloaded with scrape_data.py

    Parameters
    ----------
    timetable : dict, required
        Dictionary containing, data about each bus, stop and bus timetables in Kraków

    Returns:
    --------
    graph : dict
        Dictionary reflecting bus connections (routes)
    """


    graph = {}
    for line, stops_times_dict in timetable.items():
        for idx, stop in enumerate(stops_times_dict.keys(), start=1):

            stops_times_dict_len = len(stops_times_dict.keys())
            if idx < stops_times_dict_len:
                next_stop = list(stops_times_dict.keys())[idx]

            if stop not in graph.keys() and idx < stops_times_dict_len:
                graph[stop] = {next_stop: [line]}

            elif idx < stops_times_dict_len:
                curently_in_graph = graph[stop]

                if next_stop in curently_in_graph.keys():
                    curently_in_graph[next_stop].append(line)
                    graph[stop] = curently_in_graph

                else:
                    graph[stop][next_stop] = [line]
    return graph


with open("graph", 'w') as graph_file:
    graph_file.write(json.dumps(generate_graph(timetable)))