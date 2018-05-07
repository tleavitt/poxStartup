#!/usr/bin/python
'''
Warning! The order of the imports matters!
Don't touch them if you don'
'''
import os
import sys
from pox.ext.routing_algorithms import possible_next_hops, get_path
from pox.ext.routing_algorithms import min_distance
from pox.ext.routing_algorithms import ecmp_path_builder, ksp_path_builder, init_path_map


from collections import defaultdict
from jelly_graph import create_regular_jellyfish_graph, create_irregular_jellyfish_graph
from jelly_build_topology import int2dpid
import pdb

sys.path.append("../../")
from pox.forwarding.l2_multi_modified import Switch
from pox.lib.addresses import EthAddr


'''
Goal of this file: initialize
and save the below config variables:
'''

# Adjacency map.  [dpid1][dpid2] -> port from dpid1 to dpid2
adjacency = defaultdict(lambda:defaultdict(lambda:None))

def adjsToAdjacency(adjs):
    #mac_map = {}
    port_map = {}

    for key in adjs:
        port_map[key] = 0
        for key_dest in adjs[key]:
            port_map[key] +=1


            adjacency[int2dpid(key)][int2dpid(key_dest)] = port_map[key]


    return adjacency
# ethaddr -> (dpid, port)
mac_map = {}

# dpid -> boolean (True if switch, False if host)
is_switch = {}

# (dpid, port) -> ethaddr
#idport_map = {}



'''
# [sw1][sw2] -> {distance: [possible next hops from sw1] }
path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))

our_path_map = init_path_map()

# Select a routing algorithm:
build_path_map = ecmp_path_builder(8) 
'''



