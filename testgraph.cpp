#include <iostream> 
#include <boost/graph/adjacency_list.hpp> 
#include <boost/graph/graph_utility.hpp> 
#include <boost/graph/random.hpp>
#include <boost/random/mersenne_twister.hpp> 

using namespace boost; 
typedef property<edge_weight_t, int> EdgeWeightProperty; // Define the graph type with edge weights 
typedef adjacency_list<vecS, vecS, undirectedS, no_property, EdgeWeightProperty> Graph; 

int main() { // Define the graph type using Boost adjacency_list 
// Create an empty graph 
Graph g; 
// Define parameters for the random graph 
const int num_vertices = 10; 
// Number of vertices const 
int num_edges = 15; 
// Number of edges 
// Random number generator 
boost::random::mt19937 gen; // Generate the random graph 
boost::generate_random_graph(g, num_vertices, num_edges, gen, false);
// Print the generated graph 
std::cout << "Generated Random Graph:" << std::endl; boost::print_graph(g);

const int min_weight = 1;
const int max_weight = 20;
// Random number generator for weights 
boost::random::uniform_int_distribution<> weight_dist(min_weight, max_weight); 
// Assign random weights to each edge 
graph_traits<Graph>::edge_iterator ei, ei_end; 
for (boost::tie(ei, ei_end) = edges(g); ei != ei_end; ++ei) {
   put(edge_weight, g, *ei, weight_dist(gen)); 
}


// Print the generated graph with weights 
std::cout << "Generated Random Graph with Weights:" << std::endl; 
for (boost::tie(ei, ei_end) = edges(g); ei != ei_end; ++ei) 
{ 
  std::cout << source(*ei, g) << " <--> " << target(*ei, g) << " [weight=" << get(edge_weight, g, *ei) << "]" << std::endl; 
}

}
