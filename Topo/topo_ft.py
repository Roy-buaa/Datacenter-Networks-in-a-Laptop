from mininet.topo import Topo
from utils import *
import re

class FatTreeTopo(Topo):
    def __init__(self, k):
        super(FatTreeTopo, self).__init__()

        self.k = k

        pods = [self.make_pod(i) for i in range(k)]

        for core_num in range((k // 2) ** 2):
            dpid = location_to_dpid(core=core_num)
            s = self.addSwitch('c_s%d'%core_num, dpid=dpid)

            stride_num = core_num // (k // 2)
            for i in range(k):
                self.addLink(s, pods[i][stride_num])

    
    def make_pod(self, pod_num):
        lower_layer_switches = [
            self.addSwitch('p%d_s%d'%(pod_num, i), dpid=location_to_dpid(pod=pod_num, switch=i))
            for i in range(self.k // 2)
        ]

        for i, switch in enumerate(lower_layer_switches):
            for j in range(2, self.k // 2 + 2):
                h = self.addHost('p%d_s%d_h%d'%(pod_num, i, j),
                    ip='10.%d.%d.%d'%(pod_num, i, j),
                    mac=location_to_mac(pod_num, i, j))
                self.addLink(switch, h)
        
        upper_layer_switches = [
            self.addSwitch('p%d_s%d'%(pod_num, i), dpid=location_to_dpid(pod=pod_num, switch=i))
            for i in range(self.k // 2, self.k)
        ]

        for lower in lower_layer_switches:
            for upper in upper_layer_switches:
                self.addLink(lower, upper)

        return upper_layer_switches


class HierarchyTopo(Topo):
    def __init__(self, k):
        super(HierarchyTopo, self).__init__()

        self.k = k

        pods = [self.make_pod(i) for i in range(k)]

        for core_num in range(k // 2):
            dpid = location_to_dpid(core=core_num)
            s = self.addSwitch('c_s%d'%core_num, dpid=dpid)

            for i in range(k):
                self.addLink(s, pods[i])

    
    def make_pod(self, pod_num):
        edges = [
            self.addSwitch('p%d_s%d'%(pod_num, i), dpid=location_to_dpid(pod=pod_num, switch=i))
            for i in range(self.k // 2)
        ]

        for i, switch in enumerate(edges):
            for j in range(2, self.k // 2 + 2):
                h = self.addHost('p%d_s%d_h%d'%(pod_num, i, j),
                    ip='10.%d.%d.%d'%(pod_num, i, j),
                    mac=location_to_mac(pod_num, i, j))
                self.addLink(switch, h)
                
        id = self.k // 2
        agg = self.addSwitch('p%d_s%d'%(pod_num, id), dpid=location_to_dpid(pod=pod_num, switch=id))

        for i, e in enumerate(edges):
            self.addLink(e, agg)

        return agg


class DirectTopo(Topo):
    def __init__(self, k):
        super(DirectTopo, self).__init__()
        self.k = k
        self.hosts = []
        self.switches = []
        for i in range(k):
            self.hosts.append(self.addHost('host' + str(k + 1)))
        for i in range(k):
            self.switches.append(self.addSwitch('switch' + str(k + 1)))
        for i in range(k):
            for j in range(i, k):
                self.addLink(self.switches[i], self.switches[j])