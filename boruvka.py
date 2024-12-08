import argparse
import json
import threading
import copy

ROOT_LIST = None
ORIGINAL_GRAPH = None
CURRENT_GRAPH = None

def get_args(): 
	parser = argparse.ArgumentParser()
	parser.add_argument("file", type=str)
	args = parser.parse_args()
	return args

def get_json_data(file_path):
    try:
        with open(file_path, 'r') as file:
            # Parse the JSON content
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
    except IOError:
        print(f"Error: Could not read the file '{file_path}'.")

def step_1(neighbors, own_id):
    best = neighbors[0]
    for neighbor in neighbors:
        if neighbor.get("weight") < best.get("weight"):
            best = neighbor
    
    global ROOT_LIST
    ROOT_LIST[own_id] = best.get("id")

def point_to_root(non_root, roots):
    pointers = [ROOT_LIST[i] for i in non_root]
    return set(pointers).issubset(roots)

def step_2(non_root, roots, id):
     while (not point_to_root(non_root, roots)):
        global ROOT_LIST
        ROOT_LIST[id] = ROOT_LIST[ROOT_LIST[id]]

def step_3(id):


# each step will be internally multithreaded
def boruvka(graph_data):
    global ROOT_LIST, ORIGINAL_GRAPH, CURRENT_GRAPH 
    ROOT_LIST = list(range(len(graph_data)))
    ORIGINAL_GRAPH = graph_data
    CURRENT_GRAPH = copy.deepcopy(graph_data)

    while len(CURRENT_GRAPH) > 1:
        # Step 1: get the min_weight edge in vertex
        threads = []
        for node_id, node_data in CURRENT_GRAPH.items():
            neighbors = node_data.get("neighbors", [])
            thread = threading.Thread(target=step_1, args=(neighbors, node_id))
            threads.append(thread)
            thread.start()

        #wait for threads to finish

        # THE FOLLOWING IS NOT LISTED IN THE PARALLEL ALGO IN PAPER
        for i in range(len(ROOT_LIST)):
            if (i == ROOT_LIST[ROOT_LIST[i]]):
                ROOT_LIST[i] = i

        roots = set([i for i in range(len(ROOT_LIST)) if i == ROOT_LIST[i]])
        non_roots = set(list(range(len(ROOT_LIST)))) - roots

        # Step 2: find new root
        step_2(non_roots, roots, id)

        # Step 3: 

def spawn_threads(graph_data):

    threads = []
    for node_id, node_data in graph_data.items():
        neighbors = node_data.get("neighbors", [])
        thread = threading.Thread(target=boruvka, args=(node_id, neighbors))
        threads.append(thread)
        thread.start()

if __name__ == "__main__":
    file_path = get_args().file 
    json_data = get_json_data(file_path)
