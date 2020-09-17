##################################################
# REORDER CODES                                  #
##################################################


# !/usr/bin/env python


import sys
import getopt
import os
import time
import re
import random
import logging


class Config:
    WORK_DIR = None
    INPUT_PATH = None
    FOR_H = False
    FOR_CPP = False
    PRO_INCLUDE = False  # weird
    PRO_QENUMS = False
    PRO_QPROPERTY = False
    PRO_ENUM = False  # weird
    PRO_SIGNALS = False
    PRO_SLOTS = False
    PRO_FUNC = False

    # for print
    def __str__(self):
        return "\
	WORK_DIR=%s\n\
	INPUT_PATH=%s\n\
	FOR_H=%s\n\
	FOR_CPP=%s\n\
	PRO_INCLUDE=%s\n\
	PRO_QENUMS=%s\n\
	PRO_QPROPERTY=%s\n\
	PRO_ENUM=%s\n\
	PRO_SIGNALS=%s\n\
	PRO_SLOTS=%s\n\
	PRO_FUNC=%s" \
               % (Config.WORK_DIR, \
                  Config.INPUT_PATH, \
                  Config.FOR_H, \
                  Config.FOR_CPP, \
                  Config.PRO_INCLUDE, \
                  Config.PRO_QENUMS, \
                  Config.PRO_QPROPERTY, \
                  Config.PRO_ENUM, \
                  Config.PRO_SIGNALS, \
                  Config.PRO_SLOTS, \
                  Config.PRO_FUNC)


