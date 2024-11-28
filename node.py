import json
from enum import Enum, IntEnum
import sys
import os
from dataclasses import dataclass
from typing import Dict
import socket
import threading
import select
import queue

@dataclass
class Edge:
	class EdgeState(IntEnum):
		BASIC = 0
		BRANCH = 1
		REJECTED = 2

	u: int
	v: int
	in_socket: socket.socket = None
	out_socket: socket.socket = None
	address: int = -1
	weight: int = 0
	directed: bool = False
	state: EdgeState = EdgeState.BASIC



class Node:
	NETWORK_HOST = "127.0.0.1"
	BUFFER_LENGTH = 4*32

	class NodeState(IntEnum):
		SLEEPING = 0
		FIND = 1
		FOUND = 2

	class Operation(IntEnum):
		NOOP = 0
		CONNECT = 1
		INITIATE = 2
		TEST = 3
		ACCEPT = 4
		REJECT = 5
		REPORT = 6
		CHANGE_ROOT = 7

	def __init__(self, id: int, data_filename: str):
		self.id = id
		self.port = None
		self.sock = None
		self.status = self.NodeState.SLEEPING
		self.level = 0
		self.fragment_number = 0
		self.best_edge = None
		self.best_weight = None
		self.test_edge = None
		self.in_branch = None
		self.find_count = 0
		self.out_edges: Dict[int, Edge]  = dict()
		self._is_init_node = False
		self.message_queue = queue.SimpleQueue()
		self._init_network_from_json(filename=data_filename)



	def _init_network_from_json(self, filename):
		f = open(filename, "r")
		network_data = json.loads(f.read())
		node_data = network_data["nodeData"]
		my_data = node_data[str(self.id)]
		self.port = my_data["server_address"]
		self._init_node_port()

		coordinator_data = network_data["coordinatorData"]
		coordinator_port = coordinator_data["server_address"]
		self._init_coordination_sock(coordinator_port)


		neighbors= my_data["neighbors"]
		for neighbor in neighbors:
			neighbor_id = neighbor["id"]
			neighbor_weight = neighbor["weight"]
			self.out_edges[neighbor_id] = Edge(
				u=self.id, v=neighbor_id, weight=neighbor_weight, address=node_data[str(neighbor_id)]["server_address"]
			)
		
		# print(f"{self.id} is beginning to connect/accept connections to/from neighbors.")
		acceptor_thread = threading.Thread(target=self.accept_neighbor_connections)
		connector_thread = threading.Thread(target=self.connect_to_neighbors)
		acceptor_thread.start()
		connector_thread.start()
		acceptor_thread.join()
		acceptor_thread.join()
		
		self.message_queue_thread = threading.Thread(target=self._message_queue_daemon)
		self.message_queue_thread.start()

		# print(self.id, " has succesfully connected and accepted conenctions to/from all neighbors.")

	def connect_to_neighbors(self):
		for neigbor_id in self.out_edges.keys():
			try:
				edge = self.out_edges[neigbor_id]
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((Node.NETWORK_HOST, edge.address))
				sock.send(bytes(str(self.id), "utf8"))
				edge.out_socket = sock
			except Exception as errno:
				print("Connection to neighbors failed: ", errno)
				sys.exit(-1)


	def accept_neighbor_connections(self):
		num_neighbors = len(self.out_edges)
		self.sockets_to_neighbors: Dict[socket.socket, int] = dict()
		while num_neighbors > 0:
			neighbor_sock = self.sock.accept()[0]
			data = neighbor_sock.recv(Node.BUFFER_LENGTH).decode()
			neighbor_id = int(data)
			self.out_edges[neighbor_id].in_socket = neighbor_sock
			self.sockets_to_neighbors[neighbor_sock] = neighbor_id
			num_neighbors -= 1

	def _init_node_port(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(('', self.port))
		self.sock.listen(1)

	def _init_coordination_sock(self, port: int):
		self.coordination_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.coordination_sock.connect((Node.NETWORK_HOST, port))
		data = int(self.coordination_sock.recv(Node.BUFFER_LENGTH).decode())
		if data == 2:
			self._is_init_node = True
			print(f"{self.id} will kickoff the algorithm.")
		elif data != 1:
			print("Coordinator terminated program execution.")
			sys.exit(-1)

	def execute_GHS(self):
		if self._is_init_node:
			self.wakeup()
		self.sleep()

	
	
	def send_message_to_neighbor(self, neighbor: int, message: object, operation: int = 0):
		print(f"{self.id} is sending message {self.Operation(operation).name} to {neighbor} with message {str(message)}")
		message_data = {
			"id": self.id,
			"operation": operation ,
			"message": message
		}
		message_string = json.dumps(message_data)
		edge = self.out_edges[neighbor]
		out_socket = edge.out_socket
		out_socket.send(bytes(message_string, "utf8"))

	def sleep(self):
		while True:
			obj: json = self.message_queue.get() #blocks until obj is available
			print(f"{self.id} received a", self.Operation(obj["operation"]).name, "message from", {obj["id"]})

			operation = obj["operation"]
			if operation == self.Operation.CONNECT:
				self._process_connect(obj)
			elif operation == self.Operation.INITIATE:
				self._process_initiate(obj)
			elif operation == self.Operation.TEST:
				self._process_test(obj)
			elif operation == self.Operation.ACCEPT:
				self._process_accept(obj)
			elif operation == self.Operation.REJECT:
				self._process_reject(obj)
			elif operation == self.Operation.REPORT:
				self._process_report(obj)
			elif operation == self.Operation.CHANGE_ROOT:
				self._change_root()


	def wakeup(self):
		self.status = self.NodeState.FOUND
		#Find minimum weight edge:
		min_edge_neighbor = min(self.out_edges.keys(), key = lambda v: self.out_edges[v].weight)
		min_edge = self.out_edges[min_edge_neighbor]
		min_edge.state = Edge.EdgeState.BRANCH
		print(f"Minimum weight edge from {self.id} is {min_edge.v} with weight {min_edge.weight}.")
		self._send_connect(min_edge_neighbor, self.level)

	def _process_connect(self, obj: json):
		if self.status == self.NodeState.SLEEPING:
			self.wakeup()
		message = obj["message"]
		level = message["level"]
		other_id = obj["id"]
		edge = self.out_edges[other_id]
		if level < self.level:
			edge.state = Edge.EdgeState.BRANCH
			self._send_initiate(other_id, self.level, self.fragment_number, self.status)
			if self.status == self.NodeState.FIND:
				self.find_count += 1
		elif edge.state == Edge.EdgeState.BASIC:
			self.message_queue.put(obj)
		else:
			self._send_initiate(other_id, self.level + 1, edge.weight, self.NodeState.FIND)

	def _process_initiate(self, obj: json):
		message = obj["message"]
		self.level = message["level"]
		self.fragment_number = message["fragmentNumber"]
		self.status = self.NodeState(message["status"])
		other_id = obj["id"]
		edge = self.out_edges[other_id]
		self.in_branch = edge
		self.best_edge = None
		self.best_weight = -1
		for neighbor, edge in self.out_edges.items():
			if neighbor == other_id or edge.state != Edge.EdgeState.BRANCH:
				continue
			self._send_initiate(neighbor, self.level, self.fragment_number, self.status)
			if self.status == self.NodeState.FIND:
				self.find_count += 1

		if self.status == self.NodeState.FIND:
			self._test()
	
	def _process_test(self, obj: json):
		if self.status == self.NodeState.SLEEPING:
			self.wakeup()
		message = obj["message"]
		level = message["level"]
		other_id = obj["id"]
		fragment_number = message["fragmentNumber"]
		if level > self.level:
			self.message_queue.put(obj)
			return
		
		if fragment_number != self.fragment_number:
			self._send_accept(other_id)
		else:
			edge = self.out_edges[other_id]
			if edge.state == Edge.EdgeState.BASIC:
				edge.state = Edge.EdgeState.REJECTED
			if self.test_edge != edge:
				self._send_reject(other_id)
			else:
				self._test()

	def _process_accept(self, obj):
		self.test_edge = None
		other_id = obj["id"]
		edge = self.out_edges[other_id]
		if ((not self.best_edge) or edge.weight < self.best_weight):
			self.best_edge = edge
			self.best_weight = edge.weight
		self._report()

	def _process_reject(self, obj):
		other_id = obj["id"]
		edge = self.out_edges[other_id]
		if edge.state == Edge.EdgeState.BASIC:
			edge.state = Edge.EdgeState.REJECTED
		self._test()


	def _process_report(self, obj):
		other_id = obj["id"]
		edge = self.out_edges[other_id]
		message = obj["message"]
		weight = message["bestWeight"]
		if edge != self.in_branch:
			self.find_count -= 1
			if weight < self.best_weight:
				self.best_edge = edge
				self.best_weight = weight
			self._report()

		elif self.status == self.NodeState.FIND:
			self.message_queue.put(obj)
		elif weight > self.best_weight:
			self._change_root()
		elif weight == self.best_weight == -1:
				print("HALTING")
				exit(-1) #TODO: figure this out


	def _change_root(self):
		if self.best_edge.state == Edge.EdgeState.BRANCH:
			self._send_change_root(self.best_edge.v)
		else:
			self._send_connect(self.best_edge.v, self.level)
			self.best_edge.state = Edge.EdgeState.BRANCH


	def _test(self):
		print(f"{self.id} is calling test().")
		minimum_basic_edge = None
		min_key = None
		for key, edge in self.out_edges.items():
			if edge.state == Edge.EdgeState.BASIC:
				if minimum_basic_edge:
					min_key, minimum_basic_edge = (min_key, minimum_basic_edge) \
						if minimum_basic_edge.weight < edge.weight \
						else (key, edge)
				else:
					min_key, minimum_basic_edge = key, edge

		if minimum_basic_edge:
			self.test_edge = minimum_basic_edge
			self._send_test(min_key, self.level, self.fragment_number)
		else:
			self.test_edge = None
			self._report()


	def _report(self):
		if self.find_count == 0 and self.test_edge is None:
			self.status = self.NodeState.FOUND
			self._send_report(self.in_branch.v, self.best_weight)


	def _send_report(self, neighbor: int, best_weight: int):
		message = {
			"bestWeight": best_weight
		}
		self.send_message_to_neighbor(neighbor, message, self.Operation.REPORT)
	
	def _send_test(self, neighbor: int, level: int, fragment_number):
		message = {
			"level": level,
			"fragmentNumber": fragment_number
		}
		self.send_message_to_neighbor(neighbor, message, self.Operation.TEST)
	
	def _send_initiate(self, neighbor: int, level: int, fragment_number: int, status: int):
		message = {
			"level": level, 
			"fragmentNumber": fragment_number, 
			"status": status
		}
		self.send_message_to_neighbor(neighbor, message, self.Operation.INITIATE)

	def _send_connect(self, neighbor: int, level: int):
		message = {
			"level": level
		}
		self.send_message_to_neighbor(neighbor, message, self.Operation.CONNECT)
	
	def _send_accept(self, neighbor: int):
		self.send_message_to_neighbor(neighbor=neighbor, message={}, operation=self.Operation.ACCEPT)

	def _send_reject(self, neighbor: int):
		self.send_message_to_neighbor(neighbor=neighbor, message={}, operation=self.Operation.REJECT)

	def _send_change_root(self, neighbor: int):
		self.send_message_to_neighbor(neighbor=neighbor, message={}, operation=self.Operation.CHANGE_ROOT)

	

	def _message_queue_daemon(self):
		while True:
			readlist = self.sockets_to_neighbors.keys()
			readable, _, _ = select.select(readlist, [], [])
			for sock in readable:
				data = sock.recv(Node.BUFFER_LENGTH).decode().strip()
				if data == "":
					continue
				try:
					obj = json.loads(data)
					self.message_queue.put(obj)
				except:
					continue
	



if __name__ == "__main__":
	id = int(sys.argv[1])
	filename = sys.argv[2]
	node = Node(id, filename)
	node.execute_GHS()