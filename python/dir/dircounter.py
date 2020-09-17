##################################################
# DIRCOUNTER                                     #
##################################################


# !/usr/bin/env python


import sys
import getopt
import os
import time


##################################################
class Config(object):
    CFG_TOPPATH = ""

    @staticmethod
    def usage():
        print "usage:"
        print "\t%s <path> [options]" % (sys.argv[0])
        print "\tpath: a directory, absolute or relative."
        print "\toptions: -h --help"
        print "\t\t-h, --help: help usage."

    @staticmethod
    def parseargs():
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        for opt, value in opts:
            if opt in ("-h", "--help"):
                Config.usage()
                return False
        if len(args) != 1:
            Config.usage()
            return False
        if not os.path.exists(args[0]):
            print "error: %s not exists!" % (args[0])
            return False
        Config.CFG_TOPPATH = os.path.abspath(args[0])
        return True


##################################################
class DirCounter(object):
    DC_SPLITER = "master"
    DC_SPLITER_MAX = 1
    DC_SPLITER_PREFIX = "INCLUDEPATH += $$PWD"

    def __init__(self, path):
        super(DirCounter, self).__init__()
        self.toppath = os.path.abspath(path)
        assert(os.path.exists(self.toppath))
        self.dirarray = []

    def __countdir(self, path):
        abspath = os.path.abspath(path)
        if -1 != os.path.basename(abspath).find(".") or os.path.islink(abspath):
            return
        assert(os.path.exists(abspath))
        if os.path.isdir(abspath):
            tmp = abspath
            tmp = abspath.split(DirCounter.DC_SPLITER, DirCounter.DC_SPLITER_MAX)[-1]
            tmp = DirCounter.DC_SPLITER_PREFIX + tmp
            self.dirarray.append(tmp)
            for f in os.listdir(abspath):
                os.chdir(abspath)
                self.__countdir(f)

    def countdir(self):
        self.__countdir(self.toppath)

    def getresult(self):
        for path in sorted(self.dirarray):
            print "%s" % (path)
        print "-" * 100


##################################################
def main():
    print "*" * 10, "begin", "*" * 10
    timebegin = time.time()
    if not Config.parseargs():
        exit()
    dc = DirCounter(Config.CFG_TOPPATH)
    dc.countdir()
    dc.getresult()
    timeend = time.time()
    print "-" * 100
    print "time(s): %d" % (timeend - timebegin)
    print "*" * 10, "end", "*" * 10


##################################################
if __name__ == '__main__':
    main()
