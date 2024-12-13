#include <pthread.h> /*used in other parts of the assignment */
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>  /* for uint64  */
#include <time.h>    /* for clock_gettime */
#include <iostream>
#include <fstream>
#include <unordered_map>
#include <vector>
#include <numeric>
#include "json.hpp"

using json = nlohmann::json;

// Structure to represent a neighbor
struct Neighbor {
    int u;
    int v;
    int u_component;
    int v_component;
    int weight;
};

// Structure to represent a node
struct Node {
    int id;
    int name; 
    std::vector<Neighbor> neighbors;
};

void print_graph(std::unordered_map<int, Node>* graph){
    for (const auto& [id, node] : *graph) {
        std::cout << "Node: " << id << ", Name: " << node.name << "\n";
        std::cout << "  Neighbors:\n";
        for (const auto& neighbor : node.neighbors) {
            std::cout << "    u: " << neighbor.u << ", v: " << neighbor.v << ", Weight: " << neighbor.weight << "\n";
        }
    }
}

void step_1(std::vector<Neighbor> neighbors, int id, std::vector<int>* rootlist, std::vector<Neighbor>* MST){
    Neighbor best = neighbors[0];
    for (Neighbor& neighbor : neighbors){
        if (neighbor.weight < best.weight){
            best = neighbor;
        }
    }

    (*rootlist)[id] = best.v_component;
    Neighbor* temp = new Neighbor();
    temp->v_component = best.v_component;
    temp->v = best.v;
    temp->u_component = best.u_component;
    temp->u = best.u;
    temp->weight = best.weight;
    MST->push_back(*temp);
}

bool point_to_root(std::vector<int>* non_roots, std::vector<int>* roots, std::vector<int>* rootlist){
}

void step_2(std::vector<int>* non_roots, std::vector<int>* roots, std::vector<int>* rootlist){
    
}

std::vector<Neighbor>* boruvka(std::unordered_map<int, Node>* graph, int numThread){
    size_t graph_size = graph->size();
    std::vector<int> rootlist(graph_size);
    std::iota(rootlist.begin(), rootlist.end(), 0); // Fill with 0, 1, 2, ..., n-1
    // Print the vector
    for (int num : rootlist) {
        std::cout << num << " ";
    }

    std::unordered_map<int, Node> current_graph = *graph;
    std::vector<Neighbor>* MST = new std::vector<Neighbor>();

    while (current_graph.size() > 1){
        for (const auto& [node_id, node] : current_graph) {
            step_1(node.neighbors, node_id, &rootlist, MST);
        }

        std::vector<int> roots;
        std::vector<int> non_roots;


        for (int i = 0; i < graph_size; i++){
            if (i == rootlist[rootlist[i]]){
                rootlist[i] = i;
                roots.push_back(i);
            } else {
                non_roots.push_back(i);
            }
        }

        for (int i : non_roots){
            step_2(&non_roots, &roots, &rootlist);
        }

    }

    return MST;
}

int main(int argc, char *argv[]) {
    uint64_t execTime; /*time in nanoseconds */
    struct timespec tick, tock;

    char* filepath = argv[1];

    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open the file." << std::endl;
        return 1;
    }

    // Parse the JSON file
    json jsonData;
    try {
        file >> jsonData;
    } catch (const std::exception& e) {
        std::cerr << "Error parsing JSON: " << e.what() << std::endl;
        return 1;
    }

    // Unordered map to store the graph
    std::unordered_map<int, Node>* graph = new std::unordered_map<int, Node>();

    // Iterate through JSON data
    for (const auto& [key, value] : jsonData.items()) {
        int nodeId = std::stoi(key); // Convert string key to integer

        Node node;
        node.id = nodeId;
        node.name = nodeId; 

        // Parse neighbors
        if (value.contains("neighbors")) {
            for (const auto& neighbor : value["neighbors"]) {
                Neighbor n;
                n.u = nodeId;
                n.u_component = nodeId;
                n.v = neighbor["id"];
                n.v_component = neighbor["id"];
                n.weight = neighbor["weight"];
                node.neighbors.push_back(n);
            }
        }

        // Insert into graph
        // graph[nodeId] = node;
        graph->emplace(nodeId, node);
    }

    print_graph(graph);
    int numThread = std::atoi(argv[2]);
    boruvka(graph, numThread);

    return 0;
}