import topo_ft
import sys

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.openflow.nicira as nx
from pox.lib.util import dpidToStr
from pox.lib.addresses import IPAddr
from utils import *

middle = [
    [0, 0, 0, 0, 0, 0, 0, 2],
    [0, 0, 0, 8, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

ratio = [
    [0, 0, 0, 0, 0, 0, 0, 0.5],
    [0, 0, 0, 0.5, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


class install_direct(object):
    def __init__(self, topo):
        core.openflow.addListeners(self)
        self.topo = topo
        self.k = self.topo.k

    def _handle_ConnectionUp(self, event):
        name = topo_ft.dpid_to_name(event.dpid)
        dpid = event.dpid
        connection = event.connection
        self.install(connection, dpid, name)
        self.install_indirect(connection, dpid, name)

    def add_route(self, connection, ip, mask, port, priority=100):
        msg = nx.nx_flow_mod()
        msg.priority = priority
        msg.match.append(nx.NXM_OF_ETH_TYPE(0x800))
        msg.match.append(nx.NXM_OF_IP_DST(ip, mask))
        msg.actions.append(of.ofp_action_output(port=port))
        connection.send(msg)

    def add_indirect_route(self, connection, ip, src_ip, port, priority=200):
        print('indirect ' + ip + ' ' + src_ip + ' ' + str(port))
        msg = nx.nx_flow_mod()
        msg.priority = priority
        msg.match.append(nx.NXM_OF_ETH_TYPE(0x800))
        msg.match.append(nx.NXM_OF_IP_DST(ip, '255.255.255.0'))
        msg.match.append(nx.NXM_OF_IP_SRC(src_ip, "255.255.255.255"))
        msg.actions.append(of.ofp_action_output(port=port))
        connection.send(msg)
    
    def install(self, connection, dpid, name):
        print(name)
        n = int(name[name.find('s') + 1:])
        for switch in range(self.k ** 2 // 2):
            if switch != n:
                self.add_route(connection, '10.0.%d.0'%switch, '255.255.255.0', switch + 1)
        for host in range(self.k // 2):
            self.add_route(connection, '10.0.%d.%d'%(n, host + 2), '255.255.255.255', 1000 + host)


    def install_indirect(self, connection, dpid, name):
        n = int(name[name.find('s') + 1:])
        num = self.k ** 2 // 2
        for i in range(num):
            if middle[n][i] != 0:
                r = int(ratio[n][i] * self.k // 2)
                m = middle[n][i] - 1
                for host in range(r):
                    self.add_indirect_route(connection, '10.0.%d.0'%i, '10.0.%d.%d'%(n, host + 2),  m + 1)


def launch(num):
    topo = topo_ft.DirectTopo(int(num))

    core.registerNew(install_direct, topo)

    print('controller loaded')