##################################################
class MatchRule(object):
    class FileInfo:
        def __init__(self, name):
            self.__filename = name
            self.__filedirname = os.path.dirname(name)
            self.__filebasename = os.path.basename(name)

            # parse, basic
            self.filecontent = []  # real text [line]
            self.datacache = []  # to be re-sorted [lineno, line]
            self.prerule = None  # related to  Config
            self.fileprocessed = False  # need update the file

            # beginning to ending
            self.hassignal = False
            self.hasslot = False

            self.classfound = False  # weird
            self.currentclassname = None  # may be embeded
            self.classnamedict = {}  # classname:[beginno, endno]

            self.dirtylist = []  # [lineno]
            self.dirtyflag = [[0, 0], [0, 0]]  # [comment, pre-processor] [beginno, endno]
            self.dirtyfound = False  # multi-line
            self.dirtymacro = False  # for filesafety

            # reparse, function
            self.filesafety = True  # from dirtymacro and brace
            self.filecontent2 = []  # [line]
            self.datacache2 = []  # [lineno] or [beginno, endno]
            self.publicmatched = False  # for .h public
            self.funcentered = False  # for .cpp block beginning
            self.funcbrace = [0, 0]  # for .cpp block scope

            self.filetype = ""
            if name.endswith(".h"):
                self.filetype = "HEADER"
            elif name.endswith(".cpp"):
                self.filetype = "CPP"

        # for print
        def __str__(self):
            return self.getfilename()

        def getfilename(self):
            return self.__filename

        def getfiledirname(self):
            return self.__filedirname

        def getfilebasename(self):
            return self.__filebasename

        # .h
        def findclass(self, line, lineno):
            classname = None
            # finds class name
            if not self.classfound:
                wordlist = line.split()
                if len(wordlist) > 0:
                    if "class" == wordlist[0]:
                        for word in wordlist:
                            if word in ("class", "NG_EXPORT"):
                                continue
                            # class pre-declaration
                            if word.find(";") != -1:
                                break
                            # inheritance
                            if word.endswith(":"):
                                classname = word[:-1]
                            else:
                                classname = word
                            break
                        if classname:
                            if line.find(";") != -1:
                                logging.error("[class]" + str(lineno) + ":" + line)
                                exit()
                            self.classfound = True
                            self.sendclassname((lineno, classname))
            else:
                # finds class ending
                if re.match(r"\s*\};", line):
                    self.sendclassname((lineno, lineno), False)
                else:
                    # finds embeded class name
                    wordlist = line.split()
                    if len(wordlist) > 0:
                        if wordlist[0] in ("class", "struct", "enum", "union"):
                            # anonym
                            if len(wordlist) == 1 or wordlist[1] == "{":
                                self.sendclassname((lineno, str(lineno)))
                                return
                            for word in wordlist:
                                if word in ("class", "struct", "enum", "union", "NG_EXPORT"):
                                    continue
                                if word.find(";") != -1:
                                    break
                                if word.endswith(":"):
                                    classname = word[:1]
                                else:
                                    classname = word
                                break
                            if classname:
                                # weird type usage
                                if line.find(";") == -1 and line.find("(") == -1:
                                    self.sendclassname((lineno, classname))

        # called by findclassname
        def sendclassname(self, name, entry=True):
            # @name (lineno, classname)
            # class name found
            if entry:
                if self.currentclassname is None:
                    self.currentclassname = name[1]
                else:
                    # embeded classname
                    self.currentclassname += ("::" + str(name[1]))
                assert self.currentclassname not in self.classnamedict.keys()
                self.classnamedict[self.currentclassname] = [name[0], -1]
            # class ending found
            else:
                assert self.currentclassname is not None
                assert self.currentclassname in self.classnamedict.keys()
                assert -1 == self.classnamedict[self.currentclassname][1]
                self.classnamedict[self.currentclassname][1] = name[0]
                # embed classname?
                mark = self.currentclassname.rfind("::")
                if -1 == mark:
                    self.currentclassname = None
                    self.classfound = False
                else:
                    self.currentclassname = self.currentclassname[:mark]

        # .h class
        # .cpp
        def finddirty(self, line, lineno):
            if "HEADER" == self.filetype and self.classfound or "CPP" == self.filetype:
                if self.dirtyfound:
                    self.dirtylist.append(lineno)
                    # */ dirtyflag[0] [1, 1]
                    if 1 == self.dirtyflag[0][0]:
                        if re.match(r".*\*/", line):
                            self.dirtyflag[0][1] = 1
                        if self.dirtyflag[0][0] == self.dirtyflag[0][1]:
                            self.dirtyfound = False
                            self.dirtyflag[0] = [0, 0]
                    ##endif dirtyflag[1] [n, n]
                    elif self.dirtyflag[1][0] > 0:
                        ##if embeded
                        if re.match(r"\s*#\s*(if|ifdef|ifndef)\s+\S+", line):
                            self.dirtyflag[1][0] += 1
                        ##endif
                        if re.match(r"\s*#\s*endif", line):
                            self.dirtyflag[1][1] += 1
                        if self.dirtyflag[1][0] == self.dirtyflag[1][1]:
                            self.dirtyfound = False
                            self.dirtymacro = False
                            self.dirtyflag[1] = [0, 0]
                    else:
                        logging.error("[finddirty]" + str(lineno) + ":" + line)
                        exit()

                else:
                    for i in (0, 1):
                        for j in (0, 1):
                            assert 0 == self.dirtyflag[i][j]
                    # //
                    if re.match(r"\s*//", line):
                        self.dirtylist.append(lineno)
                        return
                    # /**/
                    if re.match(r"\s*/\*.*\*/", line):
                        self.dirtylist.append(lineno)
                        return
                    # /* dirtyflag[0] [1, 0]
                    if re.match(r"\s*/\*", line):
                        self.dirtylist.append(lineno)
                        self.dirtyflag[0][0] = 1
                        self.dirtyfound = True
                        return
                    ##if dirtyflag[1] [1, 0]
                    if re.match(r"\s*#\s*(if|ifdef|ifndef)\s+\S+", line):
                        self.dirtylist.append(lineno)
                        self.dirtyflag[1][0] = 1
                        self.dirtyfound = True
                        self.dirtymacro = True

        # .cpp
        def findfunchead(self, line, lineno):
            # complicated rules to find func head
            if lineno in self.dirtylist:
                return -1
            # not good
            if line.count("::") != 1:
                return -1
            if line.count("(") != 1:
                return -1
            if re.match(r"\s*\S+.*\s+\S+::\S+\(.*\)", line):
                if line.find(";") == -1 and line.find("=") == -1 and line.find('"') == -1 and line.find("{") == -1:
                    return lineno
                else:
                    return -1
            else:
                return -1

        # exchanges the position of two close functions
        def reprocess(self):
            assert 2 == len(self.datacache2)
            if "HEADER" == self.filetype:
                preno_begin = preno_end = self.datacache2[0]
                rearno_begin = rearno_end = self.datacache2[1]
            elif "CPP" == self.filetype:
                preno_begin = self.datacache2[0][0]
                preno_end = self.datacache2[0][1]
                rearno_begin = self.datacache2[1][0]
                rearno_end = self.datacache2[1][1]
            else:
                preno_begin = preno_end = rearno_begin = rearno_end = -1
                print "unknown file type!!"
                exit()
            self.datacache2 = []
            if 1 == rearno_begin - preno_end:
                pass
            else:
                # grpups (spaceline, dirty...) to rear
                rearno_begin = preno_end + 1
            while True:
                if preno_begin - 1 in self.dirtylist:
                    preno_begin -= 1
                else:
                    break
            # groups spaceline to pre
            if len(self.filecontent2[preno_begin - 1].rstrip(os.linesep)) == 0:
                preno_begin -= 1
            linecount = rearno_end - preno_begin + 1
            prelist = self.filecontent2[preno_begin:preno_end + 1]
            rearlist = self.filecontent2[rearno_begin:rearno_end + 1]
            for line in prelist:
                rearlist.append(line)
            assert len(rearlist) == linecount
            for offset in range(0, linecount):
                self.filecontent2[preno_begin + offset] = rearlist[offset]
            self.fileprocessed = True

        # only for function
        def reparse(self):
            for lineno, line in enumerate(self.filecontent):
                # .h line by line
                if "HEADER" == self.filetype:
                    # bounded by class
                    # calls findclass before finddirty
                    self.findclass(line, lineno)
                    self.finddirty(line, lineno)
                    self.filecontent2.append(line)
                    if self.classfound:
                        # public, exclude (protected, private...)
                        if self.publicmatched:
                            if not lineno in self.dirtylist:
                                # two close functions matched
                                if re.match(r"\s*\S+\s+\S+\(.*\);", line):
                                    self.datacache2.append(lineno)
                                    if 2 == len(self.datacache2):
                                        self.reprocess()
                                else:
                                    # clears cache
                                    self.datacache2 = []
                                    self.publicmatched = False
                                    continue
                                    # weird
                                    if re.match(r"\s*(signals|Q_SIGNALS):|\s*(public|protected|private).*:", line):
                                        self.publicmatched = False
                                    if re.match(r"\s*public:", line):
                                        self.publicmatched = True

                        else:
                            if re.match(r"\s*public:", line):
                                self.publicmatched = True
                # .cpp block by block
                elif "CPP" == self.filetype:
                    self.finddirty(line, lineno)
                    self.filecontent2.append(line)
                    # function entered
                    if self.funcentered:
                        if self.dirtymacro:
                            # returns immediately if unsafe
                            if line.find("{") != -1 or line.find("}") != -1:
                                self.filesafety = False
                                return
                        if line.find("{") != -1 and lineno not in self.dirtylist:
                            self.funcbrace[0] += 1
                        if line.find("}") != -1 and lineno not in self.dirtylist:
                            self.funcbrace[1] += 1
                        if self.funcbrace[0] == self.funcbrace[1] and 0 != self.funcbrace[0]:
                            self.funcentered = False
                            self.funcbrace = [0, 0]
                            datacachelen = len(self.datacache2)
                            self.datacache2[datacachelen - 1][1] = lineno
                            if 2 == datacachelen:
                                self.reprocess()
                    # finds function beginning
                    else:
                        funchead = self.findfunchead(line, lineno)
                        if -1 != funchead:
                            self.funcentered = True
                            self.datacache2.append([lineno, -1])
                            assert 2 == len(self.funcbrace)
                            assert 0 == self.funcbrace[0]
                            assert 0 == self.funcbrace[1]
                            if -1 != line.find("{"):
                                self.funcbrace[0] = 1
                            if -1 != line.find("}"):
                                self.funcbrace[1] = 1
                            if 1 == self.funcbrace[0] and 1 == self.funcbrace[1]:
                                self.funcentered = False
                                self.funcbrace = [0, 0]
                                datacachelen = len(self.datacache2)
                                self.datacache2[datacachelen - 1][1] = lineno
                                if 2 == datacachelen:
                                    self.reprocess()

        # basic rule
        def senddata(self, line, lineno, rule):
            if rule is None:
                if self.prerule is None:
                    self.filecontent.append(line)
                else:
                    self.processdata()
                    self.filecontent.append(line)
            # filecontent with rule, not line
            else:
                if self.prerule is None:
                    self.filecontent.append(rule)
                    self.datacache.append((lineno, line))
                else:
                    if rule == self.prerule:
                        self.filecontent.append(rule)
                        self.datacache.append((lineno, line))
                    else:
                        self.processdata()
                        self.filecontent.append(rule)
                        self.datacache.append((lineno, line))
            self.prerule = rule

        # simple signal
        def sendsignal(self, line, lineno, rule):
            assert (MatchRule.FI_SIGNAL == rule)
            if not self.hassignal:
                # just begins
                self.senddata(line, lineno, None)
                self.hassignal = True
                assert (0 == len(self.datacache))
            else:
                # has begun
                if self.prerule is None:
                    pass
                else:
                    assert (MatchRule.FI_SIGNAL == self.prerule)
                # meets ending
                if re.match(MatchRule.MR_SIGNAL_END, line):
                    self.senddata(line, lineno, None)
                    self.hassignal = False
                    return
                # ignores / and #
                if re.match(MatchRule.MR_SIGNAL_TER, line):
                    self.senddata(line, lineno, None)
                    self.hassignal = False
                    return
                # ignores spaceline
                if 0 == len(line.rstrip(os.linesep)):
                    self.senddata(line, lineno, None)
                    self.hassignal = False
                    return
                if re.match(MatchRule.MR_SIGNAL_GET, line):
                    self.senddata(line, lineno, MatchRule.FI_SIGNAL)
                else:
                    logging.error("[signal]" + str(lineno) + ":" + line)
                    exit()

        # weird slot
        def sendslot(self, line, lineno, rule):
            # same method as signal
            assert (MatchRule.FI_SLOT == rule)
            if not self.hasslot:
                self.senddata(line, lineno, None)
                self.hasslot = True
                assert (0 == len(self.datacache))
            else:
                if self.prerule is None:
                    pass
                else:
                    assert (MatchRule.FI_SLOT == self.prerule)
                if re.match(MatchRule.MR_SLOT_END, line):
                    self.senddata(line, lineno, None)
                    self.hasslot = False
                    return
                if re.match(MatchRule.MR_SLOT_TER, line):
                    self.senddata(line, lineno, None)
                    self.hasslot = False
                    return
                if 0 == len(line.rstrip(os.linesep)):
                    self.senddata(line, lineno, None)
                    self.hasslot = False
                    return
                if re.match(MatchRule.MR_SLOT_GET, line):
                    self.senddata(line, lineno, MatchRule.FI_SLOT)
                else:
                    # ignores (declaration and definition)
                    self.senddata(line, lineno, None)
                    self.hasslot = False

        # .h
        def processdata(self):
            # QENUMS QPROPERTY signal slot - 1/nochange 2/exchage 3/random
            if self.prerule in MatchRule.FI_COMMON_PROCESS:
                linecount = len(self.datacache)
                lineno_begin = self.datacache[0][0]
                if 1 == linecount:
                    self.filecontent[lineno_begin] = self.datacache[0][1]
                elif 2 == linecount:
                    self.filecontent[lineno_begin] = self.datacache[1][1]
                    self.filecontent[lineno_begin + 1] = self.datacache[0][1]
                elif 2 < linecount:
                    # random strategy
                    lineseq = range(0, linecount)
                    for offset in range(0, linecount):
                        linepos = random.choice(lineseq)
                        seqindex = lineseq.index(linepos)
                        self.filecontent[lineno_begin + offset] = self.datacache[linepos][1]
                        del lineseq[seqindex]
            self.datacache = []
            self.fileprocessed = True

        def complete(self):
            # function, exclude slot
            if Config.PRO_FUNC:
                self.reparse()
                self.filecontent = self.filecontent2
            # weird preprocessor
            if not self.filesafety:
                logging.warn("nothing to do for this file because of some uncertain reason")
                return
            if not self.fileprocessed:
                logging.warn("nothing to do for this file because of no rules matched")
                return
            # final
            # logging default level is warn
            logging.warn(self.getfilename() + " will be replaced")
            os.remove(self.getfilename())
            fd = open(self.getfilename(), "a")
            for line in self.filecontent:
                fd.write(line)
            fd.close()
            print self.getfilename(), "...done"


    ##################################################
    # NQFlickable.h include problem
    # NQView.h weird problem
    MR_DIR_IGNORE = ("tests", "shaders", "Designer", "doc", "iautoqmlconfig", "qml", "QmlAppLaunch")
    MR_FILETYPE = r".+\.h$|.+\.cpp$"
    MR_QENUMS = r"Q_ENUMS\(.+\)"
    FI_QENUMS = "QENUMS"
    MR_QPROPERTY = r"Q_PROPERTY\(.+\)"
    FI_QPROPERTY = "QPROPERTY"
    MR_SIGNAL = r"^\s*(signals|Q_SIGNALS):"
    FI_SIGNAL = "SIGNAL"
    MR_SIGNAL_END = r"^\s*(public|protected|private).*:|^\s*\};"
    MR_SIGNAL_TER = r"^\s*(#|/)"
    MR_SIGNAL_GET = r"^\s*\S+\s+.+\(.*\);"
    MR_SLOT = r"^\s*(public|protected|private)\s+(slots|Q_SLOTS):"
    FI_SLOT = "SLOT"
    MR_SLOT_END = MR_SIGNAL_END
    MR_SLOT_TER = MR_SIGNAL_TER
    MR_SLOT_GET = MR_SIGNAL_GET
    FI_COMMON_PROCESS = (FI_QENUMS, FI_QPROPERTY, FI_SIGNAL, FI_SLOT)

    ##################################################
    def __init__(self, obj):
        # object.__init__(self)
        super(MatchRule, self).__init__()
        self.fileinfo = MatchRule.FileInfo(obj)

    def parsefile(self):
        print self.fileinfo, "parsing..."
        if "HEADER" == self.fileinfo.filetype:
            if not Config.FOR_H:
                logging.warn("nothing to do for this .h")
                return False
        elif "CPP" == self.fileinfo.filetype:
            if not Config.FOR_CPP:
                logging.warn("nothing to do for this .cpp")
                return False
        fd = open(self.fileinfo.getfilename(), "r")
        for lineno, line in enumerate(fd):
            rule = None
            # only exchanges functions for cpp
            if "CPP" == self.fileinfo.filetype:
                self.fileinfo.senddata(line, lineno, None)
                continue
            # signal
            if Config.PRO_SIGNALS:
                if self.fileinfo.hassignal:
                    rule = MatchRule.FI_SIGNAL
                else:
                    if re.match(MatchRule.MR_SIGNAL, line):
                        rule = MatchRule.FI_SIGNAL
                if rule:
                    self.fileinfo.sendsignal(line, lineno, rule)
                    continue
            # slot
            if Config.PRO_SLOTS:
                if self.fileinfo.hasslot:
                    rule = MatchRule.FI_SLOT
                else:
                    if re.match(MatchRule.MR_SLOT, line):
                        rule = MatchRule.FI_SLOT
                if rule:
                    self.fileinfo.sendslot(line, lineno, rule)
                    continue
            # QENUMS
            if Config.PRO_QENUMS:
                if re.search(MatchRule.MR_QENUMS, line):
                    rule = MatchRule.FI_QENUMS
                    self.fileinfo.senddata(line, lineno, rule)
                    continue
            # QPROPERTY
            if Config.PRO_QPROPERTY:
                if re.search(MatchRule.MR_QPROPERTY, line):
                    rule = MatchRule.FI_QPROPERTY
                    self.fileinfo.senddata(line, lineno, rule)
                    continue
            # others
            self.fileinfo.senddata(line, lineno, None)
        fd.close()
        return True

    def complete(self, goon):
        if goon:
            self.fileinfo.complete()


