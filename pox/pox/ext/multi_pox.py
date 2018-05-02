from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class MULTIPOX( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='./pox.py', cargs=('openflow.of_01 forwarding.l2_multi openflow.discovery'), 
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
controllers={ 'multi': MULTIPOX }
