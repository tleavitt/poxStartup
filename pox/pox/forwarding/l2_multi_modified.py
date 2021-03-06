# Copyright 2012-2013 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A shortest-path forwarding application.

This is a standalone L2 switch that learns ethernet addresses
across the entire network and picks short paths between them.

You shouldn't really write an application this way -- you should
keep more state in the controller (that is, your flow tables),
and/or you should make your topology more static.  However, this
does (mostly) work. :)

Depends on openflow.discovery
Works with openflow.spanning_tree

Can copy-paste install path.

Consider projects like D-Cell, 
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.recoco import Timer
from collections import defaultdict
from pox.openflow.discovery import Discovery
from pox.lib.util import dpid_to_str
import time
import pdb

_dpid_to_str = lambda dpid: dpid_to_str(dpid)

#Define _select_path
import sys
sys.path.append("../../")
from pox.ext.routing_algorithms import possible_next_hops, get_path
from pox.ext.routing_algorithms import min_distance
from pox.ext.routing_algorithms import ecmp_path_builder, ksp_path_builder, init_path_map
from pox.ext.config import ADJ_FILENAME, MAC_FILENAME, PATHMAP_FILENAME
import cPickle as pickle

log = core.getLogger()

# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
# adjacency = defaultdict(lambda:defaultdict(lambda:None))
with open(ADJ_FILENAME, 'r+') as af:
  adjacency = pickle.load(af)

# Switches we know of.  [dpid] -> Switch
switches = {}

# ethaddr -> (dpid, port)
with open(MAC_FILENAME, 'r+') as mf:
  mac_map = pickle.load(mf)

# path map
with open(PATHMAP_FILENAME, 'r+') as pmf:
  our_path_map = pickle.load(pmf)

# Select a routing algorithm:
build_path_map = ecmp_path_builder(8) 

# Waiting path.  (dpid,xid)->WaitingPath
waiting_paths = {}

# Time to not flood in seconds
FLOOD_HOLDDOWN = 5

# Flow timeouts
FLOW_IDLE_TIMEOUT = 10
FLOW_HARD_TIMEOUT = 30

# How long is allowable to set up a path?
PATH_SETUP_TIME = 30



def _check_path (p):
  """
  Make sure that a path is actually a string of nodes with connected ports

  returns True if path is valid
  """
  for a,b in zip(p[:-1],p[1:]):
    if adjacency[a[0]][b[0]] != a[2]:
      return False
    if adjacency[b[0]][a[0]] != b[1]:
      return False
  return True


def _our_get_path (src, dst, first_port, final_port):
  """
  Gets a cooked path -- a list of (node,in_port,out_port)
  """
  # Start with a raw path...
  if len(our_path_map) == 0: 
    build_path_map(adjacency, our_path_map)

  path = get_path(src, dst, our_path_map)
  if path is None:
    return None

  # Now add the ports and switches?
  r = []
  in_port = first_port

  for dpid1, dpid2 in zip(path[:-1],path[1:]):

    out_port = adjacency[dpid1][dpid2]

    r.append((switches[dpid1], in_port, out_port))

    in_port = adjacency[dpid2][dpid1]

  r.append((switches[dst], in_port, final_port))

  assert _check_path(r), "Illegal path!"

  return r


class WaitingPath (object):
  """
  A path which is waiting for its path to be established
  """
  def __init__ (self, path, packet):
    """
    xids is a sequence of (dpid,xid)
    first_switch is the DPID where the packet came from
    packet is something that can be sent in a packet_out
    """
    self.expires_at = time.time() + PATH_SETUP_TIME
    self.path = path
    self.first_switch = switches[path[0][0]].dpid
    self.xids = set()
    self.packet = packet

    if len(waiting_paths) > 1000:
      WaitingPath.expire_waiting_paths()

  def add_xid (self, dpid, xid):
    self.xids.add((dpid,xid))
    waiting_paths[(dpid,xid)] = self

  @property
  def is_expired (self):
    return time.time() >= self.expires_at

  def notify (self, event):
    """
    Called when a barrier has been received
    """
    self.xids.discard((event.dpid,event.xid))
    if len(self.xids) == 0:
      # Done!
      if self.packet:
        log.info("Sending delayed packet out %s"
                  % (_dpid_to_str(self.first_switch),))
        msg = of.ofp_packet_out(data=self.packet,
            action=of.ofp_action_output(port=of.OFPP_TABLE))
        core.openflow.sendToDPID(self.first_switch, msg)

      core.l2_multi.raiseEvent(PathInstalled(self.path))


  @staticmethod
  def expire_waiting_paths ():
    packets = set(waiting_paths.values())
    killed = 0
    for p in packets:
      if p.is_expired:
        killed += 1
        for entry in p.xids:
          waiting_paths.pop(entry, None)
    if killed:
      log.error("%i paths failed to install" % (killed,))