##################################################
def usage():
    print "******************************************************************"
    print "*\tusage:"
    print "*\t\tthis '%s' will re-sort your codes and it depends on the rule from you command line." % (sys.argv[0])
    print "*\tformat:"
    print "*\t\tpython %s -d <path> [options]" % (sys.argv[0])
    print "*\t\tpath: a file or a directory, both absolute and relative path are supported."
    print "*\t\toptions: -h -e -p -s -l -f --header --cpp"
    print "*\t\t\t-h: help for script usage"
    print "*\t\t\t-e: re-sort for QENUMS"
    print "*\t\t\t-p: re-sort for QPROPERTY"
    print "*\t\t\t-s: re-sort for signals"
    print "*\t\t\t-l: re-sort for slots"
    print "*\t\t\t-f: re-sort for functions"
    print "*\t\t\t--header: resort for header file"
    print "*\t\t\t--cpp: resort for cpp file"
    print "*\tnote:"
    print "*\t\tyou should specify at least one of --header and --cpp"
    print "*\t\tand other optional options may be necessary."
    print "******************************************************************"
    exit()


##################################################
def checkinput():
    print "your command:",
    for arg in sys.argv:
        print arg,
    print
    opts, args = getopt.getopt(sys.argv[1:], "hd:epslf", ["header", "cpp", "include", "enum"])
    if 0 < len(args):
        usage()
    for opt, value in opts:
        if "-h" == opt:
            usage()
        elif "-d" == opt:
            if not os.path.exists(value):
                logging.error("invalid path: " + value)
                exit()
            Config.INPUT_PATH = os.path.abspath(value)
        elif "-e" == opt:
            Config.PRO_QENUMS = True
        elif "-p" == opt:
            Config.PRO_QPROPERTY = True
        elif "-s" == opt:
            Config.PRO_SIGNALS = True
        elif "-l" == opt:
            Config.PRO_SLOTS = True
        elif "-f" == opt:
            Config.PRO_FUNC = True
        elif "--header" == opt:
            Config.FOR_H = True
        elif "--cpp" == opt:
            Config.FOR_CPP = True
        elif "--include" == opt:
            Config.PRO_INCLUDE = True
        elif "--enum" == opt:
            Config.PRO_ENUM = True
    if not Config.INPUT_PATH:
        usage()
    if Config.FOR_H is False and Config.FOR_CPP is False:
        usage()
    Config.WORK_DIR = os.path.abspath(".")
    print Config()


