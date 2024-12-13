import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
from typing import Union
import random
from pathlib import Path

def graph_to_obj(graph: nx.Graph):
	"""
	Turns an input graph into an object with the structure: 
	{
		"1": {
			"name": 1
			"neighbors": [
				{
					"id": 2,
					"weight": 4
				},
				{
					"id": 3, 
					"weight": 5
				}
			]
		},
		"2": {
			"neighbors": [
				{
					"id": 1, 
					"weight": 4
				}
			]
		}
		"3": {
			"neighbors": [
				{
					"id": 1, 
					"weight": 5
				}
			]
		}
	}
	"""
	obj = defaultdict(dict)
	for u, v in graph.edges:
		weight = graph[u][v]["weight"]
		neighbors_u = obj[str(u)].get("neighbors") or []
		neighbors_u.append({
			"id": v,
			"weight": weight
		})
		obj[str(u)]["neighbors"] = neighbors_u

		neighbors_v = obj[str(v)].get("neighbors") or []
		neighbors_v.append({
			"id": u,
			"weight": weight
		})
		obj[str(v)]["neighbors"] = neighbors_v
	return obj


def compute_mst(graph: nx.Graph, algo: str="prim") -> nx.Graph:
	"""
	Returns the MST of the input graph.
		args:
			graph (nx.Graph): Graph to compute the MST of
			algo (str): Can be "prim", "kruskal", or "boruvka"
	"""
	mst = nx.minimum_spanning_tree(graph, algorithm=algo)
	return mst


def draw_graph(graph: nx.Graph, out_file: str="graph.png") -> None:
	"""
	Draws the input graph and saves the resulting image in out_file.
	"""
	plt.clf()
	pos=nx.spring_layout(graph)
	nx.draw(graph, pos, with_labels=True)
	labels = {e: graph.edges[e]["weight"] for e in graph.edges}
	nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
	nx.draw_networkx_nodes(graph, pos)
	plt.savefig(out_file, format="png")


def random_connected_graph(num_nodes: int, p_edge: float = 0.5, m = None) -> nx.Graph:
	"""
	Creates a random graph with num_nodes vertices where each edge has probability 0.5 of being included. 
	"""
	#Create Random Connected Graph
	graph: nx.Graph
	while True:
		if m is None:
			graph = nx.erdos_renyi_graph(num_nodes, p_edge)
		else: 
			graph = nx.ra
		if nx.is_connected(graph):
			break
		#Add Unique Weights to graph
	num_edges = graph.size()
	min_weight = 1
	max_weight = 3*graph.size()
	weights = random.sample(range(min_weight, max_weight), num_edges)
	for (u, v), weight in zip(graph.edges, weights):
		graph[u][v]["weight"] = weight
	return graph