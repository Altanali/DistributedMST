#ifndef SETUP_HELPERS_HPP
#define SETUP_HELPERS_HPP

#include "json.hpp"
#include <netinet/in.h> 
#include <fstream>
#include <iostream>
#include <argparse/argparse.hpp>

using namespace std;
using json = nlohmann::json;


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

void setup_basic_graph_datafile(int num_nodes, 
								unordered_map<int, vector<int>> &graph, 
								vector<int> &server_fds, 
								vector<struct sockaddr_in> server_addresses, 
								string out_filename) {
	/**
	 * Create a datafile with n lines where the i^th line contains the following data
	 * for the i^th node: 
	 * 		socket file descriptor, 
	 * 		server addresses,
	 * 		list[int id for each neighbor]
	 */
	ofstream ofs;
	ofs.open(out_filename);
	for(int idx = 0; idx < num_nodes; ++idx) {
		ofs << to_string(server_fds[idx]);
		ofs << "," << to_string(server_addresses[idx].sin_port);
		for(int neighbor : graph[idx]) {
			ofs << "," << neighbor;
		}
		ofs << endl;
	}
	ofs.close();

}

void dump_json_to_datafile(json obj, string out_filename) {
	ofstream ofs;
	ofs.open(out_filename);
	ofs << obj.dump();
	ofs.close();
}

void raise_error(string error_message) {
	cerr << error_message << endl;
	exit(-1);
}

void raise_error(string context, string error_message) {
	fprintf(stderr, "%s: %s\n", context.c_str(), strerror(errno));
	cerr << error_message << endl;
	exit(-1);
}

#endif