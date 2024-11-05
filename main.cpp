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

using namespace std;

int main() {

	int num_nodes = 100;
	int address_base = 8080;
	unordered_map<int, vector<int>> adjacency_list = {
		{0, {1, 2}}, 
		{1, {0}},
		{2, {0}}
	};
	vector<int> server_fds(num_nodes);
	vector<struct sockaddr_in> server_addreses(num_nodes);
	vector<pid_t> node_pids(num_nodes);
	string node_executable = "./node.exe";


	//Write Information to File
	fstream fs;
	fs.open("./node_data.txt", fstream::in | fstream::out | std::fstream::app);

	for(int i = 0; i < num_nodes; ++i) {
		//Create Process and exec(node.exe)
		server_fds[i] = socket(AF_INET, SOCK_STREAM, 0);
		server_addreses[i] = {AF_INET, htons(address_base + i), INADDR_ANY}; 
		fs << to_string(i) << ", " << to_string(server_fds[i]) << endl;
	}

	fs.close();
	

	for(int node_i = 0; node_i < num_nodes; ++node_i) {
		pid_t pid = fork();
		if(pid == -1) {
			cout << "Failed to fork process" << endl;
			exit(-1);
		}
		if(pid == 0) {
			//Exec Node
			char *args[] = {
				(char *)node_executable.c_str(), (char *)(to_string(node_i).c_str()), nullptr
			};
			if(execvp(args[0], args) == -1) {
				perror("excecvp failed");
			}
		}
		else {
			node_pids[node_i] = pid;
		}
	}
	
	cout << "About to wait for children" << endl;
	for(pid_t pid : node_pids) {
		int status;
		waitpid(pid, &status, 0);
		if(WIFEXITED(status))
			cout << "child died with wexit status: " << WEXITSTATUS(status) << endl;
	}
}

