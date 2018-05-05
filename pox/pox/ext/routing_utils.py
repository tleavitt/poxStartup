#!/usr/bin/python

''' 
Returns n_switches, n_hosts, k
for a given fat tree topology
'''
def fat_tree_size(k, n_hosts=None):
    if k == None:
        k = int(round((4 * n_hosts) ** (1. / 3)))
    if n_hosts == None:
        n_hosts = k**3 / 4

    n_core = (k/2)**2
    n_edge = k * (k/2)
    n_agg = k * (k/2)

    return n_core + n_edge + n_agg, n_hosts, k

def fat_tree_size2(k, n_hosts=None):
    if k == None:
        k = int(round((4 * n_hosts) ** (1. / 3)))
    if n_hosts == None:
        n_hosts = k**3 / 4

    n_agg = n_hosts / (k / 2)
    n_edge = n_hosts / (k / 2)
    n_core = (k/2)**2

    return n_core + n_edge + n_agg, n_hosts, k


if __name__ == '__main__':
    k = 48
    n_switches, n_hosts, _ = fat_tree_size(k)
    print "k: {}, n_switches: {}, n_hosts: {}".format(k, n_switches, n_hosts)

    n_hosts = 686
    n_switches, _, k = fat_tree_size(k=None, n_hosts=n_hosts)
    print "k: {}, n_switches: {}, n_hosts: {}".format(k, n_switches, n_hosts)

    n_hosts = 686
    n_switches, _, k = fat_tree_size2(k=None, n_hosts=n_hosts)
    print "k: {}, n_switches: {}, n_hosts: {}".format(k, n_switches, n_hosts)


# 686 hosts, k = 14, so in fat tree there are 7 hosts per switch.
# with Jellyfish, k = 14 and 7 hosts per switch means we need
# 686 / 7 = 98 switches, each with r = 14 ports and 
# 