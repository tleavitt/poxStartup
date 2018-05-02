#!/usr/bin/python

import random
import pdb

def create_regular_jellyfish_graph(N=20, r=8):
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
            j = random.choice(tuple(adjs[i] - set([x]))) 
            # it's ok to choose x == j, this just becomes a noop
            remove_edge(i, j)
            add_edge(i, x)
            add_edge(x, j)
            # check_unfin_to_fin(x)

    return adjs


def create_irregular_jellyfish_graph(N=20, n=10, r=8):
    '''
    N: number of switches
    n: number of hosts
    r: total ports per switch
    '''
    d = r # degree of graph
    adjs = [set() for _ in range(N + n)]
    # adjs[i] is the set of neighbors of node i
    all_switches = set(range(N)) # switches have 
    unfinished_nodes = set([i for i in range(N + n)])
        # switches with < d neighbors, or hosts without a server.
    finished_nodes = set()
        # switches with d neighbors or hosts with a server.

    def is_switch(i):
        return i < N

    def is_host(i):
        return i >= N

    def add_edge(i, j):
        adjs[i].add(j)
        adjs[j].add(i)

    def remove_edge(i, j):
        adjs[i].remove(j)
        adjs[j].remove(i)

    def check_unfin_to_fin(i):
        is_fin = (len(adjs[i]) == d) if is_switch(i) else (len(adjs[i]) == 1)
        if is_fin and i in unfinished_nodes:
            unfinished_nodes.remove(i)
            finished_nodes.add(i)

    def check_fin_to_unfin(i):
        is_unfin = (len(adjs[i]) < d) if is_switch(i) else (len(adjs[i]) == 0)
        if is_unfin and i in finished_nodes:
            finished_nodes.remove(i)
            unfinished_nodes.add(i)

    # randomly add neighbors
    while len(unfinished_nodes) > 1:
        '''
        choose a random unfinished node i.
        We're gonna add an edge to it, dammit!
        '''
        i = random.choice(tuple(unfinished_nodes))
        if is_switch(i):
            # switches can be neighbors with anything
            possible_neighbors = unfinished_nodes - adjs[i] - set([i])
        else:
            # hosts can only be neighbors with switches
            possible_neighbors = unfinished_nodes & all_switches

        if len(possible_neighbors) > 0:
            j = random.choice(tuple(possible_neighbors))
            add_edge(i, j)
            check_unfin_to_fin(i)
            check_unfin_to_fin(j) 
        else:
            '''
             i is neighbors with all unfinished switches
             => there are less than d unfinished switches and they
                are all neighbors with i
            There is some j that is finished and is not neighbors
            with i.
            pick it, delete an edge from it, and add an edge i-j

            if i is not a switch, that means the intersection of unfinished_nodes
            and all_switches is empty, i.e. the only remaining nodes are hosts.
            '''
            if is_switch(i):
                # switches can be neighbors with anything
                finished_neighbors = finished_nodes - adjs[i]
            else:
                finished_neighbors = finished_nodes & all_switches

            j = random.choice(tuple(finished_neighbors))
            k = random.choice(tuple(adjs[j]))
            remove_edge(j, k)
            add_edge(j, i)
            check_fin_to_unfin(k)
            check_unfin_to_fin(i)


    # after adding, there might be one node
    # widh degree <= d - 2
    if len(unfinished_nodes) == 1:
        x = tuple(unfinished_nodes)[0]
        if is_host(x):
            # Disconnect a random pair of switches, and add
            # a connection between one of the switches and the host.
            i = random.choice(range(N))
            j = random.choice(tuple(adjs[i] & all_switches))
            remove_edge(i, j)
            add_edge(i, x)
        else:
            while len(adjs[x]) <= d - 2:
                i = random.choice(tuple(finished_nodes))
                j = random.choice(tuple(adjs[i] - set([x]))) 
                # it's ok to choose x == j, this just becomes a noop
                remove_edge(i, j)
                add_edge(i, x)
                add_edge(x, j)
                # check_unfin_to_fin(x)
    else:
        pass
        # pdb.set_trace()        

    return adjs

def validate_regular_adjs(adjs, d = 8):
    for i, neighbors in enumerate(adjs):
        assert len(neighbors) <= d
        for j in neighbors:
            assert i in adjs[j]

def validate_irregular_adjs(adjs, N, n):
    assert len(adjs) == N + n
    for sw, neighbors in zip(range(N), adjs[:N]):
        assert len(neighbors) <= d
        for j in neighbors:
            assert sw in adjs[j]
    for h, neighbors in zip(range(N, N+n), adjs[N:N+n]):
        # pdb.set_trace()
        assert len(neighbors) == 1
        sw = tuple(neighbors)[0]
        assert h in adjs[sw]

REGULAR = False
def create_jellyfish_graph(N, n, r):
    if REGULAR:
        return create_regular_jellyfish_graph(N, r)
    else:
        return create_irregular_jellyfish_graph(N, n, r)

def validate_adjs(adjs, d=8, N=20, n=10):
    if REGULAR:
        return validate_regular_adjs(adjs, d)
    else:
        return validate_irregular_adjs(adjs, N, n)

if __name__ == '__main__':
    N = 40; n = 20; r = 10
    d = r
    print "(N, n, r): ", (N, n, r)
    adjs = create_jellyfish_graph(N, n, r)
    validate_adjs(adjs, d = d, N=N, n=n)
    print "Graph validation passed."
