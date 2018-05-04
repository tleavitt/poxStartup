from collections import defaultdict, deque
from jelly_graph import adjs_to_switch_map, create_regular_jellyfish_graph, create_irregular_jellyfish_graph
import random 
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

def build_path_map_ecmp(adjacency, path_map):

  for i in adjacency.keys():
    _ = ecmp_bfs(i, adjacency, path_map)
  return path_map

def ecmp_bfs(start, adjacency, path_map):

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
        # if it involves taking a new first hop, update
        # path_map.
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


def min_distance(src, dst, path_map):
  sort_dists = sorted(path_map[src][dst])
  return sort_dists[0] if len(sort_dists) > 0 else float('inf')

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

def test_efmp_bfs():
  N = 20; n = 8; r = 8
  print "Checking ecmp routing for irregular jellyfish with:"
  print "  n switches: {}, n hosts: {}, ports per swtch: {}".format(N, n, r)
  path_map = init_path_map()
  adjs = create_irregular_jellyfish_graph(N, n, r)
  switch_adjs = adjs_to_switch_map(adjs)

  # build shortest path tree.
  for i in range(N + n):
    _ = ecmp_bfs(i, switch_adjs, path_map)

  for i in range(N + n):
    for j in range(N + n):
      path_itoj = get_path(i, j, path_map)
      assert len(path_itoj) == min_distance(i, j, path_map) + 1
      assert check_path(path_itoj, switch_adjs)

  print "Check passed."


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
  test_efmp_bfs()