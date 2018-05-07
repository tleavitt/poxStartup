#!/usr/bin/python
 
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf
from mininet.clean import cleanup
 
# sys.path.append("../../")
from proactive_pox import PROACTIVEPOX
from multi_pox import MULTIPOX
import pdb

def aggNet():
    cleanup()
    # CONTROLLER_IP='127.0.0.1'
 
    # net = Mininet( topo=None,
    #             build=False)
 
    # net.addController( 'c0',
    #                 controller=RemoteController,
    #                 ip=CONTROLLER_IP,
    #                 port=6633)

    net = Mininet( topo=None,
                build=False, controller=MULTIPOX)

    h1 = net.addHost( 'h1')
    h2 = net.addHost( 'h2')
    h3 = net.addHost( 'h3')
    h4 = net.addHost( 'h4')
    s1 = net.addSwitch( 's1' )
    s2 = net.addSwitch( 's2' )
    s3 = net.addSwitch( 's3' )
 
    pdb.set_trace()
    net.addLink( s1, s2 )
    net.addLink( s2, s3 )
 
    l = net.addLink( h1, s1 )
    net.addLink( h2, s1 )
    net.addLink( h3, s3 )
    net.addLink( h4, s3 )
 
    net.start()
    CLI( net )
    net.stop()
 
if __name__ == '__main__':
    setLogLevel( 'info' )
    aggNet()