from pathlib import Path
import graph_helpers
import sys
import json
from collections import defaultdict

def graph_to_amir_file(graph, filename):
	with open(filename, "w+") as f:
		for u, v in graph.edges:
			f.write(str(u) + " " + str(v) + " " + str(graph[u][v]["weight"]) +" 0\n")

def graph_to_std_file(graph, filename):
	obj = defaultdict(list)
	for u, v in graph.edges:
		weight = graph[u][v]["weight"]
		obj[str(u)].append({
			"neighbor": v,
			"weight": weight
		})
		obj[str(v)].append({
			"neighbor": u,
			"weight": weight
		})
	with open(filename, "w+") as f:
		f.write(json.dumps(obj))

if __name__ == "__main__":
	folder_root = Path("graphs")
	folder_name = folder_root.joinpath(Path(sys.argv[2] if len(sys.argv) > 2 else "temp"))
	folder_name.mkdir(parents=True, exist_ok=True)
	num_nodes = int(sys.argv[1])

	graph = graph_helpers.random_connected_graph(num_nodes)
	amir_out = folder_name.joinpath("graph_amir.txt")
	graph_out = folder_name.joinpath("graph.json")
	graph_to_amir_file(graph, amir_out)
	graph_to_std_file(graph, graph_out)

	mst = graph_helpers.compute_mst(graph, out_file=folder_name.joinpath("mst.png"))
	graph_helpers.draw_graph(graph, out_file=folder_name.joinpath("graph.png"))