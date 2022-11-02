from cgitb import reset
from fileinput import filename
import readline
from mininet.topo import Topo,MinimalTopo,LinearTopo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import Controller

# import _thread
import time
import random
import re

logDirPath = "/home/mininet/mininet/myproject/log/"

class TestTopo( Topo ):
    def build( self, k=2 ):
        "k: number of hosts"
        self.k = k
        switch = self.addSwitch( 's1' )
        for h in range( 0, k ):
            host = self.addHost( 'h-%s' % h )
            self.addLink( host, switch,
                          port1=0, port2=( k - h + 1 ) )

slience = False
def myLog(s):
    if slience is False:
        print(s)

def cleanFile(fileName):
    with open(logDirPath + fileName,"a+") as f:
        f.seek(0)
        f.truncate()

class TestNet(object):

    # seed : rand(seed)
    def __init__(self,topo):
        self.topo = topo
        self.net = Mininet(topo = topo)
        self.hostNum = len(self.net.hosts)
        self.serverNumSet = set()
        self.clientNumSet = set()
        # self.inBw = [ [0.]*self.hostNum for _ in range(0,self.hostNum)]
        # self.outBw = [ [0.]*self.hostNum for _ in range(0,self.hostNum)]
        
        self.chosedMat = [[False]* self.hostNum for _ in range(self.hostNum)]
        self.chosed = [ False for _ in range(self.hostNum) ]

        for i in range(self.hostNum):
            self.chosedMat[i][i] = True

        self.outBwMat = [[0]* self.hostNum for _ in range(self.hostNum)]
        self.outBwCount = [[0]*self.hostNum for _ in range(self.hostNum)]
        # self.outBwLock = threading.Lock()
        self.inBwMat = [[0]*self.hostNum for _ in range(self.hostNum)]
        self.inBwCount = [[0]*self.hostNum for _ in range(self.hostNum)]
        # self.inBwLock = threading.Lock()

    def iperf_single( self,hosts=None, udpBw='10M', period=5, port=5001,format='k'):
        """Run iperf between two hosts using UDP.
           hosts: list of hosts; if None, uses opposite hosts
           returns: results two-element array of server and client speeds"""
        if not hosts:
            return
        else:
            assert len( hosts ) == 2
        client, server = hosts
        filename = client.name[1:] + '.out'
        myLog( '*** Iperf: testing bandwidth between ' )
        myLog( "%s and %s\n" % ( client.name, server.name ) )
        iperfArgs = 'iperf -u '
        bwArgs = '-b ' + udpBw + ' '
        myLog ("***start server***")
        serverHostNum = (int)(server.name[2:])
        serverFileName = 'server%s.out' % server.name[1:]
        if  serverHostNum not in self.serverNumSet:
            cleanFile(serverFileName)
            self.serverNumSet.add(serverHostNum)
        server.cmd( 'iperf -u ' + '-s ' + '-f %c ' % format  + ' -p %d ' % port  + ' >> ' + logDirPath + serverFileName + ' &')
        time.sleep(1)
        myLog ("***start client***")
        clientHostNum = (int)(client.name[2:])
        clientFileName = 'client%s.out' % client.name[1:]
        if clientHostNum not in self.clientNumSet:
            cleanFile(clientFileName)
            self.clientNumSet.add(clientHostNum)
        client.cmd(
            iperfArgs + ' -p %d ' % port + '-f %c ' % format  +' -t '+ str(period) + ' -c ' + server.IP() + ' ' + bwArgs
            +' >> ' + logDirPath + clientFileName +' &')

    def iperfMulti(self, bw, period=5,format='k'):
        # random.seed(time.time())
        base_port = 5001
        server_list = []
        client_list = [h for h in self.net.hosts]
        host_list = []
        host_list = [h for h in self.net.hosts]

        cli_outs = []
        ser_outs = []

        _len = len(host_list)
        for i in range(0, _len):
            client = host_list[i]
            server = self.choose(i)
            server_list.append(server)
            self.iperf_single(hosts = [client, server], udpBw=bw, period= period, port=base_port,format=format)
            time.sleep(.05)
            base_port += 1
        self.net.hosts[0].cmd('ping -c10'+ self.net.hosts[-1].IP() + ' > '+ logDirPath +'delay.out')

    """ def hostIperf(self,clientHostNum,startTime,lastTime,bw='10M',port=5001):
        # TEST
        # clientHost = self.net.getNodeByName('h%d' % clientHostNum)
        clientHost = self.net['h-%d' % clientHostNum]
        remainTime = lastTime - (time.time() - startTime)
        serverHostNum = 0
        while(remainTime >= 1):
            # serverHostNum = random.randint(1,self.hostNum)
            serverHostNum = random.randint(0,self.hostNum-1)
            while (serverHostNum == clientHostNum):
                # serverHostNum = random.randint(1,self.hostNum)
                serverHostNum = random.randint(0,self.hostNum-1)
            # serverHost = self.net.getNodeByName('h%d' % serverHostNum)
            serverHost = self.net['h-%d' % serverHostNum]
            hosts = (clientHost,serverHost)
            seconds = random.uniform(1,remainTime)
            myLog("Log--randomTest: h%d -> h%d , bw-%s time-%ds\n"% (clientHostNum,serverHostNum,bw,seconds))
            clientHost.cmd('telnet',serverHost.IP(),'5001')
            s = self.net.iperf(hosts,l4Type='UDP',udpBw=bw,seconds=seconds)
            serverBw = parseBw(s[1])
            clientBw = parseBw(s[2])
            myLog("Log--randomTest: h%d -> h%d , cliBw-%fkb/s serBw-%fkb/s\n"%(clientHostNum,serverHostNum,clientBw,serverBw))

            self.outBwLock.acquire(blocking=True)
            self.outBwMat[clientHostNum][serverHostNum] += clientBw
            self.outBwCount[clientHostNum][serverHostNum] += 1
            self.outBwLock.release()

            self.inBwLock.acquire(blocking = True)
            self.inBwMat[clientHostNum][serverHostNum] += serverBw
            self.inBwCount[clientHostNum][serverHostNum] += 1
            self.inBwLock.release()

            remainTime = lastTime - (time.time() - startTime)
        
        myLog("Log--randomTest: h%d -> h%d , finished\n"%(clientHostNum,serverHostNum)) """

    def getRandom(self,clientHostNum):
        i = random.randint(0,self.hostNum-1)
        while i == clientHostNum:
            i = random.randint(0,self.hostNum-1)
        return self.net.hosts[i]

    def choose(self,clientHostNum):
        if self.chosed[clientHostNum] == True:
            return self.getRandom(clientHostNum)
        
        res = 0
        for i in range(self.hostNum):
            if self.chosedMat[clientHostNum][i] == False:
                self.chosedMat[clientHostNum][i] = True
                return self.net.hosts[i]

        self.chosed[clientHostNum] = True
        return self.getRandom(clientHostNum)

    # each host randomly sends packet to another host
    # bw : bandWith , default 10M
    # slot : one host will send packet to another fixed host in a slot
    # slot default : [testTime / 10,testTime / 5] second
    def randomTest(self,testTime,bw='10M',format='k'):
        # the vars needed to be inited every test
        self.serverNumSet = set()
        self.clientNumSet = set()
        self.id2hostNum = {}
        port = 5001

        startTime = time.time()
        self.net.start()  
        self.iperfMulti(bw,testTime,format=format)
        time.sleep(testTime+self.hostNum*1+1)
        myLog("Log--randomTest: Iperf finised\n")
        myLog("Log--randomTest: Parsing clients' files......\n")
        self.parseResult()
        myLog("Log--randomTest: Parsing finished !!!\n")


            # self.hostIperf(i,startTime,testTime,bw)
            # try:
            #     _thread.start_new_thread(self.hostIperf,(i,startTime,testTime,bw))
            # except Exception:
            #     print("Error--randTest: client h-%d can't run a thread\n" % i)
            #     traceback.print_exc()
            # else:
            #     myLog("Log--randTest: client h-%d run a thread sucessfully!\n" % i)
            
        # time.sleep(testTime + 2)

        """ self.net.stop()
        self.outBwLock.acquire(blocking = True)
        self.inBwLock.acquire(blocking = True)
        for i in range(0,self.hostNum):
            for j in range(0,self.hostNum):
                if self.outBwCount[i][j] != 0:
                    self.outBwMat[i][j] /= self.outBwCount[i][j]
                if self.inBwCount[i][j] != 0:
                    self.inBwMat[i][j] /= self.inBwCount[i][j]
        self.inBwLock.release()
        self.outBwLock.release() """
        # return [self.outBwMat,self.inBwMat]

    def parseHead(self,s):
        headPat = r'Client connecting'
        if re.search(headPat,s):
            return True
        else:
            return False

    def parseServerReport(self,s):
        serReportPat = r'Server Report'
        if re.search(serReportPat,s):
            return True
        else:
            return False

    def parseClientSignalLine(self,s,id2hostNum):
        idPat = r'\[\s*([\d]+)\]'
        serIpPat = r'with\s*\d+\.\d+\.\d+\.(\d+)'
        id_ = re.match(idPat,s)
        id,srchostNum = 0,0
        if id_:
            id = int(id_.group(1))
        else:
            return
        serIp_ = re.search(serIpPat,s)
        if serIp_:
            srchostNum = int(serIp_.group(1))-1
        else:
            return
        id2hostNum[id] = srchostNum
        return

    def parseClientBwLine(self,s,clientHostNum,id2hostNum,isServerPart):
        idPat = r'\[\s*([\d]+)\]'
        bwPat = r'([\d\.]+) \w+/sec'
        id_ = re.match(idPat,s)
        id = 0
        bw = 0.
        if id_:
            id = int(id_.group(1))
        else:
            return
        bw_ = re.search(bwPat,s)
        if bw_:
            bw = float(bw_.group(1))
        else:
            return
        # this part belong to client report
        if not isServerPart:
            self.outBwMat[clientHostNum][id2hostNum[id]] += bw
            self.outBwCount[clientHostNum][id2hostNum[id]] += 1
        else:
            # this part belong to server report
            self.inBwMat[clientHostNum][id2hostNum[id]] += bw
            self.inBwCount[clientHostNum][id2hostNum[id]] += 1
        return 

    def parseClientFileBw(self,fileName,clientHostNum):
        isServerPart = False
        id2hostNum = {}
        with open(logDirPath + fileName,'r') as f:
            for line in f:
                # reset the reading status
                if self.parseHead(line):
                    id2hostNum = {}
                    isServerPart = False
                isServerPart = isServerPart or self.parseServerReport(line)
                self.parseClientSignalLine(line,id2hostNum)
                self.parseClientBwLine(line,clientHostNum,id2hostNum,isServerPart)
        return
    

    def parseResult(self):
        for clientHostNum in self.clientNumSet:
            fileName = "client-%d.out" % clientHostNum
            myLog("LOG--randomTest: Parsing %s\n" % fileName)
            self.parseClientFileBw(fileName,clientHostNum)
    
    # Output: mat[client][server] -> 
    # The average output bandwidth of the client when sending to the server
    def getOutBwMat(self):
        res = [ [0.]*self.hostNum for _ in range(0,self.hostNum)]
        for i in range(self.hostNum):
            for j in range(self.hostNum):
                if self.outBwCount[i][j] != 0:
                    res[i][j] = self.outBwMat[i][j] / self.outBwCount[i][j]
        return res
    
    # Output: mat[client][server] -> 
    # The average input bandwidth of the server when receiving from the client
    def getInBwMat(self):
        res = [ [0.]*self.hostNum for _ in range(0,self.hostNum)]
        for i in range(self.hostNum):
            for j in range(self.hostNum):
                if self.inBwCount[i][j] != 0:
                    res[i][j] = self.inBwMat[i][j] / self.inBwCount[i][j]
        return res

