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
from mininet.util import quietRun, natural, custom
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from pox.lib.addresses import EthAddr

from subprocess import Popen
from time import sleep, time
from copy import copy
from json import dumps
import random
import re

from mininet.log import setLogLevel, info, warn, output

from mininet.log import setLogLevel
from mininet.clean import cleanup
from mininet.util import dumpNodeConnections

from jelly_graph import create_regular_jellyfish_graph, create_irregular_jellyfish_graph
import pdb

from pox.ext.config import ADJ_FILENAME, MAC_FILENAME, IS_SWITCH_FILENAME, IDPORT_FILENAME, PATHMAP_FILENAME
import cPickle as pickle

with open(ADJ_FILENAME, 'r+') as af:
  adjacency = pickle.load(af)

with open(IS_SWITCH_FILENAME, 'r+') as isf:
  is_switch = pickle.load(isf)

with open(IDPORT_FILENAME, 'r+') as idf:
  idport_map = pickle.load(idf)

# path map
with open(PATHMAP_FILENAME, 'r+') as pmf:
  our_path_map = pickle.load(pmf)

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

def int2dpid( dpid ):
   try:
      dpid = hex( dpid )[ 2: ]
      dpid = '0' * ( 16 - len( dpid ) ) + dpid
      return dpid
   except IndexError:
      raise Exception( 'Unable to derive default datapath ID - '
                       'please either specify a dpid or use a '
               'canonical switch name such as s23.' )
   # return int(dpid)

# Format is: most signifant byte: port number
#            least significant bytes: dpid
def dpid_port_to_mac(dpid, port):
    msb = port & 0xff
    lsbs = int(dpid) & 0x00FFffFFffFF
    eth_addr = (msb << 40) | lsbs
    return EthAddr("%012x" % eth_addr)




def buildJellyFishTopo(net, linkopts):
        nodes = {}
        for dpid in adjacency:
            if is_switch[dpid]:
                n = net.addSwitch('s{}'.format(int(dpid)), dpid=int2dpid(dpid))
                of_addr = dpid_port_to_mac(dpid, 1)
                n.config(mac=of_addr)
                n.intfList()[0].setMAC(of_addr)
            else:
                # n = net.addHost('h{}'.format(int(dpid)), pid=int(dpid))
                continue
            nodes[dpid] = n


        for dpid1, neighbors in adjacency.items():
            if not is_switch[dpid1]:
                continue

            for dpid2 in neighbors:
                if dpid1 > dpid2:
                    continue # Don't double add connections.

                if not is_switch[dpid2]:
                    continue

                port12 = adjacency[dpid1][dpid2]
                port21 = adjacency[dpid2][dpid1]
                addr1 = str(idport_map[(dpid1, port12)])
                addr2 = str(idport_map[(dpid2, port21)])

                n1 = nodes[dpid1]
                n2 = nodes[dpid2]
                net.addLink( n1, n2, port1 = port12, port2 = port21,
                    bw=linkopts['bw'])
                n1_intf, n2_intf = n1.connectionsTo(n2)[0]
                n1_intf.setMAC(addr1)
                n2_intf.setMAC(addr2)

class PrettyFloats( float ):
    def __repr__( self ):
        return '%.15g' % self

def prettyFloats( obj):
    "Beautify floats in dict/list/tuple data structure"
    if isinstance( obj, float ):
        return PrettyFloats( obj )
    elif isinstance( obj, dict ):
        return dict((k, prettyFloats(v)) for k, v in obj.items())
    elif isinstance( obj, ( list, tuple ) ):
        return map( prettyFloats, obj )
    return obj

def pct( x ):
    "pretty percent"
    return round(  x * 100.0, 2 )

def parseIntfStats( startTime, stats ):
    """Parse stats; return dict[intf] of (s, rxbytes, txbytes)
       and list of ( start, stop, user%... )"""
    spaces = re.compile('\s+')
    colons = re.compile( r'\:' )
    seconds = re.compile( r'(\d+\.\d+) seconds')
    intfEntries, cpuEntries, lastEntries = {}, [], []
    for line in stats.split( '\n' ):
        m = seconds.search(line)
        if m:
            s = round( float( m.group( 1 ) ) - startTime, 3 )
        elif '-eth' in line:
            line = spaces.sub( ' ', line ).split()
            intf = colons.sub( '', line[ 0 ] )
            rxbytes, txbytes = int( line[ 1 ] ), int( line[ 9 ] )
            intfEntries[ intf ] = intfEntries.get( intf, [] ) +  [
                    (s, rxbytes, txbytes ) ]
        elif 'cpu ' in line:
            line = spaces.sub( ' ', line ).split()
            entries = map( float, line[ 1 : ] )
            if lastEntries:
                dtotal = sum( entries ) - sum( lastEntries )
                if dtotal == 0:
                    raise Exception( "CPU was stalled from %s to %s - giving up" %
                                     ( lastTime, s ) )
                deltaPct = [ pct( ( x1 - x0 ) / dtotal ) 
                             for x1, x0 in zip( entries, lastEntries) ]
                interval = s - lastTime
                cpuEntries += [ [ lastTime, s ] + deltaPct ]
            lastTime = s
            lastEntries = entries

    return intfEntries, cpuEntries