##################################################
def filterfile(path):
    # re
    # obj = re.match(MatchRule.MR_FILETYPE, path)
    pattern = re.compile(MatchRule.MR_FILETYPE)
    obj = pattern.match(path)
    if obj is None:
        print path, "...ignored"
        return
    print obj.group(), "...matched"
    # real work begins
    mr = MatchRule(path)
    parsed = mr.parsefile()
    mr.complete(parsed)


##################################################
def scanfile(path):
    path_abs = os.path.abspath(path)
    if os.path.isfile(path_abs):
        print path_abs, "matching..."
        # finds .h/cpp files
        filterfile(path_abs)
        time.sleep(.1)
    elif os.path.isdir(path_abs):
        for afile in os.listdir(path_abs):
            # some dirs will be ignored
            if afile in MatchRule.MR_DIR_IGNORE:
                print "%s/%s ...ignored" % (path_abs, afile)
                continue
            if afile.startswith("."):
                print "%s/%s ...ignored" % (path_abs, afile)
                continue
            # changes the workdir while recurring
            os.chdir(path_abs)
            scanfile(afile)


##################################################
def scanfiles():
    scanfile(Config.INPUT_PATH)


##################################################
def main():
    print "!!!!!!!!!!begin!!!!!!!!!!"
    checkinput()
    # works whlie scanning files
    scanfiles()
    print "!!!!!!!!!!end!!!!!!!!!!"


##################################################
if __name__ == '__main__':
    main()
