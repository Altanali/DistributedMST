import argparse
import json
import threading
import copy
import queue
from collections import defaultdict

ROOT_LIST = None
ORIGINAL_GRAPH = None
CURRENT_GRAPH = None

MST_EDGES = queue.Queue()

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

def preprocess_graph(graph_data):
    global ROOT_LIST, ORIGINAL_GRAPH, CURRENT_GRAPH
    ROOT_LIST = list(range(len(graph_data)))

    #change graph_data keys to ints
    ORIGINAL_GRAPH = defaultdict(dict)
    for node_id, node_data in graph_data.items():
        ORIGINAL_GRAPH[int(node_id)] = node_data
        for neighbor in node_data["neighbors"]:
            neighbor["u"] = int(node_id)
            neighbor["v"] = neighbor["id"]
            neighbor["u_component"] = int(node_id)
            neighbor["v_component"] = neighbor["id"]
            neighbor.pop("id")

    CURRENT_GRAPH = copy.deepcopy(graph_data)

def step_1(neighbors, own_id):
    best = neighbors[0]
    for neighbor in neighbors:
        if neighbor["weight"] < best["weight"]:
            best = neighbor
    
    global ROOT_LIST, MST_EDGES
    ROOT_LIST[own_id] = best.get("id")
    MST_EDGES.put((best["u"], best["v"], best["weight"]))

def point_to_root(non_root, roots):
    pointers = [ROOT_LIST[i] for i in non_root]
    return set(pointers).issubset(roots)

def step_2(non_root, roots, id):
    while (not point_to_root(non_root, roots)):
        global ROOT_LIST
        ROOT_LIST[id] = ROOT_LIST[ROOT_LIST[id]]

def step_3(id):
    global CURRENT_GRAPH
    CURRENT_GRAPH[id]["name"] = ROOT_LIST[id]

def step_4(id):
    for node_id, node_data in CURRENT_GRAPH.copy():
        if id == node_data["name"]:
            for neighbor in node_data.get("neighbors"):
                neighbor["u_component"] = id
                neighbor["v_component"] = ROOT_LIST[neighbor["v_component"]]
                #Want root neighbors += (root, neighbor's root)
                CURRENT_GRAPH[id]["neighbors"].append(neighbor)
            CURRENT_GRAPH.pop(node_id)
            
def step_5(id, neighbors):
    neighbors.sort(key=lambda x: x["v_component"])
    prev = None
    best = None
    for neighbor in neighbors.copy():
        if neighbor["v_component"] == id:
            neighbors.remove(neighbor)
        elif neighbor["v_component"] == prev:
            if best["weight"] > neighbor["weight"]:
                neighbors.remove(best)
                best = neighbor
            else:
                neighbors.remove(neighbor)
        else:
            prev = neighbor["v_component"]
            best = neighbor


# each step will be internally multithreaded
def boruvka(graph_data):
    preprocess_graph(graph_data)

    while len(CURRENT_GRAPH) > 1:
        # Step 1: get the min_weight edge in vertex
        threads = []
        for node_id, node_data in CURRENT_GRAPH.items():
            neighbors = node_data.get("neighbors", [])
            step_1(neighbors, node_id)
            #NOTE TO SELF: IS NODE_ID A STR OR INT, WILL THIS AFFECT ANYTHING?
            # thread = threading.Thread(target=step_1, args=(neighbors, node_id))
            # threads.append(thread)
            # thread.start()

        #wait for threads to finish at each step

        # THE FOLLOWING IS NOT LISTED IN THE PARALLEL ALGO IN PAPER
        for i in range(len(ROOT_LIST)):
            if (i == ROOT_LIST[ROOT_LIST[i]]):
                ROOT_LIST[i] = i

        roots = set([i for i in range(len(ROOT_LIST)) if i == ROOT_LIST[i]])
        non_roots = set(list(range(len(ROOT_LIST)))) - roots

        # Step 2: find new root
        for id in non_roots:    
            # TODO: multithread this
            step_2(non_roots, roots, id)

        # Step 3: 
        for non_root in non_roots:
            # TODO: check if types work
            # TODO: multithread this
            step_3(non_root)

        # Step 4:
        for root in roots:
            # only roots execute so only they append to their own edgelists
            # TODO: multithread this
            step_4(root)

        # Step 5:
        for node_id, node_data in CURRENT_GRAPH.items():
            # TODO: multithread this
            neighbors = node_data.get("neighbors", [])
            step_5(node_id, neighbors)
        

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
    boruvka(json_data)