class PathInstalled (Event):
  """
  Fired when a path is installed
  """
  def __init__ (self, path):
    Event.__init__(self)
    self.path = path


class Switch (EventMixin):
  def __init__ (self):
    self.connection = None
    self.ports = None
    self.dpid = None
    self._listeners = None
    self._connected_at = None

  def __repr__ (self):
    return _dpid_to_str(self.dpid)

  def _install (self, switch, in_port, out_port, match, buf = None):
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.match.in_port = in_port
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    msg.actions.append(of.ofp_action_output(port = out_port))
    msg.buffer_id = buf
    if switch.connection == None:
	print "in install, switch dpid = ", switch.dpid 
    switch.connection.send(msg)

  def _install_path (self, p, match, packet_in=None):
    wp = WaitingPath(p, packet_in)
    for sw,in_port,out_port in p:
      self._install(sw, in_port, out_port, match)
      msg = of.ofp_barrier_request()
      sw.connection.send(msg)
      wp.add_xid(sw.dpid,msg.xid)

  def install_path (self, dst_sw, last_port, match, event):
    """
    Attempts to install a path between this switch and some destination
    """
    # p = _get_path(self.dpid, dst_sw.dpid, event.port, last_port)
    # log.info("their path: %s", str(p))
    our_p = _our_get_path(self.dpid, dst_sw.dpid, event.port, last_port)
    log.info("our path: %s", str(our_p))

    # if p is not None and our_p is None:
    #   pdb.set_trace()

    # for n1, n2 in zip(p, our_p):
    #   assert n1 == n2
    p = our_p
    if p is None:
      log.warning("Can't get from %s to %s", match.dl_src, match.dl_dst)

      import pox.lib.packet as pkt

      if (match.dl_type == pkt.ethernet.IP_TYPE and
          event.parsed.find('ipv4')):
        # It's IP -- let's send a destination unreachable
        log.info("Dest unreachable (%s -> %s)",
                  match.dl_src, match.dl_dst)

        from pox.lib.addresses import EthAddr
        e = pkt.ethernet()
        e.src = EthAddr(_dpid_to_str(self.dpid)) #FIXME: Hmm...
        e.dst = match.dl_src
        e.type = e.IP_TYPE
        ipp = pkt.ipv4()
        ipp.protocol = ipp.ICMP_PROTOCOL
        ipp.srcip = match.nw_dst #FIXME: Ridiculous
        ipp.dstip = match.nw_src
        icmp = pkt.icmp()
        icmp.type = pkt.ICMP.TYPE_DEST_UNREACH
        icmp.code = pkt.ICMP.CODE_UNREACH_HOST
        orig_ip = event.parsed.find('ipv4')

        d = orig_ip.pack()
        d = d[:orig_ip.hl * 4 + 8]
        import struct
        d = struct.pack("!HH", 0,0) + d #FIXME: MTU
        icmp.payload = d
        ipp.payload = icmp
        e.payload = ipp
        msg = of.ofp_packet_out()
        msg.actions.append(of.ofp_action_output(port = event.port))
        msg.data = e.pack()
        self.connection.send(msg)

      return

    log.info("Installing path for %s -> %s %04x (%i hops)",
        match.dl_src, match.dl_dst, match.dl_type, len(p))
    # log.info("path: %s", str(p))

    # We have a path -- install it
    self._install_path(p, match, event.ofp)

    # Now reverse it and install it backwards
    # (we'll just assume that will work)
    p = [(sw,out_port,in_port) for sw,in_port,out_port in p]
    self._install_path(p, match.flip())


  def _handle_PacketIn (self, event):
    def flood ():
      """ Floods the packet """
      if self.is_holding_down:
        log.warning("Not flooding -- holddown active")
      msg = of.ofp_packet_out()
      # OFPP_FLOOD is optional; some switches may need OFPP_ALL
      msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      msg.buffer_id = event.ofp.buffer_id
      msg.in_port = event.port
      self.connection.send(msg)

    def drop ():
      # Kill the buffer
      if event.ofp.buffer_id is not None:
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        event.ofp.buffer_id = None # Mark is dead
        msg.in_port = event.port
        self.connection.send(msg)
	
    packet = event.parsed

    loc = (self.dpid, event.port) # Place we saw this ethaddr
    oldloc = mac_map.get(packet.src) # Place we last saw this ethaddr

    if packet.effective_ethertype == packet.LLDP_TYPE:
      drop()
      return

    if oldloc is None:
      if packet.src.is_multicast == False:
        # mac_map[packet.src] = loc # Learn position for ethaddr
        log.info("Unecpected mac: %s at %s.%i", packet.src, loc[0], loc[1])
    elif oldloc != loc:
      # ethaddr seen at different place!
      if core.openflow_discovery.is_edge_port(switches[loc[0]].dpid, loc[1]):
        # New place is another "plain" port (probably)
        pass
        # log.info("%s moved from %s.%i to %s.%i?", packet.src,
        #           _dpid_to_str(switches[oldloc[0]].dpid), oldloc[1],
        #           _dpid_to_str(switches[loc[0]].dpid),    loc[1])
        if packet.src.is_multicast == False:
          # mac_map[packet.src] = loc # Learn position for ethaddr
          # log.info("Learned %s at %s.%i", packet.src, loc[0], loc[1])
          pass
      elif packet.dst.is_multicast == False:
        # New place is a switch-to-switch port!
        # Hopefully, this is a packet we're flooding because we didn't
        # know the destination, and not because it's somehow not on a
        # path that we expect it to be on.
        # If spanning_tree is running, we might check that this port is
        # on the spanning tree (it should be).
        if packet.dst in mac_map:
          # Unfortunately, we know the destination.  It's possible that
          # we learned it while it was in flight, but it's also possible
          # that something has gone wrong.
          log.warning("Packet from %s to known destination %s arrived "
                      "at %s.%i without flow", packet.src, packet.dst,
                      _dpid_to_str(self.dpid), event.port)

    if packet.dst.is_multicast:
      log.info("Got multicast from %s, ignoring", packet.src)
      # flood()
    else:
      if packet.dst not in mac_map:
        log.info("%s unknown -- dropping" % (packet.dst,))
        # flood()
      else:
        dest_dpid, dest_port = mac_map[packet.dst]
        match = of.ofp_match.from_packet(packet)
        self.install_path(switches[dest_dpid], dest_port, match, event)

  def disconnect (self):
    if self.connection is not None:
      log.info("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None

  def connect (self, connection):
    if self.dpid is None:
      self.dpid = connection.dpid
    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    log.info("Connect %s" % (connection,))
    self.connection = connection
    self._listeners = self.listenTo(connection)
    self._connected_at = time.time()


  @property
  def is_holding_down (self):
    if self._connected_at is None: return True
    if time.time() - self._connected_at > FLOOD_HOLDDOWN:
      return False
    return True

  def _handle_ConnectionDown (self, event):
    self.disconnect()


class l2_multi (EventMixin):

  _eventMixin_events = set([
    PathInstalled,
  ])

  def __init__ (self):
    # Listen to dependencies
    def startup ():
      core.openflow.addListeners(self, priority=0)
      core.openflow_discovery.addListeners(self)
    core.call_when_ready(startup, ('openflow','openflow_discovery'))

  def _handle_LinkEvent (self, event):
    print "_handle_LinkEvent!"
    def flip (link):
      return Discovery.Link(link[2],link[3], link[0],link[1])

    l = event.link
    sw1 = switches[l.dpid1]
    sw2 = switches[l.dpid2]



    # Invalidate all flows and path info.
    # For link adds, this makes sure that if a new link leads to an
    # improved path, we use it.
    # For link removals, this makes sure that we don't use a
    # path that may have been broken.
    #NOTE: This could be radically improved! (e.g., not *ALL* paths break)

    if event.removed:
      # This link no longer okay
      return
    else:
      # check that adjacency has been pre-populated correctly.
      assert adjacency[sw1.dpid][sw2.dpid] == l.port1
      assert adjacency[sw2.dpid][sw1.dpid] == l.port2

      return

  def _handle_ConnectionUp (self, event):
    sw = switches.get(event.dpid)
    if sw is None:
      # New switch
      sw = Switch()
      switches[event.dpid] = sw
      sw.connect(event.connection)
      print "Connecting if, dpid= ", event.dpid
    else:
      print "Connecting else, dpid = ", event.dpid
      sw.connect(event.connection)

  def _handle_BarrierIn (self, event):
    wp = waiting_paths.pop((event.dpid,event.xid), None)
    if not wp:
      log.info("No waiting packet %s,%s", event.dpid, event.xid)
      return
    log.info("Notify waiting packet %s,%s", event.dpid, event.xid)
    wp.notify(event)


def launch (): 
  core.registerNew(l2_multi)

  timeout = min(max(PATH_SETUP_TIME, 5) * 2, 15)
  Timer(timeout, WaitingPath.expire_waiting_paths, recurring=True)
