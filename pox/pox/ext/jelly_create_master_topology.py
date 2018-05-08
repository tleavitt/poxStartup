#!/usr/bin/python
'''
Warning! The order of the imports matters!
Don't touch them if you don'
'''
import os
import sys

from collections import defaultdict
from jelly_graph import create_regular_jellyfish_graph, create_irregular_jellyfish_graph
from routing_algorithms import ecmp_path_builder, ksp_path_builder, init_path_map
from routing_algorithms import path_map_to_dict

import cPickle as pickle
import pdb

sys.path.append("../../")
from pox.ext.config import ADJ_FILENAME, MAC_FILENAME, IS_SWITCH_FILENAME, IDPORT_FILENAME, PATHMAP_FILENAME
from pox.lib.addresses import EthAddr


'''
Goal of this file: initialize
and save the below config variables:
'''

# Adjacency map.  [dpid1][dpid2] -> port from dpid1 to dpid2
# adjacency = defaultdict(lambda:defaultdict(lambda:None))
adjacency = {}
#(dpid, port) -> ethaddr
idport_map = {}
# ethaddr -> (dpid, port)
mac_map = {}
# dpid -> boolean (True if switch, False if host)
is_switch = {}

def adjsToAdjacency(adjs, N):
    #mac_map = {}
    # port_map = {}
    # for key in adjs:
    #     port_map[key] = 0
    #     for key_dest in adjs[key]:
    #         port_map[key] +=1
    #         adjacency[int2dpid(key)][int2dpid(key_dest)] = port_map[key]

    for i, neighbors in enumerate(adjs):
        key = i + 1
        adjacency[int(key)] = {}
        cur_port = 2 if int(key) <= N else 1
        for j in neighbors:
            key_dest = j + 1
            adjacency[int(key)][int(key_dest)] = cur_port
            cur_port += 1

    return adjacency



def make_is_switch(adjacency, N, n, r):
	for dpid in adjacency:
		if int(dpid) <= N:
			#its a switch
			is_switch[dpid] = True
		else :
			is_switch[dpid] = False

	return is_switch


# Format is: most signifant byte: port number
#            least significant bytes: dpid
def dpid_port_to_mac(dpid, port):
	msb = port & 0xff
	lsbs = int(dpid) & 0x00FFffFFffFF
	eth_addr = (msb << 40) | lsbs
	return EthAddr("%012x" % eth_addr)

def id_port_maps(adjacency):

	for i, neighbors in adjacency.items():
		for j, port in neighbors.items():
			eth_addr = dpid_port_to_mac(i, port)
			mac_map[eth_addr] = (i, port)
			idport_map[(i, port)] = eth_addr

	return mac_map, idport_map

'''
# [sw1][sw2] -> {distance: [possible next hops from sw1] }
path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))

our_path_map = init_path_map()

# Select a routing algorithm:
build_path_map = ecmp_path_builder(8) 
'''

def pickle_obj(filename, obj):
    with open(filename, 'w+') as f:
        pickle.dump(obj, f)


# build_path_map = ecmp_path_builder(8) 
# build_path_map = ecmp_path_builder(64) 
build_path_map = ksp_path_builder(8) 

def create_topology(N, n, r):
    adjs = create_irregular_jellyfish_graph(N=N, n=n, r=r)
    adjsToAdjacency(adjs, N) # populate adjacency
    make_is_switch(adjacency, N, n, r) # populate is_switch
    id_port_maps(adjacency) # populate mac_map and idport_map
    our_path_map = init_path_map() 
    build_path_map(adjacency, our_path_map)
    our_path_map = path_map_to_dict(our_path_map)

    # pickle the topo files.
    pickle_obj(ADJ_FILENAME, adjacency)
    pickle_obj(IS_SWITCH_FILENAME, is_switch)
    pickle_obj(MAC_FILENAME, mac_map)
    pickle_obj(IDPORT_FILENAME, idport_map)
    pickle_obj(PATHMAP_FILENAME, our_path_map)

if __name__ == "__main__":
    N = 50; n = 10; r = 10
    create_topology(N, n, r)

