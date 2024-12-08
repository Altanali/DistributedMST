import networkx as nx
import argparse
import random
import socket
import json
import os
import sys
from node import Node
import threading
from collections import defaultdict
import matplotlib.pyplot as plt
from graph_helpers import graph_to_obj, compute_mst, draw_graph, random_connected_graph

def get_args(): 
	parser = argparse.ArgumentParser()
	parser.add_argument("--num_nodes", type=int, default=2)
	args = parser.parse_args()
	return args


def dump_json_to_datafile(obj, filename):
	with open(filename, "w+") as f:
		f.write(json.dumps(obj))


def listen_for_dead_children(num_children: int = -1):
	while(True):
		try:
			pid, status = os.wait()
			exit_code = os.waitstatus_to_exitcode(status)
			if exit_code == 255:
				print("Child died badly")
				sys.exit(-1)
			elif exit_code == 0: 
				send_halt()

			num_children -= 1
			if num_children == 0:
				return
		except ChildProcessError as e:
			return


def send_halt():
	global children_socks
	message = {
			"id": -1, 
			"operation": Node.Operation.HALT,
			"message": {}
	}
	message_string = json.dumps(message)
	sock: socket.socket
	for sock in children_socks:
		try:
			sock.send(message_string.encode())
		except:
			pass


children_socks = []
if __name__ == "__main__":
	args = get_args()
	num_nodes = args.num_nodes
	p_edge = 0.5

	graph = random_connected_graph(num_nodes)


	graph_obj = graph_to_obj(graph)

	draw_graph(graph)
	compute_mst(graph, algo="prim")
	#Setup Network
	address_base = 8080
	coordinator_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	coordinator_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	while(True):
		try:
			coordinator_sock.bind(('', address_base))
			break
		except OSError as e:
			if e.errno == 98:
				address_base += 1
	coordinator_sock.listen(1)

	network_data_json = {}
	network_data_json["coordinatorData"] = {"server_address": address_base}

	#Designate Ports for each Node
	for i in range(num_nodes):
		graph_obj[str(i)]["server_address"] = address_base + i + 1
	
	network_data_json["nodeData"] = graph_obj
	dump_json_to_datafile(network_data_json, 'temp.json')
	child_pids = []
	for i in range(num_nodes):
		pid = os.fork()
		if pid == -1:
			exit(-1)
		if pid == 0:
			program_name = "python3"
			program_args = [
				program_name, "node.py", str(i), "temp.json"
			]
			os.execvp(
				program_name, program_args
			)
		else:
			child_pids.append(pid)
	
	nanny_thread = threading.Thread(target=listen_for_dead_children)
	nanny_thread.start()

	while len(children_socks) < num_nodes:
		sock, port = coordinator_sock.accept()
		children_socks.append(sock)
	
	for i in range(num_nodes):
		sock: socket.socket = children_socks[i]
		if i == 0:
			sock.send("2".encode())
		else:
			sock.send("1".encode())
	
	status = 0

	nanny_thread.join()
	coordinator_sock.close()