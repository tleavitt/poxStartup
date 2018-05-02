from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

# ./pox.py openflow.of_01 forwarding.topo_proactive openflow.discovery
class PROACTIVEPOX( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='./pox.py', cargs=('openflow.of_01 forwarding.topo_proactive openflow.discovery'), 
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
controllers={ 'proactive': PROACTIVEPOX }
