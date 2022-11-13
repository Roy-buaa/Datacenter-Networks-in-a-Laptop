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
        host_num = k ** 3 // 4
        switch_num = k ** 2 // 2
        host_per_switch = k // 2
        switches = []
        self.k = k
        
        for i in range(switch_num):
            s = self.addSwitch('p0_s' + str(i), dpid=location_to_dpid(pod=0, switch=i))
            switches.append(s)
            for j in range(host_per_switch):
                h = self.addHost('p0_s' + str(i) + '_h' + str(j + 2),
                    ip='10.0.%d.%d'%(i, j + 2),
                    mac=location_to_mac(0, i, j + 2))
                self.addLink(s, h, 1000 + j, 1)
            
        for i in range(switch_num):
            for j in range(i + 1, switch_num):
                print(switches[j] + " port" + str(j + 1))
                self.addLink(switches[i], switches[j], j + 1, i + 1)


class NewDirectTopo(Topo):
    def __init__(self, k, switch_bw, host_bw):
        super(NewDirectTopo, self).__init__()
        host_num = k ** 3 // 4
        assert(host_num == len(host_bw))
        switch_num = k ** 2 // 2
        assert(switch_num == len(switch_bw))
        host_per_switch = k // 2
        switches = []
        self.k = k
        
        for i in range(switch_num):
            s = self.addSwitch('p0_s' + str(i), dpid=location_to_dpid(pod=0, switch=i))
            switches.append(s)
            for j in range(host_per_switch):
                h = self.addHost('p0_s' + str(i) + '_h' + str(j + 2),
                    ip='10.0.%d.%d'%(i, j + 2),
                    mac=location_to_mac(0, i, j + 2))
                self.addLink(s, h, 1000 + j, 1, bw=host_bw[i])
            
        for i in range(switch_num):
            for j in range(i + 1, switch_num):
                print(switches[j] + " port" + str(j + 1))
                self.addLink(switches[i], switches[j], j + 1, i + 1, bw=switch_bw[i][j])
