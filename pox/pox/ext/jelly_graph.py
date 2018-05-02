#!/usr/bin/python

import random
import pdb

def create_jellyfish_graph(N=20, k=12, r=8):
    '''
    N: number of switches
    r: ports per switch for other switches
    '''
    d = r # degree of graph
    adjs = [set() for _ in range(N)]
    # adjs[i] is the set of neighbors of switch i
    unfinished_nodes = set([i for i in range(N)]) # nodes with < d neighbors
    finished_nodes = set() # nodes with d neighbors

    def add_edge(i, j):
        adjs[i].add(j)
        adjs[j].add(i)

    def remove_edge(i, j):
        adjs[i].remove(j)
        adjs[j].remove(i)

    def check_unfin_to_fin(i):
        if len(adjs[i]) == d and i in unfinished_nodes:
            unfinished_nodes.remove(i)
            finished_nodes.add(i)

    def check_fin_to_unfin(i):
        if len(adjs[i]) < d and i in finished_nodes:
            finished_nodes.remove(i)
            unfinished_nodes.add(i)

    # randomly add neighbors
    while len(unfinished_nodes) > 1:
        '''
        choose a random unfinished node i.
        We're gonna add an edge to it, dammit!
        '''
        i = random.choice(tuple(unfinished_nodes))
        unfinished_neighbors = unfinished_nodes - adjs[i] - set([i])
        if len(unfinished_neighbors) > 0:
            j = random.choice(tuple(unfinished_neighbors))
            add_edge(i, j)
            check_unfin_to_fin(i)
            check_unfin_to_fin(j) 
        else:
            '''
             i is neighbors with all unfinished nodes
             => there are less than d unfinished nodes and they
                are all neighbors with i
            There is some j that is finished and is not neighbors
            with i.
            pick it, delete an edge from it, and add an edge i-j
            '''
            finished_neighbors = finished_nodes - adjs[i]
            j = random.choice(tuple(finished_neighbors))
            k = random.choice(tuple(adjs[j]))
            remove_edge(j, k)
            add_edge(j, i)
            check_fin_to_unfin(k)
            check_unfin_to_fin(i)


    # after adding, there might be one node
    # widh degree <= d - 2
    if len(unfinished_nodes) >= 1:
        x = tuple(unfinished_nodes)[0]
        while len(adjs[x]) <= d - 2:
            i = random.choice(tuple(finished_nodes))
            j = random.choice(tuple(adjs[i]))
            remove_edge(i, j)
            add_edge(i, x)
            add_edge(x, j)
            # check_unfin_to_fin(x)

    return adjs

def validate_adjs(adjs, d = 8):
    for i, neighbors in enumerate(adjs):
        assert len(neighbors) <= d
        for j in neighbors:
            assert i in adjs[j]

if __name__ == '__main__':
    N = 4; k = 4; r = 3
    d = r
    print "(N, k, r): ", (N, k, r)
    adjs = create_jellyfish_graph(N, k, r)
    validate_adjs(adjs, d = d)
    print "Graph validation passed."
