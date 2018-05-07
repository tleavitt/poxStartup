'''
Warning! The order of the imports matters!
Don't touch them if you don't have to!
'''
import os
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time


from mininet.log import setLogLevel
from mininet.clean import cleanup
from mininet.util import dumpNodeConnections

from jelly_graph import create_regular_jellyfish_graph, create_irregular_jellyfish_graph
import pdb

from pox.ext.config import ADJ_FILENAME, MAC_FILENAME, IS_SWITCH_FILENAME, IDPORT_FILENAME
import cPickle as pickle

with open(ADJ_FILENAME, 'r+') as af:
  adjacency = pickle.load(af)

with open(IS_SWITCH_FILENAME, 'r+') as isf:
  is_switch = pickle.load(isf)

with open(IDPORT_FILENAME, 'r+') as idf:
  idport_map = pickle.load(idf)

# class JellyTopo( Topo ):
#     '''
#     Jellyfish topology with multiple links
#     '''
#     def __init__( self, adjacency,
#         verbose=False, **kwargs ):
#         Topo.__init__( self, **kwargs )

#         self.adjacency = adjacency
#         nodes = {}

#         for dpid in adjacency:
#             if is_switch[dpid]:
#                 n = self.addSwitch('s{}'.format(dpid), dpid=dpid)
#             else:
#                 n = self.addSwitch('h{}'.format(dpid), dpid=dpid)
#             nodes[dpid] = n


#         for dpid1, neighbors in adjacency.items():
#             for dpid1, port in neighbors.items():
#                 idport_map = 

def buildJellyFishTopo(net):
        nodes = {}

        for dpid in adjacency:
            if is_switch[dpid]:
                n = net.addSwitch('s{}'.format(dpid), dpid=dpid)
            else:
                n = net.addHost('h{}'.format(dpid), pid=int(dpid))
            nodes[dpid] = n


        for dpid1, neighbors in adjacency.items():
            for dpid2 in neighbors:
                port12 = adjacency[dpid1][dpid2]
                port21 = adjacency[dpid2][dpid1]
                addr1 = idport_map[(dpid1, port12)]
                addr2 = idport_map[(dpid2, port21)]

                net.addLink(
                    nodes[dpid1],
                    nodes[dpid2],
                    port1 = port12,
                    port2 = port12,
                    addr1 = addr1,
                    addr2 = addr2    
                )

def runJellyfishLink():
    '''
    Create and run jellyfish network
    '''
    net = Mininet(topo=None,
                build=False,
                host=CPULimitedHost, link=TCLink)
    net.addController('c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=6633) 
    buildJellyFishTopo(net)

    print "Dumping switch connections"
    dumpNodeConnections(net.switches)

    # dhcp_script = create_dhcp_file(topo)
    # pdb.set_trace()
    net.start()
    # for i, h in enumerate(net.hosts):
    #     h.cmd('dhclient eth0')

    # CLI(net, script=dhcp_script)
    CLI(net)

    net.stop()

def main():
    cleanup()
    setLogLevel('info')
    runJellyfishLink(remote_control=True)

if __name__ == "__main__":
    main()

