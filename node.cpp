#include <iostream>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h> 
#include <unistd.h>
#include <cstring>
#include <string>
#include <stdlib.h>
#include <arpa/inet.h>
#include "json.hpp"
#include "setup_helpers.hpp"
#include <thread>
#include <fstream>

using namespace std;
using json = nlohmann::json;


void connect_to_neighbors(vector<json> &neighbors, json &node_data, unordered_map<int, int> &neighbor_sockets, int node_id);
void accept_neighbor_connections(int num_neighbors, int fd, int node_id);


int main(int argc, char **argv) {
    //Executable Name, Node_ID
    size_t RECV_BUFFER_LENGTH = sizeof(int)*32;
    int node_id = atoi(argv[1]);
    cout << "Hello World from " << node_id << endl; 
    string data_filename = argv[2];
    ifstream ifs(data_filename);
    json network_data = json::parse(ifs);
    json coordinator_data = network_data["coordinatorData"];
    json node_data = network_data["nodeData"];
    json my_data = node_data[to_string(node_id)];
    vector<json> neighbors = my_data["neighbors"];

    //Bind to socket and begin listening 
    int node_fd = my_data["server_fd"];
    int node_port = my_data["server_address"];
    struct sockaddr_in node_address = {AF_INET, htons(node_port), INADDR_ANY};
    
    int optval = 1;
    if((setsockopt(node_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &optval, sizeof(optval)) < 0)) {
			raise_error("setsockopt", "Node failed to set socket options.");
	}

    if(bind(node_fd, (struct sockaddr *)&node_address, sizeof(node_address)) < 0) 
        raise_error("bind", "Node " + to_string(node_id) + " failed to bind to socket " + to_string(node_fd));

    listen(node_fd, neighbors.size());
    

    //Connect to coordinator and wait for signal that connection to neighbors is possible.
    int coordination_sock = socket(AF_INET, SOCK_STREAM, 0);
    if(coordination_sock == -1) {
        raise_error("socket", "Node failed to create a socket to connect to the coordinator.");
    }

    struct sockaddr_in coordinator_address = {AF_INET, htons(coordinator_data["server_address"]), INADDR_ANY};
    inet_pton(AF_INET, "127.0.0.1", &coordinator_address.sin_addr);
    if(connect(coordination_sock, (struct sockaddr *)&coordinator_address, sizeof(coordinator_address)) < 0)  {
        raise_error("connect", "Node " + to_string(node_id) + " failed to connect to coordinator.");
    }
    
    char recv_buffer[RECV_BUFFER_LENGTH];
    if(recv(coordination_sock, recv_buffer, RECV_BUFFER_LENGTH, 0) < 0) {
        raise_error("receive", "Node " + to_string(node_id) + " failed to receive message from coordinator.");
    } else if(strcmp(recv_buffer, "1\0") != 0) {
        raise_error("Coordinator cancelled program execution.");
    } 

    unordered_map<int, int> neighbor_sockets;
    //Connect to Neighbors
    std::thread acceptor_thread(accept_neighbor_connections, neighbors.size(), node_fd, node_id);
    std::thread connector_thread(connect_to_neighbors, ref(neighbors), ref(node_data), ref(neighbor_sockets), node_id);


    connector_thread.join();
    acceptor_thread.join();

    cout << node_id << " has succesfully connected and accepted conenctions to/from all neighbors." << endl;

    exit(0);
}

void connect_to_neighbors(vector<json> &neighbors, json &node_data, unordered_map<int, int> &neighbor_sockets, int node_id) {
    for(auto neighbor_obj : neighbors) {
        int neighbor_id = neighbor_obj["id"];
        json neighbor_data = (node_data)[to_string(neighbor_id)];
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if(sock < 0) {
            raise_error("socket", "Node failed to create socket.");
        }
        struct sockaddr_in neighbor_address = {
            AF_INET, htons(neighbor_data["server_address"]), INADDR_ANY
        };
        inet_pton(AF_INET, "127.0.0.1", &neighbor_address.sin_addr);
        // cout << node_id << " is trying to connect to " << neighbor_id << " with socket number " << sock << endl;
        if(connect(sock, (struct sockaddr *)&neighbor_address, sizeof(neighbor_address)) < 0)  {
            raise_error("connect", "Node " + to_string(node_id) + " failed to connect to neighbor.");
        }
        (neighbor_sockets)[neighbor_id] = sock;
    }
}


void accept_neighbor_connections(int num_neighbors, int my_fd, int node_id) {
    int num_connections = 0;
	while(num_connections < num_neighbors) {
		int fd = accept(my_fd, NULL, 0);
        // cout << node_id << " has accepted a connection on socket number " << fd << endl; 
		if(fd < 0)
			raise_error("accept", "Node failed to accept a node's connection.");
		++num_connections;
	}
}
