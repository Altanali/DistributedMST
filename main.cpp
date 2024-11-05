#include <iostream>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h> 
#include <unistd.h>
#include <cstring>
#include <arpa/inet.h>

using namespace std;

int main() {
	int server_fd = socket(AF_INET, SOCK_STREAM, 0); 
	struct sockaddr_in address = {AF_INET, htons(8080), INADDR_ANY}; 
	cout << "server fd: " << server_fd << endl;
	bind(server_fd, (struct sockaddr*)&address, sizeof(address)); 
	listen(server_fd, 3); 

	int new_socket = accept(server_fd, nullptr, nullptr); 
	if (new_socket < 0) {
		 std::cerr << "Connection failed" << std::endl; return -1; 
	}
	close(server_fd);
	close(new_socket);
}