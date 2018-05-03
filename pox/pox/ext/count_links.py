import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from routing_algorithms import init_path_map, ecmp_bfs, build_path_map_ecmp
from jelly_graph import adjs_to_switch_map, create_regular_jellyfish_graph, create_irregular_jellyfish_graph
import random
from collections import defaultdict, deque, Counter
import pdb


def init_link_counts(adjs):
    return {
        i: Counter({j: 0 for j in neighbors})
        for i, neighbors in enumerate(adjs)
    }   

def count_links_all_paths(adjs, build_path_map=build_path_map_ecmp):
    path_map = init_path_map()
    switch_adjs = adjs_to_switch_map(adjs)

    build_path_map(switch_adjs, path_map)

    # Iterate over the path map
    link_counts = init_link_counts(adjs)
    for src in switch_adjs.keys():
        # traverse the paths from src to all the 
        # other nodes, using breadth first search. 
        # Each time you traverse a link,
        # increase its count by one.

        # entries are (from, to, dst)
        hops_to_take = deque()
        for dst, (dist, next_hops) in path_map[src].items():
            hops_to_take.extend(( (src, nxt, dst) for nxt in next_hops ))

        while len(hops_to_take) > 0:
            frm, to, dst = hops_to_take.popleft() 
            # traverse the hop (frm, to) along the path
            # from src to dst
            link_counts[frm][to] += 1
            if to == dst:
                continue # we're here! stop counting paths.
            else:
                # add the remaining possible hops
                dist, next_hops = path_map[to][dst]
                hops_to_take.extend(( (to, nxt, dst) for nxt in next_hops ))

    return link_counts


def count_links_perm_traffic(adjs, N=2, n=2, build_path_map=build_path_map_ecmp):
    path_map = init_path_map()
    switch_adjs = adjs_to_switch_map(adjs)

    build_path_map(switch_adjs, path_map)

    # traffic_map[i] is the host reveiceing from host i 
    srcs = range(N, N + n)
    dsts = range(N, N + n)
    random.shuffle(dsts)

    # Iterate over the path map
    link_counts = init_link_counts(adjs)
    for src, dst in zip(srcs, dsts):
        # traverse the paths from src to dst, 
        # using breadth first search. 
        # Each time you traverse a link,
        # increase its count by one.


        # entries are (from, to) for individual hops
        hops_to_take = deque()
        dist, next_hops = path_map[src][dst]
        hops_to_take.extend(((src, nxt) for nxt in next_hops))

        while len(hops_to_take) > 0:
            frm, to = hops_to_take.popleft() 
            # traverse the hop (frm, to) along the path
            # from src to dst
            link_counts[frm][to] += 1
            if to == dst:
                continue # we're here! stop counting paths.
            else:
                # add the remaining possible hops
                dist, next_hops = path_map[to][dst]
                hops_to_take.extend(((to, nxt) for nxt in next_hops))

    return link_counts

def plot_link_counts(link_counts, N, n, r):
    counts_list = [cnt for tos in link_counts.values() for cnt in tos.values()]
    counts_list.sort()

    plt.plot(counts_list)
    plt.savefig('fig9_N{}_n{}_r{}.png'.format(N, n, r), format='png')


if __name__ == '__main__':
    N = 20; n = 20; r = 8
    adjs = create_irregular_jellyfish_graph(N, n, r) 
    link_counts = count_links_perm_traffic(adjs, N, n)
    plot_link_counts(link_counts, N, n, r)