def listening( src, dest, port=5001 ):
    "Return True if we can connect from src to dest on port"
    cmd = 'echo A | telnet -e A %s %s' % (dest.IP(), port)
    result = src.cmd( cmd )
    return 'Connected' in result

def remoteIntf( intf ):
    "Return other side of link that intf is connected to"
    link = intf.link
    return link.intf1 if intf == link.intf2 else link.intf2



def iperfPairs( opts, clients, servers ):
    "Run iperf semi-simultaneously one way for all pairs"
    pairs = len( clients )
    plist = zip( clients, servers )
    info( '*** Clients: %s\n' %  ' '.join( [ c.name for c in clients ] ) )
    info( '*** Servers: %s\n' %  ' '.join( [ c.name for c in servers ] ) )
    info( "*** Shutting down old iperfs\n")
    quietRun( "pkill -9 iperf" )
    info( "*** Starting iperf servers\n" )
    for dest in servers:
        dest.cmd( "iperf -s &" )
    info( "*** Waiting for servers to start listening\n" )
    for src, dest in plist:
        info( dest.name, '' )
        while not listening( src, dest ):
            info( '.' )
            sleep( .5 )
    info( '\n' )
    info( "*** Starting iperf clients\n" )
    for src, dest in plist:
        # packet size: 8 kB by default
        src.sendCmd( "sleep 1; iperf -t %s -i .5 -c %s -l %s" % (
            opts.time, dest.IP(), opts.pkt_size) )
    info( '*** Running cpu and packet count monitor\n' )
    startTime = int( time() )
    cmd = "./packetcount %s .5" % ( opts.time + 2 )
    stats = quietRun( cmd  )
    intfEntries, cpuEntries = parseIntfStats( startTime, stats )
    info( "*** Waiting for clients to complete\n" )
    results = []
    for src, dest in plist:
        result = src.waitOutput()
        dest.cmd( "kill -9 %iperf" )
        # Wait for iperf server to terminate
        dest.cmd( "wait" )
        # We look at the stats for the remote side of the destination's
        # default intf, as it is 1) now in the root namespace and easy to
        # read and 2) guaranteed by the veth implementation to have
        # the same byte stats as the local side (with rx and tx reversed,
        # naturally.)  Otherwise
        # we would have to spawn a packetcount process on each server
        for intf in dest.intfList()[1:]:
            intervals = intfEntries[ intf.name ]
            # Note: we are reversing txbytes and rxbytes to reflect
            # the statistics *at the destination*
            results += [ { 'dest': dest.name, 'intf': intf.name,
                        'destStats(seconds,txbytes,rxbytes)': intervals } ]
    return results, cpuEntries

def appendOutput( opts, totals ):
    "Append results as JSON to stdout or opts.outfile"
    info( '*** Dumping result\n' )
    f = open( opts.outfile, 'a' ) if opts.outfile else sys.stdout
    print >>f, dumps( prettyFloats( totals ) )
    if opts.outfile:
        f.close()

def initOutput( opts ):
    "Initialize an output file"
    name = opts.outfile
    f =  open( name, 'w') if name else sys.stdout
    print >>f, '# pair_intervals results'
    print >>f, dumps( opts.__dict__ )
    if name:
        f.close()

class Opts:
    counts = 1
    time = 20
    outfile = os.path.abspath('./iperf_results/ksp8_N50_n10_r10_lr15M_pkts8K')
    linkopts = dict(bw=15, delay='2ms', loss=0)
    pkt_size = '8K'


def runJellyfishLink():
    '''
    Create and run jellyfish network
    '''
    opts = Opts()
    net = Mininet(topo=None,
                build=False,
                host=CPULimitedHost, link=TCLink)
    net.addController('c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=6633) 
    buildJellyFishTopo(net, opts.linkopts)

    # print "Dumping switch connections"
    # dumpNodeConnections(net.switches)

    # dhcp_script = create_dhcp_file(topo)
    # pdb.set_trace()
    # for i, h in enumerate(net.hosts):
    #     h.cmd('dhclient eth0')

    # CLI(net, script=dhcp_script)
    # net.start()
    # CLI(net)
    # net.stop()
    results = []
    initOutput( opts )
    cpuHeader = ( 'cpu(start,stop,user%,nice%,sys%,idle%,iowait%,'
             'irq%,sirq%,steal%,guest%)' )
    for it in range(opts.counts):
        nodes = copy(net.switches)
        random.shuffle(nodes)
        clients = nodes[:len(nodes)/2]
        servers = nodes[len(nodes)/2:]

        net.start()
        intervals, cpuEntries = iperfPairs( opts, clients, servers )
        net.stop()
        # Write output incrementally in case of failure
        result = { 'it': it, 'results': intervals,
            cpuHeader: cpuEntries }
        appendOutput( opts, [ result ] )
        results.append(result)

    return results

def sanityCheck():
    "Make sure we have stuff we need"
    reqs = [ 'iperf', 'telnet', './packetcount' ]
    for req in reqs:
        if quietRun( 'which ' + req ) == '':
            print ( "Error: cannot find", req,
               " - make sure it is built and/or installed." )
            exit( 1 )

def main():
    cleanup()
    setLogLevel('info')
    sanityCheck()
    runJellyfishLink()

if __name__ == "__main__":
    main()

