import os
import sys
sys.path.append("../../")
import pox.ext
path = os.path.abspath(os.path.dirname(pox.ext.__file__))

ADJ_FILENAME = os.path.abspath('{}/topo_config/adjacency.pkl'.format(path))
IS_SWITCH_FILENAME = os.path.abspath('{}/topo_config/is_switch.pkl'.format(path))
MAC_FILENAME = os.path.abspath('{}/topo_config/mac_map.pkl'.format(path))
IDPORT_FILENAME = os.path.abspath('{}/topo_config/idport_map.pkl'.format(path))
PATHMAP_FILENAME = os.path.abspath('{}/topo_config/our_path_map.pkl'.format(path))