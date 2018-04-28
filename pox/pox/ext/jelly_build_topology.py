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


class JellyfishTopo( Topo ):
    '''
    Jellyfish topology with multiple links
    '''
    def __init__( self, N=20, k=12, r=4, verbose=False, **kwargs ):
        Topo.__init__( self, **kwargs )
        self.N = N; self.k = k; self.r = r
        adjs = create_jellyfish_graph(N, k, r)

        switches = [self.addSwitch('s{}'.format(i)) for i in range(N)]
        servers = [
            [self.addHost('h{}_{}'.format(i, j)) for j in range(r)]
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


def runJellyfishLink():
    '''
    Create and run jellyfish network
    '''
    # topo = JellyfishTopo(N=4, k=4, r=1, verbose=True)
    topo = JellyfishTopo(N=3, k=3, r=1, verbose=True)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    print "Dumping node connections"
    dumpNodeConnections(net.hosts)
    net.start()
    net.pingAll()
    net.stop()

def main():
    cleanup()
    setLogLevel('info')
    runJellyfishLink()

if __name__ == "__main__":
    main()

