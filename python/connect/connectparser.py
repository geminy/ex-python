#!/usr/bin/env python


import re


class ConnectInfo:
    def __init__(self):
        self.send = ""
        self.sendname = ""
        self.recv = ""
        self.recvname = ""
        self.sig = ""

    def __str__(self):
        return "%s %s %s %s %s" % (self.send, self.sendname, self.recv, self.recvname, self.sig)


class ConnectParser(object):
    CP_RE_SENDER_RECEIVER = "OBJECT\s+dumpinfo\s+sender\s+(\w+)::(\w+)\s+and\s+receiver\s+(\w+)::(\w+)\s+.*"
    CP_RE_SIGNAL = "OBJECT\s+dumpinfo\s+duplicated\s+signal\s+connection:\s+(\w+\(.*?\)).*"

    def __init__(self):
        object.__init__(self)
        self.sendrecvpattern = re.compile(ConnectParser.CP_RE_SENDER_RECEIVER)
        self.sigpattern = re.compile(ConnectParser.CP_RE_SIGNAL)
        self.linecopy = None
        self.filecopy = []
        self.connectinfolist = []
        self.lastmatchsignal = False
        self.connectinfocache = []

    def parseline(self, lineno, line):
        # 1. unique
        # if line == self.linecopy:
        #     return
        # else:
        #     self.filecopy.append(line)
        #     self.linecopy = line
        # 2. match
        # print lineno, line,
        matched = None
        matched = self.sendrecvpattern.match(line)
        if matched:
            if self.lastmatchsignal:
                assert len(self.connectinfocache) > 0
                for info in self.connectinfocache:
                    self.connectinfolist.append(info)
                self.connectinfocache = []
            ci = ConnectInfo()
            ci.send = matched.group(1)
            ci.sendname = matched.group(2)
            ci.recv = matched.group(3)
            ci.recvname = matched.group(4)
            self.connectinfocache.append(ci)
            self.lastmatchsignal = False
        else:
            matched = self.sigpattern.match(line)
            if matched:
                assert len(self.connectinfocache) > 0
                if self.lastmatchsignal:
                    assert len(self.connectinfocache) == 1
                    ci = ConnectInfo()
                    ci.send = self.connectinfocache[0].send
                    ci.sendname = self.connectinfocache[0].sendname
                    ci.recv = self.connectinfocache[0].recv
                    ci.recvname = self.connectinfocache[0].recvname
                    ci.sig = matched.group(1)
                    self.connectinfocache.append(ci)
                else:
                    for i in range(0, len(self.connectinfocache)):
                        self.connectinfocache[i].sig = matched.group(1)
                self.lastmatchsignal = True
        assert matched


    def done(self):
        # 1. unique
        # print len(self.filecopy)
        # for line in self.filecopy:
        #     print line,
        # 2. match
        fd = open("connect_info", "w")
        for info in self.connectinfolist:
            print info
            fd.write(str(info) + "\n")
        fd.close()
        # done
        print "done"

def main():
    fd = open("connect")
    cp = ConnectParser()
    for (lineno, line) in enumerate(fd):
        cp.parseline(lineno + 1, line)
    cp.done()
    fd.close()

if __name__ == "__main__":
    main()