#ifndef GRAPH_HELPERS_H
#define GRAPH_HELPERS_H
#include "json.hpp"
#include <boost/graph/adjacency_list.hpp> 
#include <boost/graph/graph_utility.hpp> 
#include <boost/graph/random.hpp>
#include <boost/random/mersenne_twister.hpp> 
#include <random>
#include <vector>

using namespace std;
using namespace boost;
using json = nlohmann::json;
typedef boost::property<edge_weight_t, int> EdgeWeightProperty;
typedef boost::adjacency_list<vecS, vecS, undirectedS, no_property, EdgeWeightProperty> UndirectedGraph;
typedef UndirectedGraph::edge_descriptor Edge;


void init_random_undirected(
		UndirectedGraph &graph,
		int num_nodes, 
		int num_edges = -1, 
		int min_weight = 0,
		int max_weight = 100, 
		bool connected = false
) {
	graph.clear();
	std::random_device rd;
	std::mt19937 gen(rd());

	if(num_edges == -1) {
		int max_num_edges = num_nodes*(num_nodes - 1) / 2;
		boost::random::uniform_int_distribution<> distrib(1, max_num_edges);
		num_edges = distrib(gen);
	}

	boost::generate_random_graph(graph, num_nodes, num_edges, gen, false);

	boost::random::uniform_int_distribution<> weight_distrib(min_weight, max_weight);
	graph_traits<UndirectedGraph>::edge_iterator e_iter, e_end;
	for(boost::tie(e_iter, e_end) = edges(graph); e_iter != e_end; ++e_iter) {
		put(edge_weight, graph, *e_iter, weight_distrib(gen));
	}

	return;

}

void undirected_graph_to_json(UndirectedGraph &graph, json &obj) {
	UndirectedGraph::vertex_iterator v_iter, v_end;
	auto weight_map = get(edge_weight, graph);
	for(tie(v_iter, v_end) = vertices(graph); v_iter != v_end; ++v_iter) {
		graph_traits<UndirectedGraph>::adjacency_iterator adj_iter, adj_end;
		vector<json> neighbors_i;
		tie(adj_iter, adj_end) = adjacent_vertices(*v_iter, graph);
		for(; adj_iter != adj_end; ++adj_iter) {	
			json neighbor_obj;
			int neighbor_id = *adj_iter;
			pair<Edge, bool> ed = boost::edge(*v_iter, *adj_iter, graph);
			cout << get(edge_weight, graph, ed.first) << endl;

			int edge_weight = weight_map[ed.first];
			neighbor_obj["id"] = neighbor_id;
			neighbor_obj["weight"] = edge_weight;
			neighbors_i.push_back(neighbor_obj); //probably a better way to do this
		}
		obj[to_string(*v_iter)] = {{"neighbors", neighbors_i}};
	}

}


void print_undirected_graph(UndirectedGraph &graph) {
	graph_traits<UndirectedGraph>::edge_iterator e_iter, e_end;
	for(boost::tie(e_iter, e_end) = edges(graph); e_iter != e_end; ++e_iter) 
	{ 
  		std::cout << source(*e_iter, graph) << " <--> " << target(*e_iter, graph)  << " [weight=" << get(edge_weight, graph, *e_iter) << "]" << std::endl; 
	}
}
#endif