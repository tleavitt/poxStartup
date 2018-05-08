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

import pdb

sys.path.append("../../")
from pox.forwarding.l2_multi_modified import Switch
from pox.lib.addresses import EthAddr


'''
Goal of this file: initialize
and save the below config variables:
'''
def int2dpid( dpid ):
   try:
      dpid = hex( dpid )[ 2: ]
      dpid = '0' * ( 16 - len( dpid ) ) + dpid
      return dpid
   except IndexError:
      raise Exception( 'Unable to derive default datapath ID - '
                       'please either specify a dpid or use a '
               'canonical switch name such as s23.' )
# Adjacency map.  [dpid1][dpid2] -> port from dpid1 to dpid2
adjacency = defaultdict(lambda:defaultdict(lambda:None))
#(dpid, port) -> ethaddr
idport_map = {}
mac_map = {}
is_switch = {}



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


# dpid -> boolean (True if switch, False if host)

def make_is_switch(adjacency, N, n, r):
	for dpid in adjacency:
		if int(dpid) < N:
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



