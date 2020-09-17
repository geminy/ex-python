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
        self.connectinfo = None
        self.lastmatchsignal = True

    def parseline(self, lineno, line):
        # 1. unique
        if line == self.linecopy:
            return
        else:
            self.filecopy.append(line)
            self.linecopy = line
        return
        # 2. match
        print lineno, line,
        matched = None
        if not self.lastmatchsignal:
            matched = self.sigpattern.match(line)
            if not matched:
                print "error"
                exit()
            self.lastmatchsignal = True
            self.connectinfo.sig = matched.group(1)
            self.connectinfolist.append(self.connectinfo)
            del self.connectinfo
            self.connectinfo = None
        else:
            matched = self.sendrecvpattern.match(line)
            if not matched:
                print "error"
                exit()
            self.lastmatchsignal = False
            self.connectinfo = ConnectInfo()
            self.connectinfo.send = matched.group(1)
            self.connectinfo.sendname = matched.group(2)
            self.connectinfo.recv = matched.group(3)
            self.connectinfo.recvname = matched.group(4)

    def done(self):
        # 1. unique
        print len(self.filecopy)
        for line in self.filecopy:
            print line,
        return
        # 2. match
        fd = open("d_info", "w")
        for info in self.connectinfolist:
            print info
            fd.write(str(info) + "\n")
        fd.close()
        # done
        print "done"

def main():
    fd = open("d")
    cp = ConnectParser()
    for (lineno, line) in enumerate(fd):
        cp.parseline(lineno + 1, line)
    cp.done()
    fd.close()

if __name__ == "__main__":
    main()