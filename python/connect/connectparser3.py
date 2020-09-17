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
        # if line == self.linecopy:
        #     return
        # else:
        #     self.filecopy.append(line)
        #     self.linecopy = line
        # return
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
        # print len(self.filecopy)
        # pair_first = None
        # pair_second = None
        # is_sendrecv = False
        # is_signal = False
        # last_sendrecv = False
        # last_signal = False
        # for line in self.filecopy:
        #     if self.sendrecvpattern.match(line):
        #         is_sendrecv = True
        #         is_signal = False
        #     else:
        #         is_sendrecv = False
        #         if self.sigpattern.match(line):
        #             is_signal = True
        #         else:
        #             is_signal = False
        #     if (is_sendrecv and is_signal) or (not is_sendrecv and not is_signal):
        #         print "error matched %s" % (line)
        #         exit()
        #     if last_sendrecv and last_signal:
        #         print "error last"
        #         exit()
        #     elif not last_sendrecv and not last_signal:
        #         if is_sendrecv:
        #             pair_first = line
        #             last_sendrecv = True
        #             last_signal = False
        #         else:
        #             pass
        #     elif last_sendrecv:
        #         if is_sendrecv:
        #             pair_first = None
        #             pair_second = None
        #             last_sendrecv = True
        #             last_signal = False
        #         else:
        #             pair_second = line
        #             last_sendrecv = False
        #             last_signal = True
        #     elif last_signal:
        #         if is_signal:
        #             pair_first = None
        #             pair_second = None
        #             last_sendrecv = False
        #             last_signal = True
        #         else:
        #             if pair_first and pair_second:
        #                 print pair_first, pair_second,
        #             pair_first = None
        #             pair_second = None
        #             pair_first = line
        #             last_sendrecv = True
        #             last_signal = False
        #
        # return
        # 2. match
        fd = open("m_info", "w")
        for info in self.connectinfolist:
            print info
            fd.write(str(info) + "\n")
        fd.close()
        # done
        print "done"

def main():
    fd = open("m")
    cp = ConnectParser()
    for (lineno, line) in enumerate(fd):
        cp.parseline(lineno + 1, line)
    cp.done()
    fd.close()

if __name__ == "__main__":
    main()