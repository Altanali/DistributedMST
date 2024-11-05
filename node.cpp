#include <iostream>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h> 
#include <unistd.h>
#include <cstring>
#include <string>
#include <stdlib.h>
#include <arpa/inet.h>

using namespace std;

int main(int argc, char **argv) {
    //Executable Name, Node_ID
    int node_id = atoi(argv[1]);
    cout << "Hi my id is " << node_id << endl;

    exit(-1*node_id);


    // int sock = socket(AF_INET, SOCK_STREAM, 0);
    // struct sockaddr_in server_address = {AF_INET, htons(8080)};
    // inet_pton(AF_INET, "127.0.0.1", &server_address.sin_addr);

    // if (connect(sock, (struct sockaddr*)&server_address, sizeof(server_address)) < 0) {
    //     std::cerr << "Connection failed" << std::endl;
    //     return -1;
    // }

    // std::cout << "Process 1 (Client): Connected to Process 2. Type messages or 'exit' to quit.\n";

    // char buffer[1024];
    // std::string message;

    // while (true) {
    //     std::cout << "Process 1: ";
    //     std::getline(std::cin, message);

    //     send(sock, message.c_str(), message.size(), 0);

    //     if (message == "exit") {
    //         std::cout << "Process 1: 'exit' command sent. Closing connection." << std::endl;
    //         break;
    //     }

    //     // Receive response from Process 2
    //     memset(buffer, 0, sizeof(buffer));
    //     int bytes_read = read(sock, buffer, sizeof(buffer));
    //     if (bytes_read <= 0) break;

    //     std::cout << "Process 1 received: " << buffer << std::endl;
    // }

    // close(sock);
    // return 0;
}
