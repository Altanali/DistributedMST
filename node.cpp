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
#include <fstream>

using namespace std;
using json = nlohmann::json;

int main(int argc, char **argv) {
    //Executable Name, Node_ID
    int node_id = atoi(argv[1]);
    cout << "Hello World from " << node_id << endl; 
    string data_filename = argv[2];
    ifstream ifs(data_filename);
    
    json network_data = json::parse(ifs);
    json coordinator_data = network_data["coordinatorData"];
    json node_data = network_data["nodeData"];

    json my_data = node_data[to_string(node_id)];
    vector<int> neighbors = my_data["neighbors"];






    //Bind to socket and begin listening 
    int node_fd = my_data["server_fd"];
    int node_port = my_data["server_address"];
    struct sockaddr_in node_address = {AF_INET, htons(node_port), INADDR_ANY};
    // if(bind(node_fd, (struct sockaddr *)&node_address, sizeof(node_address)) < 0) 
    //     raise_error("Node " + to_string(node_id) + " failed to bind to socket " + to_string(node_fd));

    // listen(node_fd, neighbors.size());
    
    //Connect to coordinator.
    struct sockaddr_in coordinator_address = {AF_INET, htons(coordinator_data["server_address"]), INADDR_ANY};
    inet_pton(AF_INET, "127.0.0.1", &coordinator_address.sin_addr);
    if(connect(node_fd, (struct sockaddr *)&coordinator_address, sizeof(coordinator_address)) < 0)  {
        fprintf(stderr, "connect: %s\n", strerror(errno));
        raise_error("Node " + to_string(node_id) + " failed to connect to coordinator.");
    }
    
    exit(0);

    
    


}
