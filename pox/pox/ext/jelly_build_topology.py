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

from jelly_graph import create_jellyfish_graph


class RegularJellyTopo( Topo ):
    '''
    Jellyfish topology with regular graph shape
    '''
    def __init__( self, N=20, k=12, r=8, verbose=False, **kwargs ):
        Topo.__init__( self, **kwargs )

        # N: number of switches
        # k: ports per switch
        # r: ports per switch for other switches (degree of graph)

        self.N = N; self.k = k; self.r = r
        self.adjs = adjs = create_regular_jellyfish_graph(N, r)


        n_svs = k - r
        switches = [self.addSwitch('s{}'.format(i)) for i in range(N)]
        servers = [
            [self.addHost('h{}_{}'.format(i, j)) for j in range(n_svs)]
            for i in range(N)
        ]
        # servers[i] is the list of servers connected to switches[i]

        # first, connect servers to switches
        for sw, svs in zip(switches, servers):
            for sv in svs:
                if verbose:
                    print "JF: adding link", sw, "<->", sv
                self.addLink(sw, sv)

        # connect switches according to the jellyfish adjacency lists.
        for i, neighbors in enumerate(adjs):
            for j in neighbors:
                # only add links with i < j to avoid double counting.
                if i < j:
                    if verbose:
                        print "JF: adding link", switches[i], "<->", switches[j]
                    self.addLink(switches[i], switches[j])

class IrregularJellyTopo( Topo ):
    '''
    Jellyfish topology with multiple links
    '''
    def __init__( self, N=20, n=20, r=8, verbose=False, **kwargs ):
        Topo.__init__( self, **kwargs )

        # N: number of switches
        # n: number of hosts
        # r: ports per switch

        self.N = N; self.n = n; self.r = r
        self.adjs = adjs = create_irregular_jellyfish_graph(N, n, r)

        # first N nodes are switches, last n are hosts
        nodes = [self.addSwitch('s{}'.format(i)) for i in range(N)]
        nodes += [self.addHost('h{}'.format(i) for i in range(n))]

        # connect nodes according to the jellyfish adjacency lists.
        for i, neighbors in enumerate(adjs):
            for j in neighbors:
                # only add links with i < j to avoid double counting.
                if i < j:
                    if verbose:
                        print "JF: adding link", nodes[i], "<->", nodes[j]
                    self.addLink(nodes[i], nodes[j])


def runJellyfishLink(remote_control=False):
    '''
    Create and run jellyfish network
    '''
    topo = RegularJellyTopo(N=4, k=4, r=2, verbose=True)
    if remote_control:
        net = Mininet(topo=None,
                    build=False,
                    host=CPULimitedHost, link=TCLink)
        net.addController('c0',
                controller=RemoteController,
                ip='127.0.0.1',
                port=6633) 
        net.buildFromTopo(topo)
    else:
        net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=JELLYPOX)

    print "Dumping switch connections"
    dumpNodeConnections(net.switches)
    net.start()
    CLI(net)
    net.stop()

def main():
    cleanup()
    setLogLevel('info')
    runJellyfishLink(remote_control=True)

if __name__ == "__main__":
    main()

