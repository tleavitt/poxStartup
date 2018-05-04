#!/usr/bin/python
import sys
from collections import defaultdict, deque
from jelly_graph import adjs_to_switch_map, create_regular_jellyfish_graph, create_irregular_jellyfish_graph
import random 
import time
import pdb

# [sw1][sw2] -> {distance: [possible next hops from sw1] }
def init_path_map():
    return defaultdict(
      lambda:defaultdict(
        lambda:defaultdict(
          lambda:(float('inf'),[])
        )
      )
    )

def min_distance(src, dst, path_map):
  sort_dists = sorted(path_map[src][dst])
  return sort_dists[0] if len(sort_dists) > 0 else float('inf')

'''
ECMP multipath routing algorithms
'''
def ecmp_path_builder(kway=8):

  def build_path_map(adjacency, path_map):

    for i in adjacency.keys():
      _ = ecmp_bfs(i, adjacency, path_map, kway=kway)
    return path_map

  return build_path_map

build_path_map_ecmp8 = ecmp_path_builder(8)
build_path_map_ecmp64 = ecmp_path_builder(64)

def ecmp_bfs(start, adjacency, path_map, kway=8):
  '''
  Compute the ECMP routes from `start` to
  all other nodes in the graph `adjacency`,
  storing the results in path_map.
  kway is the maximum number of first hops
  to consider from one port to another.
  '''

  paths_from_start = path_map[start]

  distances = lambda sw: paths_from_start[sw]
  def min_dist(sw):
    sort_dists = sorted(distances(sw))
    return sort_dists[0] if len(sort_dists) > 0 else float('inf')
  visited = lambda sw: len(distances(sw)) > 0

  # frontier are the switches we are ready to process, 
  # values are (switch, 
  #             dist to start along this path, 
  #             next hop from start to get to this node.)
  paths_from_start[start] = {0: []}
  frontier = deque((
    (sw, 1, sw) for sw in adjacency[start].keys()
  ))

  while len(frontier) > 0:
    cur, dist, hop_start = frontier.popleft()

    if visited(cur):
      # someone beat us to the switch.
      md = min_dist(cur)
      assert dist >= md
      if dist == md:
        # we found a new path to get from start to cur.
        # in k-way ECMP, we consider only k parallel routes
        # from any src to dst.
        if len(paths_from_start[cur][dist]) >= kway:
          continue
        # else, if new path involves taking a new first hop,
        # update path_map.
        if hop_start not in paths_from_start[cur][dist]:
          paths_from_start[cur][dist].append(hop_start)
    else:
      # this is the first time we've visited this node.
      paths_from_start[cur][dist]= [hop_start]
      unvisited_neighbors = (sw for sw in adjacency[cur].keys() if not visited(sw))
      frontier.extend((
        (sw, dist + 1, hop_start) for sw in unvisited_neighbors
      ))

  # path_map[start] = paths_from_start
  return paths_from_start


def get_raw_path(src, dst, path_map):
  """
  Get a __random__ raw path (just a list of nodes to traverse)
  """

  dist = min_distance(src, dst, path_map)
  if dist == float('inf'):
    return None
  next_hops = path_map[src][dst][dist]
  if len(next_hops) == 0:
    # we're here!
    return []
  assert len(next_hops) > 0
  next_hop = random.choice(next_hops)

  return [next_hop] + get_raw_path(next_hop, dst, path_map)


def get_path(src, dst, path_map):

  # Start with a raw path...
  path = get_raw_path(src, dst, path_map)
  if path is None:
    return None
  else:
    return [src] + path

def test_routing_alg(path_builder=ecmp_path_builder):
  N = 245; n = 686; r = 14
  print "Checking ecmp routing for irregular jellyfish with:"
  print "  n switches: {}, n hosts: {}, ports per swtch: {}".format(N, n, r)
  path_map = init_path_map()
  adjs = create_irregular_jellyfish_graph(N, n, r)
  switch_adjs = adjs_to_switch_map(adjs)

  # build shortest path tree.
  print "Building path map...",
  sys.stdout.flush()
  start = time.time()

  path_builder()(switch_adjs, path_map)

  print "done. (took {} s)".format(time.time() - start) 

  print "Checking all paths...",
  sys.stdout.flush()
  start = time.time()
  for i in range(N + n):
    for j in range(N + n):
      path_itoj = get_path(i, j, path_map)
      assert len(path_itoj) == min_distance(i, j, path_map) + 1
      assert check_path(path_itoj, switch_adjs)

  print "check passed. (took {} s)".format(time.time() - start) 


def check_path (p, switch_adjs):
  """
  Make sure that a path is actually a string of connected nodes.

  returns True if path is valid
  """
  for i in range(len(p) - 1):
    s, d = p[i], p[i+1] 
    if d not in switch_adjs[s]:
      return False
    if s not in switch_adjs[d]:
      return False
  return True

if __name__ == '__main__':
  test_routing_alg()
  