class FatTreeTopo(Topo):

# build a fat tree topo of size k
    def __init__(self, k):
        assert(k <= 48)
        self.k = k
        self.core_switch = []
        self.agg_switch = []
        self.edge_switch = []
        self.host = []
        super(FatTreeTopo, self).__init__()
        self.build()

    def build(self):
        for i in range(self.k ** 2 // 4):
            self.core_switch.append(self.addSwitch('cs-' + str(i)))
        for i in range(self.k ** 3 // 4):
            self.host.append(self.addHost('h-' + str(i)))
            # self.host.append(self.addHost('h' + str(i)))
        for i in range(self.k):
            self.makePod(i)
        for pod_num in range(self.k // 2):
            for pod_seq in range(self.k // 2):
                for conn_num in range(self.k // 2):
                    self.addLink(self.agg_switch[pod_num][pod_seq], self.core_switch[pod_seq * (self.k // 2) + conn_num])

    def makePod(self, num):
        agg_switchs = []
        edge_switchs = []
        for i in range(self.k // 2):
            agg_switchs.append(self.addSwitch('as-' + str(num) + '-' + str(i)))
            edge_switchs.append(self.addSwitch('es-' + str(num) + '-' + str(i)))
        for i in range(self.k // 2):
            for j in range(self.k // 2):
                self.addLink(agg_switchs[i], edge_switchs[j])
        start = (self.k // 2) ** 2 * num
        for i in range((self.k // 2) ** 2):
            self.addLink(self.host[start + i], edge_switchs[i // (self.k // 2)])
        self.agg_switch.append(agg_switchs)
        self.edge_switch.append(edge_switchs)

if __name__ == "__main__":
    # topo = FatTreeTopo(4)
    topo = TestTopo(3)
    test = TestNet(topo)
    for _ in range(6):
        test.randomTest(bw='100G',testTime = 3,format='M')
        print(test.getInBwMat())
        print(test.getOutBwMat())
