##################################################
# LINECOUNTER                                    #
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
        print "\tpath: a file or a directory, absolute or relative."
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
class LineCounter(object):
    LC_FILE_SUFFIX = ("h", "cpp", "c")

    def __init__(self, path):
        super(LineCounter, self).__init__()
        self.toppath = os.path.abspath(path)
        assert(os.path.exists(self.toppath))
        self.linedict = {}  # filename: lineno
        self.treedict = {}  # path: linesum

    def __countline(self, path):
        abspath = os.path.abspath(path)
        if os.path.basename(abspath).startswith(".") or os.path.islink(abspath):
            return
        assert(os.path.exists(abspath))
        if os.path.isfile(abspath):
            filename = os.path.basename(abspath)
            if filename.count(".") != 1:
                return
            if filename.rsplit(".")[-1] in LineCounter.LC_FILE_SUFFIX:
                print abspath
                fd = open(abspath, "r")
                lineno = len(fd.readlines())
                fd.close()
                assert(abspath not in self.linedict.keys())
                self.linedict[abspath] = lineno
        elif os.path.isdir(abspath):
            for f in os.listdir(abspath):
                os.chdir(abspath)
                self.__countline(f)

    def countline(self):
        self.__countline(self.toppath)
        for filename in self.linedict.keys():
            assert(filename not in self.treedict.keys())
            self.treedict[filename] = self.linedict[filename]
            dirname = filename
            while True:
                dirname = os.path.dirname(dirname)
                if dirname in self.treedict.keys():
                    self.treedict[dirname] += self.linedict[filename]
                else:
                    self.treedict[dirname] = self.linedict[filename]
                if dirname == self.toppath:
                    break

    def getresult(self):
        for path in sorted(self.treedict.keys()):
            print "%s: %d" % (path, self.treedict[path])
        linetotalsum = sum(self.linedict.values())
        print "-" * 100
        print "%s: %d" % (self.toppath, linetotalsum)


##################################################
def main():
    print "*" * 10, "begin", "*" * 10
    timebegin = time.time()
    if not Config.parseargs():
        exit()
    lc = LineCounter(Config.CFG_TOPPATH)
    lc.countline()
    lc.getresult()
    timeend = time.time()
    print "-" * 100
    print "time(s): %d" % (timeend - timebegin)
    print "*" * 10, "end", "*" * 10


##################################################
if __name__ == '__main__':
    main()
