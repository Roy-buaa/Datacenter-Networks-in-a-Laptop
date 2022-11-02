from topo_ft import FatTreeTopo, HierarchyTopo, DirectTopo

from mininet.node import RemoteController
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, warn, error, debug
from mininet.clean import cleanup
from subprocess import Popen, PIPE
import os
import sys
import atexit
import signal
import glob
from time import sleep
import utils

k = 4

def run_pox(controller_name):
	p_pox = Popen(
		['/home/mininet/pox/pox.py', 'fakearp', controller_name, '--num=%d'%k],
		# make pox ignore sigint so we can ctrl-c mininet stuff without killing pox
		preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
	)
	atexit.register(p_pox.kill)


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('parameters error!')
		sys.exit()

	topo_name = sys.argv[1]
	k = int(sys.argv[2])

	if topo_name == "hierarchy":
		run_pox('controller_dj')
		topo = HierarchyTopo(k)
	elif topo_name == "fattree":
		run_pox('controller_2level')
		topo = FatTreeTopo(k)
	else:
		print("topo not support")
		sys.exit()

	sleep(1)
	
	net = Mininet(topo, controller=RemoteController)

	net.start()

	sleep(3)

	CLI(net)
