from matplotlib.pyplot import matplotlib
from routing_algorithm import init_path_map, ecmp_bfs, build_path_map_ecmp
from jelly_graph import adjs_to_switch_map, create_regular_jellyfish_graph, create_irregular_jellyfish_graph


from collections import defaultdict, deque, Counter


def init_link_counts(adjs):
    return {
        i: Counter({j: 0 for j in neighbors})
        for i, neighbors in enumerate(adjs)
    }   

def count_distinct_paths_for_links(N, n, r):
    path_map = init_path_map()
    adjs = create_irregular_jellyfish_graph(N, n, r) 
    switch_adjs = adjs_to_switch_map(adjs)

    build_path_map_ecmp(switch_adjs, path_map)

    # Iterate over the path map
    link_counts = init_link_counts(adjs)
    for start, step_map in path_map.items()
        # traverse the paths from start to all the 
        # other nodes. Each time you traverse a link,
        # increase its count by one.
        