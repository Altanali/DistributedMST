from boruvka import boruvka
from multithreaded_boruvka import boruvka as borvuka_multi
from bucketed_boruvka import boruvka as boruvka_bucket
import networkx as nx
import time
from graph_helpers import random_connected_graph, graph_to_obj
from create_graph_files import graph_to_amir_file
import copy
from GHS import GHS
import sys
sys.path.insert(1, './amir/GHS-MST/')
from Main import run_GHS
import math

num_nodes = 350
max_edges = math.comb(num_nodes, 2)
num_edges = max_edges // 5

print(num_edges)

num_iter = 5

borvuka_time = 0
multi_boruvka_time = 0
nx_prim_time = 0
nx_boruvka_time = 0
ghs_time = 0
bucket_boruvka_time = 0
for i in range(num_iter):
	random_graph = random_connected_graph(num_nodes, m=num_edges)
	graph_obj = graph_to_obj(random_graph)
	graph_to_amir_file(random_graph, "temp.dat")

	graph_copy = copy.deepcopy(graph_obj)
	start = time.time()
	boruvka(graph_copy)
	end = time.time()
	print("\tBoruvka Time: ", end - start)
	borvuka_time += end - start

	# graph_copy = copy.deepcopy(graph_obj)
	# start = time.time()
	# borvuka_multi(graph_copy)
	# end = time.time()
	# print("\tMultithreaded Boruvka Time: ", end - start)
	# multi_boruvka_time += end - start

	graph_copy = copy.deepcopy(graph_obj)
	start = time.time()
	boruvka_bucket(graph_copy)
	end = time.time()

	bucket_boruvka_time += end - start
	print("\t Bucketed Boruvka Time: ", end - start)


	start = time.time()
	nx.minimum_spanning_tree(random_graph, algorithm="prim")
	end = time.time()
	print("\tNX Prim Time: ", end - start)
	nx_prim_time += end - start

	start = time.time()
	nx.minimum_spanning_tree(random_graph, algorithm="boruvka")
	end = time.time()
	print("\tNX Boruvka Time: ", end - start)
	nx_boruvka_time += end - start

	ghs_time += run_GHS("temp.dat")



print("Bucketed Boruvka Time: ", bucket_boruvka_time/num_iter)
print("Boruvka Time: ", borvuka_time/num_iter)
print("Multi Boruvka Time: ", multi_boruvka_time/num_iter)
print("NX Prim Time: ", nx_prim_time/num_iter)
print("NX Boruvka Time: ", nx_boruvka_time/num_iter)
print("GHS Time: ", ghs_time/num_iter)

