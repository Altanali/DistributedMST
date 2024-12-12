import argparse
import json
import threading
import copy
import queue
from collections import defaultdict
from pprint import pprint

NUM_THREAD = 10
STEP_1_BARRIER = None
STEP_ROOT_BARRIER = None
STEP_2_BARRIER = None
STEP_3_BARRIER = None
STEP_4_BARRIER = None
STEP_5_BARRIER = None
NON_ROOTS = None
ROOTS = None

ROOT_LIST = None
ORIGINAL_GRAPH = None
CURRENT_GRAPH = None

MST_EDGES = queue.SimpleQueue()

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
        node_data["name"] = int(node_id)

    CURRENT_GRAPH = copy.deepcopy(ORIGINAL_GRAPH)

def step_1(neighbors, own_id):
    best = neighbors[0]
    for neighbor in neighbors:
        if neighbor["weight"] < best["weight"]:
            best = neighbor
    
    global ROOT_LIST, MST_EDGES
    ROOT_LIST[own_id] = best.get("v_component")
    MST_EDGES.put((best["u"], best["v"], best["weight"]))

def point_to_root(non_root, roots):
    pointers = [ROOT_LIST[i] for i in non_root]
    return set(pointers).issubset(roots)

def step_2(non_root, roots, start, end):
    # print("step_2 in")
    while (not point_to_root(non_root, roots)):
        global ROOT_LIST
        # for temp in non_root: #Remove when we multithread
        for id in range(start, end):
            ROOT_LIST[NON_ROOTS[id]] = ROOT_LIST[ROOT_LIST[NON_ROOTS[id]]]
    # print("step_2 out")

def step_3(id):
    # print("step_3 in")
    global CURRENT_GRAPH
    CURRENT_GRAPH[id]["name"] = ROOT_LIST[id]
    # print("step_3 out")

def step_4(id):
    for node_id, node_data in CURRENT_GRAPH.copy().items():
        if id == node_data["name"]:
            if id != node_id:
                for neighbor in (node_data.get("neighbors") or []):
                    neighbor["u_component"] = id
                    neighbor["v_component"] = ROOT_LIST[neighbor["v_component"]]
                    #Want root neighbors += (root, neighbor's root)
                    CURRENT_GRAPH[id]["neighbors"].append(neighbor)
                    # print("in loop")
                CURRENT_GRAPH.pop(node_id)
            else:
                #Update the components out edge names without readding to their neighbors list.
                temp_data = CURRENT_GRAPH[node_id]
                for neighbor in temp_data.get("neighbors" or []):
                    neighbor["v_component"] = ROOT_LIST[neighbor["v_component"]]

    # print("step_4 out")

def step_5(id, neighbors):
    # print("step_5 in")
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
    # print("step_5 out")

def thread_boruvka(tid):
    current_keys = list(CURRENT_GRAPH.keys())
    # Step 1
    chunk = len(CURRENT_GRAPH) // NUM_THREAD + 1
    for i in range(tid * chunk, min((tid + 1) * chunk, len(CURRENT_GRAPH))):
        step_1(CURRENT_GRAPH[current_keys[i]]["neighbors"], current_keys[i])
    
    STEP_1_BARRIER.wait()
    STEP_ROOT_BARRIER.wait()

    # Step 2
    chunk = len(NON_ROOTS) // NUM_THREAD + 1
    step_2(NON_ROOTS, ROOTS, tid * chunk, min((tid + 1) * chunk, len(NON_ROOTS)))
    STEP_2_BARRIER.wait()

    # Step 3
    for i in range(tid * chunk, min((tid + 1) * chunk, len(NON_ROOTS))):
        step_3(NON_ROOTS[i])
    STEP_3_BARRIER.wait()

    # Step 4
    chunk = len(ROOTS) // NUM_THREAD + 1
    for i in range(tid * chunk, min((tid + 1) * chunk, len(ROOTS))):
        step_4(ROOTS[i])
    STEP_4_BARRIER.wait()

    # Step 5 
    current_keys = list(CURRENT_GRAPH.keys())
    chunk = len(CURRENT_GRAPH) // NUM_THREAD + 1
    for i in range(tid * chunk, min((tid + 1) * chunk, len(CURRENT_GRAPH))):
        step_5(current_keys[i], CURRENT_GRAPH[current_keys[i]]["neighbors"])
    STEP_5_BARRIER.wait()

# each step will be internally multithreaded
def boruvka(graph_data):
    preprocess_graph(graph_data)
    global STEP_1_BARRIER, STEP_ROOT_BARRIER
    global STEP_2_BARRIER, STEP_3_BARRIER, STEP_4_BARRIER, STEP_5_BARRIER
    global ROOTS, NON_ROOTS

    while len(CURRENT_GRAPH) > 1:
        # Step 1: get the min_weight edge in vertex
        threads: list[threading.Thread] = []

        STEP_1_BARRIER = threading.Barrier(NUM_THREAD + 1)
        STEP_ROOT_BARRIER = threading.Barrier(NUM_THREAD + 1)
        STEP_2_BARRIER = threading.Barrier(NUM_THREAD)
        STEP_3_BARRIER = threading.Barrier(NUM_THREAD)
        STEP_4_BARRIER = threading.Barrier(NUM_THREAD)
        STEP_5_BARRIER = threading.Barrier(NUM_THREAD + 1)

        for i in range(NUM_THREAD):
            thread = threading.Thread(target=thread_boruvka, args=(i,))
            threads.append(thread)
            thread.start()

        #wait for threads to finish at each step

        STEP_1_BARRIER.wait()

        # THE FOLLOWING IS NOT LISTED IN THE PARALLEL ALGO IN PAPER
        for i in range(len(ROOT_LIST)):
            if (i == ROOT_LIST[ROOT_LIST[i]]):
                ROOT_LIST[i] = i

        ROOTS = set([i for i in range(len(ROOT_LIST)) if i == ROOT_LIST[i]])
        NON_ROOTS = list(set(list(range(len(ROOT_LIST)))) - ROOTS)
        ROOTS = list(ROOTS)

        STEP_ROOT_BARRIER.wait()
        STEP_5_BARRIER.wait()
        
    edges = remove_duplicate_edges()
    print(edges)
    return edges

def spawn_threads(graph_data):

    threads = []
    for node_id, node_data in graph_data.items():
        neighbors = node_data.get("neighbors", [])
        thread = threading.Thread(target=boruvka, args=(node_id, neighbors))
        threads.append(thread)
        thread.start()

def remove_duplicate_edges():
    global MST_EDGES
    #THIS WILL EMPTY THE QUEUE, ONLY USE AT END
    edges = set()
    while not MST_EDGES.empty():
        edge = MST_EDGES.get()
        if edge[0] < edge[1]:
            edges.add((edge[0], edge[1], edge[2]))
        else:
            edges.add((edge[1], edge[0], edge[2]))
    
    return edges

if __name__ == "__main__":
    file_path = get_args().file 
    json_data = get_json_data(file_path)
    boruvka(json_data)
    