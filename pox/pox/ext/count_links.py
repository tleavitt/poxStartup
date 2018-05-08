import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from routing_algorithms import init_path_map, ecmp_path_builder, build_path_map_ecmp8, ksp_path_builder
from routing_algorithms import min_distance, possible_next_hops, get_path 
from jelly_graph import adjs_to_switch_map, create_regular_jellyfish_graph, create_irregular_jellyfish_graph
import random
from collections import defaultdict, deque, Counter
import pdb
import time


def init_link_counts(adjs):
    return {
        i: Counter({j: 0 for j in neighbors})
        for i, neighbors in enumerate(adjs)
    }   

def count_links_all_paths(adjs, build_path_map=build_path_map_ecmp8):
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
        for dst, dist_dict in path_map[src].items():
            for dist, next_hops in dist_dict.items():
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
                for dist, next_hops in path_map[to][dst].items():
                    hops_to_take.extend(( (to, nxt, dst) for nxt in next_hops ))

    return link_counts


def count_links_perm_traffic(adjs, N=2, n=2, build_path_map=build_path_map_ecmp8):
    path_map = init_path_map()
    switch_adjs = adjs_to_switch_map(adjs)

    print " building path using {}...".format(build_path_map),
    sys.stdout.flush()
    build_path_map(switch_adjs, path_map)
    print "done."

    # traffic_map[i] is the host reveiceing from host i 
    srcs = range(N, N + n)
    dsts = range(N, N + n)
    random.shuffle(dsts)

    # Iterate over the path map
    print " counting links...",
    sys.stdout.flush()
    link_counts = init_link_counts(adjs)
    for src, dst in zip(srcs, dsts):
        # traverse the paths from src to dst, 
        # using breadth first search. 
        # Each time you traverse a link,
        # increase its count by one.

        # entries are (from, to) for individual hops
        hops_to_take = deque()
        # to avoid counting 
        # for dist, next_hops in path_map[src][dst].items():
        #     hops_to_take.extend(((src, nxt) for nxt in next_hops))
        hops_to_take.extend(
            ((src, nxt) for nxt in possible_next_hops(src, dst, path_map))
        )

        while len(hops_to_take) > 0:
            frm, to = hops_to_take.popleft() 
            # traverse the hop (frm, to) along the path
            # from src to dst
            link_counts[frm][to] += 1
            if to == dst:
                continue # we're here! stop counting paths.
            else:
                # add the remaining possible hops
                # for dist, next_hops in path_map[to][dst].items():
                #     hops_to_take.extend(((to, nxt) for nxt in next_hops))
                hops_to_take.extend(
                    ((to, nxt) for nxt in possible_next_hops(to, dst, path_map))
                )
    print "done."
    return link_counts

def count_links_perm_traffic_dfs(adjs, N=2, n=2, build_path_map=build_path_map_ecmp8):
    path_map = init_path_map()
    switch_adjs = adjs_to_switch_map(adjs)

    print " building path using {}...".format(build_path_map),
    sys.stdout.flush()
    start = time.time()
    build_path_map(switch_adjs, path_map)
    print "done. (took {} s)".format(time.time() - start)

    # traffic_map[i] is the host reveiceing from host i 
    srcs = range(N, N + n)
    dsts = range(N, N + n)
    random.shuffle(dsts)

    # Iterate over the path map
    link_counts = init_link_counts(adjs)
    
    # count the links on paths from cur to dst, 
    # using depth first search to explore all unique
    # paths form src to dst.
    def count_links_helper(cur, dst, cur_path):
        if cur == dst:
            return
        for nxt in possible_next_hops(cur, dst, path_map):
            if (cur, nxt) not in cur_path:
                cur_path.add((cur, nxt))
                link_counts[cur][nxt] += 1
                count_links_helper(nxt, dst, cur_path)
                cur_path.remove((cur, nxt))

    # count the links when traversing 
    # paths from src to dst
    def count_links(src, dst):
        count_links_helper(src, dst, set())

    print " counting links...",
    sys.stdout.flush()
    start = time.time()
    for src, dst in zip(srcs, dsts):
        count_links(src, dst)

    print "done. (took {} s)".format(time.time() - start)
    return link_counts

def count_links_perm_traffic_fixed_paths(adjs, N=2, n=2, build_path_map=build_path_map_ecmp8):
    path_map = init_path_map()
    switch_adjs = adjs_to_switch_map(adjs)

    print " building path using {}...".format(build_path_map),
    sys.stdout.flush()
    start = time.time()
    build_path_map(switch_adjs, path_map)
    print "done. (took {} s)".format(time.time() - start)

    # traffic_map[i] is the host reveiceing from host i 
    srcs = range(N, N + n)
    dsts = range(N, N + n)
    random.shuffle(dsts)

    # Iterate over the path map
    link_counts = init_link_counts(adjs)
    
    print " counting links...",
    sys.stdout.flush()
    start = time.time()

    for src, dst in zip(srcs, dsts):
        p = get_path(src, dst, path_map)
        for i in range(len(p) - 1):
            link_counts[p[i]][p[i+1]] += 1

    print "done. (took {} s)".format(time.time() - start)
    return link_counts

def plot_link_counts(link_counts, N, n, r):
    counts_list = [cnt for tos in link_counts.values() for cnt in tos.values()]
    counts_list.sort()

    plt.plot(counts_list)
    plt.savefig('fig9_N{}_n{}_r{}.png'.format(N, n, r), format='png')


def add_link_plot(ax, link_counts, label, linestyle='--'):
    counts_list = [cnt for tos in link_counts.values() for cnt in tos.values()]
    counts_list.sort()
    ax.plot(counts_list, label=label, linestyle=linestyle, linewidth=1.7)


def main():
    # N = 2; n = 2; r = 2
    # N = 4; n = 4; r = 3
    # N = 10; n = 10; r = 8
    # N = 20; n = 20; r = 8
    N = 245; n = 686; r = 48
    # N = 98; n = 50; r = 10
    # N = 343; n = 343; r = 14
    # N = 245 - 94; n = 686 + 94; r = 25
    adjs = create_irregular_jellyfish_graph(N, n, r) 
    # adjs = create_regular_jellyfish_graph(N, r, n) 
    
    fig, ax = plt.subplots() 
    print "Counting links for ecmp-8."
    link_counts_8 = count_links_perm_traffic_dfs(adjs, N, n,
                                 build_path_map = ecmp_path_builder(8))
    add_link_plot(ax, link_counts_8, "ECMP-8")

    print "Counting links for ecmp-64."
    link_counts_64 = count_links_perm_traffic_dfs(adjs, N, n,
                                 build_path_map = ecmp_path_builder(64))
    add_link_plot(ax, link_counts_64, "ECMP-64")

    print "Counting links for ksp-8."
    sys.stdout.flush()
    link_counts_64 = count_links_perm_traffic_dfs(adjs, N, n,
                                 build_path_map = ksp_path_builder(3))
    add_link_plot(ax, link_counts_64, "KSP-8", linestyle='-')

    ax.set_xlabel("Rank of link")
    ax.set_ylabel("Number of distinct paths link is on")
    ax.set_title("Figure 9 for: {} switches, {} servers, {} ports per switch".format(N, n, r))
    ax.legend(loc='upper left')
    plt.savefig('./fig9_N{}_n{}_r{}.png'.format(N, n, r), format='png')

if __name__ == '__main__':
    main()