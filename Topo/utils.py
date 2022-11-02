import re

def location_to_dpid(core=None, pod=None, switch=None):
    if core is not None:
        return '0000000010%02x0000'%core
    else:
        return'000000002000%02x%02x'%(pod, switch)

def pod_name_to_location(name):
    match = re.match('p(\d+)_s(\d+)', name)
    pod, switch = match.group(1, 2)
    return int(pod), int(switch)

def is_core(dpid):
    return ((dpid & 0xFF000000) >> 24) == 0x10

def dpid_to_name(dpid):
    if is_core(dpid):
        core_num = (dpid & 0xFF0000) >> 16
        return 'c_s%d'%core_num
    else:
        pod = (dpid & 0xFF00) >> 8
        switch = (dpid & 0xFF)
        return 'p%d_s%d'%(pod, switch)

def host_to_ip(name):
    match = re.match('p(\d+)_s(\d+)_h(\d+)', name)
    pod, switch, host = match.group(1, 2, 3)
    return '10.%s.%s.%s'%(pod, switch, host)

def ip_to_mac(ip):
    match = re.match('10.(\d+).(\d+).(\d+)', ip)
    pod, switch, host = match.group(1, 2, 3)
    return location_to_mac(int(pod), int(switch), int(host))

def location_to_mac(pod, switch, host):
    return '00:00:00:%02x:%02x:%02x'%(pod, switch, host)