#include <iostream>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h> 
#include <unistd.h>
#include <cstring>
#include <vector>
#include <sys/types.h>
#include <sys/wait.h>
#include <unordered_map>
#include <arpa/inet.h>
#include <fstream>
#include "json.hpp"
#include <argparse/argparse.hpp>
#include "setup_helpers.hpp"

using namespace std;
using json =  nlohmann::json;

void setup_basic_graph_datafile(int, unordered_map<int, vector<int>> &, vector<int> &, vector<struct sockaddr_in>, string);

void setup_argument_parser(argparse::ArgumentParser &program, int argc, char *argv[]) {
	program.add_argument("--num_nodes").help("Number of nodes in graph instance.").scan<'i', int>();
	try {
		program.parse_args(argc, argv);
	} 
	catch (const std::exception &err) {
		cerr << err.what() << endl;
		exit(1);
	}
}

int main(int argc, char *argv[]) {
	argparse::ArgumentParser program("distributed_mst");
	setup_argument_parser(program, argc, argv);
	
	int num_nodes = program.get<int>("--num_nodes");
	unordered_map<int, vector<int>> graph = {
		{0, {1, 2}}, 
		{1, {0}},
		{2, {0}}
	};
	vector<int> server_fds(num_nodes);
	vector<int> node_fds(num_nodes);
	vector<int> server_addreses(num_nodes);
	vector<pid_t> node_pids(num_nodes);
	string node_executable = "./node";
	string temp_data_filename = "temp.json";



	//Setup Netework
	int address_base = 8080;
	int coordinator_fd = socket(AF_INET, SOCK_STREAM, 0);
	if(coordinator_fd == -1) raise_error("Coordinator failed to create socket.");

	//Allows us to reuse same socket between program instances.
	int optval = 1;
	if((setsockopt(coordinator_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &optval, sizeof(optval)) < 0)) {
			raise_error("setsockopt", "Coordinator failed to set socket options.");
	}
	
	struct sockaddr_in coordinator_address = {AF_INET, htons(address_base), INADDR_ANY};
	if(bind(coordinator_fd, (struct sockaddr *)&coordinator_address, sizeof(coordinator_address)) == -1) {
		fprintf(stderr, "bind: %s\n", strerror(errno));
		raise_error("Coordinator failed to bind to socket.");
	}
	listen(coordinator_fd, num_nodes);


	json network_data_json;
	network_data_json["coordinatorData"] = {
		{"server_fd", coordinator_fd}, {"server_address", address_base}
	};


	
	json node_data_jsons;
	for(int i = 0; i < num_nodes; ++i) {
		//Create Process and exec(node.exe)
		json node_data;
		server_fds[i] = socket(AF_INET, SOCK_STREAM, 0);
		server_addreses[i] = htons(address_base + 1 + i); 

		node_data["neighbors"] = graph[i];
		node_data["server_fd"] = server_fds[i];
		node_data["server_address"] = address_base + i + 1;

		node_data_jsons[to_string(i)] = node_data;
	}
	network_data_json["nodeData"] = node_data_jsons;
	dump_json_to_datafile(network_data_json, temp_data_filename);


	for(int node_i = 0; node_i < num_nodes; ++node_i) {
		pid_t pid = fork();
		if(pid == -1) {
			cout << "Failed to fork process" << endl;
			exit(-1);
		}
		if(pid == 0) {
			//Exec Node
			char *args[] = {
				(char *)node_executable.c_str(), (char *)(to_string(node_i).c_str()), (char *)temp_data_filename.c_str(), nullptr
			};
			if(execvp(args[0], args) == -1) {
				perror("excecvp failed");
			}
		}
		else {
			node_pids[node_i] = pid;
		}
	}

	// Wait till all nodes have reached out.
	int num_connections = 0;
	while(num_connections < num_nodes) {
		int fd = accept(coordinator_fd, NULL, 0);
		if(fd < 0)
			raise_error("accept", "Coordinator failed to accept a node's connection.");
		node_fds[num_connections] = fd;
		++num_connections;
	}

	//Send children the go-ahead to begin
	char message[] = "hello world";
	size_t msg_len = strlen(message);
	for(int node_fd : node_fds) {
		cout << "in: " << node_fd << endl;
		if(send(node_fd, message, msg_len, 0) < 0) {
			cout << "hellllp" << endl;
			raise_error("send", "Coordinator failed to send message to node.");
		}
		cout << "out: " << node_fd << endl;

	}
	
	cout << "hi";
	for(pid_t pid : node_pids) {
		int status;
		cout << "waiting for " << pid << endl;
		waitpid(pid, &status, 0);
		if(WIFEXITED(status))
			cout << "Child " << pid <<  " died with wexit status: " << WEXITSTATUS(status) << endl;
	}

	close(coordinator_fd);
	for(int fd : server_fds) close(fd);
}



