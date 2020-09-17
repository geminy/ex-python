##################################################
# RENAME CLASS MEMBER VARS                       #
#     a) starts from source codes (.cpp)         #
#     b) (.h/.cpp) pair is required              #
#     c) finds class name of header firstly      #
#     d) finds class member vars (m_ not m_nq)   #
#     e) replace (m_) with (m_nq)                #
##################################################


import sys
import getopt
import os
import logging
import re
import time


##################################################
class FileParser(object):
    FP_FINDCLASS_BEGIN = r"^\s*(class)\s+(NG_EXPORT)\s+(\S+).*"
    FP_FINDCLASS_BEGIN2 = r"^\s*(class)\s+(\S+).*"
    FP_FINDCLASS_END = r"^\s*(\};)"
    FP_FINDSTRUCT_BEGIN = r"^\s*(struct)\s+(NG_EXPORT)\s+(\S+).*"
    FP_FINDSTRUCT_BEGIN2 = r"^\s*(struct)\s+(\S+).*"
    FP_FINDENUM_BEGIN = r"^\s*(enum)\s+(\S+).*"
    FP_FINDENUM_ONELINE = ("{", "}", ";")
    FP_FINDENUM_RETTYPE = ("(", ")", ";")

    FP_FINDPRIVATE_BEGIN = r"^\s*private:"
    FP_FINDPRIVATE_END = r"^\s*(public|protected):"
    FP_FINDPRIVATE_END2 = r"^\s*(signals|Q_SIGNALS):"
    FP_FINDPRIVATE_END3 = r"^\s*(public|protected|private)\s+(slots|Q_SLOTS):"

    FP_FINDCLASS_MEMBERVARS = r"^\s*(.+)\s+(m_.+);"
    FP_FINDCLASS_MEMBERVARS2 = r"^\s*(.+\s+[\*|&])(m_.+);"
    FP_CLASS_MEMBERVARS_PREFIX = r"m_"
    FP_CLASS_MEMBERVARS_PREFIX_NQ = "m_nq"

    def __init__(self, basename, filelist):
        super(FileParser, self).__init__()
        # without suffix
        self.basename = basename
        # [header, source, private]
        self.filelist = filelist

        # header
        self.classfound = False # may be embeded
        self.classname = None # current class name, only for class
        self.privatefound = False # only private member vars
        self.headercache = [] # line
        self.classesdict = {} # class/struct/enum: [beginno, endno]
        self.classdict = {} # class: [beginno, endno]
        self.membervarsdict = {} # class: [(class_member_name, type, lineno)]
        self.headercache_p = []
        self.classesdict_p = {}
        self.classdict_p = {}
        self.membervarsdict_p = {}

        # source
        self.sourcecache = []  # line
        self.membervarslist = [] # from membervarsdict and membervarsdict_p
        self.membervarslist_stripe = [] # prevent repeat

    def __saveclass(self, name, lineno, line, filetype, entry=True):
        if entry:
            clsname, clstype = name.split("-")
            assert clstype in ("class", "struct", "enum")
            if not self.classname:
                self.classname = clsname
            else:
                self.classname += ("::" + clsname)
            if filetype == FileInfo.FI_HEADER:
                assert self.classname not in self.classesdict.keys()
                self.classesdict[self.classname] = [lineno, -1]
                if "class" == clstype:
                    assert self.classname not in self.classdict.keys()
                    self.classdict[self.classname] = [lineno, -1]
            elif filetype == FileInfo.FI_PRIVATE:
                assert self.classname not in self.classesdict_p.keys()
                self.classesdict_p[self.classname] = [lineno, -1]
                if "class" == clstype:
                    assert self.classname not in self.classdict_p.keys()
                    self.classdict_p[self.classname] = [lineno, -1]
        else:
            assert self.classname is not None
            if filetype == FileInfo.FI_HEADER:
                assert self.classname in self.classesdict.keys()
                assert -1 == self.classesdict[self.classname][1]
                self.classesdict[self.classname][1] = lineno
                if self.classname in self.classdict.keys():
                    self.classdict[self.classname][1] = lineno
            elif filetype == FileInfo.FI_PRIVATE:
                assert self.classname in self.classesdict_p.keys()
                assert -1 == self.classesdict_p[self.classname][1]
                self.classesdict_p[self.classname][1] = lineno
                if self.classname in self.classdict_p.keys():
                    self.classdict_p[self.classname][1] = lineno
            embedmark = self.classname.rfind("::")
            if -1 == embedmark:
                self.classname = None
                self.classfound = False
            else:
                self.classname = self.classname[:embedmark]

    def __findclass(self, lineno, line, filetype):
        classname = None
        reresult = None
        if not self.classfound:
            reresult = re.match(FileParser.FP_FINDCLASS_BEGIN, line)
            if reresult:
                classname = reresult.group(3)
                classname = classname.strip("{")
                classname = classname.strip(":")
                classname += "-class"
            else:
                reresult = re.match(FileParser.FP_FINDCLASS_BEGIN2, line)
                if reresult:
                    tmpclass = reresult.group(2)
                    if not tmpclass.endswith(";"):
                        classname = tmpclass
                        classname = classname.strip("{")
                        classname = classname.strip(":")
                        classname += "-class"
            if classname:
                self.classfound = True
                self.__saveclass(classname, lineno, line, filetype)
        else:
            if re.match(FileParser.FP_FINDCLASS_END, line):
                self.__saveclass(None, lineno, line, filetype, False)
            else:
                # embeded class
                reresult = re.match(FileParser.FP_FINDCLASS_BEGIN, line)
                if reresult:
                    classname = reresult.group(3)
                    classname = classname.strip("{")
                    classname = classname.strip(":")
                    classname += "-class"
                else:
                    reresult = re.match(FileParser.FP_FINDCLASS_BEGIN2, line)
                    if reresult:
                        tmpclass = reresult.group(2)
                        if not tmpclass.endswith(";"):
                            classname = tmpclass
                            classname = classname.strip("{")
                            classname = classname.strip(":")
                            classname += "-class"
                # embeded struct
                if not reresult:
                    reresult = re.match(FileParser.FP_FINDSTRUCT_BEGIN, line)
                    if reresult:
                        classname = reresult.group(3)
                        classname = classname.strip("{")
                        classname = classname.strip(":")
                        classname += "-struct"
                    else:
                        reresult = re.match(FileParser.FP_FINDSTRUCT_BEGIN2, line)
                        if reresult:
                            tmpstruct = reresult.group(2)
                            if not tmpstruct.endswith(";"):
                                classname = tmpstruct
                                classname = classname.strip("{")
                                classname = classname.strip(":")
                                classname += "-struct"
                # embeded enum
                if not reresult:
                    reresult = re.match(FileParser.FP_FINDENUM_BEGIN, line)
                    if reresult:
                        enumsafe = True
                        enumsafeflag = []
                        # enum defination in one line
                        for opt in FileParser.FP_FINDENUM_ONELINE:
                            if line.find(opt) != -1:
                                enumsafeflag.append("False")
                            else:
                                enumsafeflag.append("True")
                        if not "True" in enumsafeflag:
                            enumsafe = False
                        if enumsafe:
                            enumsafeflag = []
                            # enum as the return type
                            for opt in FileParser.FP_FINDENUM_RETTYPE:
                                if line.find(opt) != -1:
                                    enumsafeflag.append("False")
                                else:
                                    enumsafeflag.append("True")
                            if not "True" in enumsafeflag:
                                enumsafe = False
                        if enumsafe:
                            classname = reresult.group(2)
                            classname = classname.strip("{")
                            classname += "-enum"
                if classname:
                    self.__saveclass(classname, lineno, line, filetype)

    def __findclsmembvars(self, lineno, line, filetype):
        if self.classfound:
            # finds private
            if self.privatefound:
                if re.match(FileParser.FP_FINDPRIVATE_END, line):
                    self.privatefound = False
                elif re.match(FileParser.FP_FINDPRIVATE_END2, line):
                    self.privatefound = False
                elif re.match(FileParser.FP_FINDPRIVATE_END3, line):
                    self.privatefound = False
            if re.match(FileParser.FP_FINDPRIVATE_BEGIN, line):
                self.privatefound = True
            if not self.privatefound:
                return
            reret = re.match(FileParser.FP_FINDCLASS_MEMBERVARS, line)
            if not reret:
                reret = re.match(FileParser.FP_FINDCLASS_MEMBERVARS2, line)
            if reret:
                membname = reret.group(2)
                if membname.startswith(FileParser.FP_CLASS_MEMBERVARS_PREFIX_NQ):
                    return
                membtype = reret.group(1)
                # for bit
                membname = membname.split()[0]
                membname = membname.split(":")[0]
                if FileInfo.FI_HEADER == filetype:
                    if self.classname not in self.membervarsdict:
                        self.membervarsdict[self.classname] = []
                    self.membervarsdict[self.classname].append((membname, membtype, lineno))
                elif FileInfo.FI_PRIVATE == filetype:
                    if self.classname not in self.membervarsdict_p:
                        self.membervarsdict_p[self.classname] = []
                    self.membervarsdict_p[self.classname].append((membname, membtype, lineno))

    def __cleardata(self):
        self.classfound = False
        self.classname = None

    def parseready(self):
        assert 3 == len(self.filelist)
        # must True
        if self.filelist[1]:
            # alternative
            if self.filelist[0] or self.filelist[2]:
                return True
        return False

    def parseheader(self):
        print self.basename, self.filelist[0]
        if self.filelist[0] is None:
            return
        self.__cleardata()
        fd = open(self.filelist[0], "r")
        for lineno, line in enumerate(fd):
            self.headercache.append(line)
            self.__findclass(lineno, line, FileInfo.FI_HEADER)
            self.__findclsmembvars(lineno, line, FileInfo.FI_HEADER)
        fd.close()

    def parseprivate(self):
        print self.basename, self.filelist[2]
        if self.filelist[2] is None:
            return
        self.__cleardata()
        fd = open(self.filelist[2], "r")
        for lineno, line in enumerate(fd):
            self.headercache_p.append(line)
            self.__findclass(lineno, line, FileInfo.FI_PRIVATE)
            self.__findclsmembvars(lineno, line, FileInfo.FI_PRIVATE)
        fd.close()

    def parsesource(self):
        print self.basename, self.filelist[1]
        assert self.filelist[1] is not None
        fd = open(self.filelist[1], "r")
        for lineno, line in enumerate(fd):
            self.sourcecache.append(line)
        fd.close()

    def complete(self):
        # collects all class member vars and makes sorting
        for nametuplelist in self.membervarsdict.values():
            for nametuple in nametuplelist:
                if nametuple[0] not in self.membervarslist:
                    self.membervarslist.append(nametuple[0])
        for nametuplelist in self.membervarsdict_p.values():
            for nametuple in nametuplelist:
                if nametuple[0] not in self.membervarslist:
                    self.membervarslist.append(nametuple[0])
        self.membervarslist = sorted(self.membervarslist)
        # long vars include other vars will be removed
        striplist = []
        length = len(self.membervarslist)
        for index, membvar in enumerate(self.membervarslist):
            if membvar in striplist:
                continue
            if index < length - 1:
                for memvar2 in self.membervarslist[index + 1:]:
                    if memvar2.find(membvar) != -1:
                        striplist.append(memvar2)
        for membvar in self.membervarslist:
            if membvar not in striplist:
                self.membervarslist_stripe.append(membvar)
        # header
        if self.filelist[0]:
            fd = open(self.filelist[0], "w")
            for line in self.headercache:
                for membvar in self.membervarslist_stripe:
                    # re-name condition
                    canreplace = False
                    membvarindex = line.find(membvar)
                    if 0 == membvarindex:
                        canreplace = True
                    elif 0 < membvarindex:
                        if not re.match(r"\w|_", line[membvarindex - 1]):
                            canreplace = True
                    if canreplace:
                        membvar_nq = membvar.replace(FileParser.FP_CLASS_MEMBERVARS_PREFIX,
                                                     FileParser.FP_CLASS_MEMBERVARS_PREFIX_NQ)
                        line = line.replace(membvar, membvar_nq)
                fd.write(line)
            fd.close()
        # source
        assert self.filelist[1] is not None
        fd = open(self.filelist[1], "w")
        for line in self.sourcecache:
            for membvar in self.membervarslist_stripe:
                canreplace = False
                membvarindex = line.find(membvar)
                if 0 == membvarindex:
                    canreplace = True
                elif 0 < membvarindex:
                    if not re.match(r"\w|_", line[membvarindex - 1]):
                        canreplace = True
                if canreplace:
                    membvar_nq = membvar.replace(FileParser.FP_CLASS_MEMBERVARS_PREFIX,
                                                 FileParser.FP_CLASS_MEMBERVARS_PREFIX_NQ)
                    line = line.replace(membvar, membvar_nq)
            fd.write(line)
        fd.close()
        # private
        if self.filelist[2]:
            fd = open(self.filelist[2], "w")
            for line in self.headercache_p:
                for membvar in self.membervarslist_stripe:
                    canreplace = False
                    membvarindex = line.find(membvar)
                    if 0 == membvarindex:
                        canreplace = True
                    elif 0 < membvarindex:
                        if not re.match(r"\w|_", line[membvarindex - 1]):
                            canreplace = True
                    if canreplace:
                        membvar_nq = membvar.replace(FileParser.FP_CLASS_MEMBERVARS_PREFIX,
                                            FileParser.FP_CLASS_MEMBERVARS_PREFIX_NQ)
                        line = line.replace(membvar, membvar_nq)
                fd.write(line)
            fd.close()
        print self.basename, "@ completed"


##################################################
class FileCollector:
    # key: in Config.CONFIG_FILETYPE
    # value: [header, source, private]
    FC_FILEDICT = {}

    @staticmethod
    def parsefile():
        for filekey in FileCollector.FC_FILEDICT:
            fp = FileParser(filekey, FileCollector.FC_FILEDICT[filekey])
            if not fp.parseready():
                print "warning: %s not a pair (h/cpp) and ignored" % (filekey)
                continue
            fp.parseheader()
            fp.parseprivate()
            fp.parsesource()
            fp.complete()


##################################################
class FileInfo:
    FI_HEADER = ".h"
    FI_SOURCE = ".cpp"
    FI_PRIVATE = "_p.h"

    def __init__(self, name):
        self.filename = name
        self.filedirname = os.path.dirname(name)
        self.filebasename = os.path.basename(name)
        self.keyname = None

    # example.h
    # example.cpp
    # example_p.h
    def filetype(self):
        prefix, suffix = self.filebasename.rsplit(".", 1)
        isprivate = False
        if prefix.endswith("_p"):
            prefix = prefix.rsplit("_", 1)[0]
            isprivate = True
        if not prefix in Config.PRO_FILELIST:
            return None
        else:
            self.keyname = prefix
            if "h" == suffix:
                if isprivate:
                    return FileInfo.FI_PRIVATE
                else:
                    return FileInfo.FI_HEADER
            elif "cpp" == suffix:
                return FileInfo.FI_SOURCE


##################################################
class Config:
    WORKDIR_INIT = None
    WORKDIR_DEST = None
    WORKDIR_NEED = "framework/qt/QmlFramework"
    PRO_FILELIST = ["NQText"] # test ok
    # PRO_FILELIST.append("NGSGPainterNode") # inherited vars conflicted with current re-name
    PRO_FILELIST.append("NQBorderImage")
    PRO_FILELIST.append("NQClearItem")
    PRO_FILELIST.append("NQDropShadow")
    PRO_FILELIST.append("NQFlickable")
    PRO_FILELIST.append("NQGestureItem")
    PRO_FILELIST.append("NQGlow")
    PRO_FILELIST.append("NQGridView")
    PRO_FILELIST.append("NQImageBase")
    PRO_FILELIST.append("NQImage")
    PRO_FILELIST.append("NQImageDecoder")
    PRO_FILELIST.append("NQImplicitSizeItem")
    # PRO_FILELIST.append("NQItem") # used outside
    PRO_FILELIST.append("NQItemView")
    PRO_FILELIST.append("NQItemViewTransition")
    PRO_FILELIST.append("NQLinearGradient")
    PRO_FILELIST.append("NQListView")
    PRO_FILELIST.append("NQMouseArea")
    PRO_FILELIST.append("NQMultiPointTouchArea")
    PRO_FILELIST.append("NQMultiPointTouchItem")
    PRO_FILELIST.append("NQOutline")
    PRO_FILELIST.append("NQPaintedItem")
    PRO_FILELIST.append("NQPositioners")
    PRO_FILELIST.append("NQRectangle")
    PRO_FILELIST.append("NQScaleGrid")
    PRO_FILELIST.append("NQShaderEffect")
    PRO_FILELIST.append("NQSourceProxy")
    PRO_FILELIST.append("NQSpecGestureItem")
    PRO_FILELIST.append("NQStyledText")
    PRO_FILELIST.append("NQTextControl")
    PRO_FILELIST.append("NQTextDocument")
    PRO_FILELIST.append("NQTextEdit")
    # PRO_FILELIST.append("NQTextNode") # used outside
    # PRO_FILELIST.append("NQTextNodeEngine") # used outside
    PRO_FILELIST.append("NQTextureProvider")
    PRO_FILELIST.append("NQTextureWatcher")
    PRO_FILELIST.append("NQTextUtil")
    PRO_FILELIST.append("NQTimeLine")
    PRO_FILELIST.append("NQTimer")
    PRO_FILELIST.append("NQTouchPadItem")
    PRO_FILELIST.append("NQTransition")
    PRO_FILELIST.append("NQTransitionManager")
    PRO_FILELIST.append("NQTriangle")

    CONFIG_DIR_IGNORE = ("Designer", "doc", "iautoqmlconfig", "qml",
                         "QmlAppLaunch", "tests",
                         "Animation", "API", "CustomControl", "mist",
                         "PVRT", "ResourceManager", "System", "WindowSystem")
    CONFIG_FILETYPE = r".+(\.h|\.cpp)$"

    def __str__(self):
        return "\
	WORKDIR_INIT=%s\n\
	WORKDIR_DEST=%s\n\
	WORKDIR_NEED=%s\n\
	PRO_FILELIST=%s" \
    % (Config.WORKDIR_INIT, \
       Config.WORKDIR_DEST, \
       Config.WORKDIR_NEED, \
       Config.PRO_FILELIST)

    @staticmethod
    def collectorinfo():
        print "===================="
        for filekey in FileCollector.FC_FILEDICT.keys():
            print filekey + ":"
            print "\theader:", FileCollector.FC_FILEDICT.get(filekey)[0]
            print "\tsource:", FileCollector.FC_FILEDICT.get(filekey)[1]
            print "\tprivate:", FileCollector.FC_FILEDICT.get(filekey)[2]
        print "===================="

    @staticmethod
    def filterfile(path):
        pattern = re.compile(Config.CONFIG_FILETYPE)
        obj = pattern.match(path)
        if obj is None:
            print path, "...ignored [f]"
            return
        assert(obj.group() == path)
        fi = FileInfo(path)
        ft = fi.filetype()
        if ft:
            if not fi.keyname in FileCollector.FC_FILEDICT:
                FileCollector.FC_FILEDICT[fi.keyname] = [None, None, None]
            if ft == FileInfo.FI_HEADER:
                assert FileCollector.FC_FILEDICT[fi.keyname][0] is None
                FileCollector.FC_FILEDICT[fi.keyname][0] = path
            elif ft == FileInfo.FI_SOURCE:
                assert FileCollector.FC_FILEDICT[fi.keyname][1] is None
                FileCollector.FC_FILEDICT[fi.keyname][1] = path
            elif ft == FileInfo.FI_PRIVATE:
                assert FileCollector.FC_FILEDICT[fi.keyname][2] is None
                FileCollector.FC_FILEDICT[fi.keyname][2] = path
            print path, "...matched [@]"
        else:
            print path, "...ignored [@]"

    @staticmethod
    def scanfiles(path):
        path_abs = os.path.abspath(path)
        if os.path.isfile(path_abs):
            Config.filterfile(path_abs)
            time.sleep(.001)
        elif os.path.isdir(path_abs):
            for afile in os.listdir(path_abs):
                if afile in Config.CONFIG_DIR_IGNORE:
                    print "%s/%s ...ignored [d]" % (path_abs, afile)
                    continue
                if afile.startswith("."):
                    print "%s/%s ...ignored [.]" % (path_abs, afile)
                    continue
                os.chdir(path_abs)
                Config.scanfiles(afile)

    @staticmethod
    def usage():
        print "******************************************************************"
        print "*\tusage:"
        print "*\t\tthis '%s' will re-name the class member variables of your codes." % (sys.argv[0])
        print "*\tformat:"
        print "*\t\tpython %s [options] <path>" % (sys.argv[0])
        print "*\t\tpath: must be 'QmlFramework' repository, both absolute and relative path are supported."
        print "*\t\toptions: -h --help"
        print "*\t\t\t-h: help usage"
        print "*\t\t\t--help: same as '-h'"
        print "******************************************************************"
        exit()

    @staticmethod
    def parseargs():
        print "parse args..."
        print "your command:",
        for arg in sys.argv:
            print arg,
        print
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        if len(args) != 1:
            Config.usage()
        else:
            if not os.path.exists(args[0]):
                logging.error("invalid path: " + args[0])
                exit()
            path = os.path.abspath(args[0])
            if not re.search(Config.WORKDIR_NEED, path):
                Config.usage()
            else:
                Config.WORKDIR_DEST = path
        for opt, value in opts:
            if opt in ["-h", "--help"]:
                Config.usage()
        Config.WORKDIR_INIT = os.path.abspath(".")
        # append all files
        # for filename in os.listdir(Config.WORKDIR_DEST + "/basicControl"):
        #     if filename.endswith(".cpp"):
        #         Config.PRO_FILELIST.append(filename.strip(".cpp"))
        print Config()
        print "args parsed successfully!"


##################################################
def main():
    print "**********@begin@**********\n"
    Config.parseargs()
    Config.scanfiles(Config.WORKDIR_DEST)
    Config.collectorinfo()
    FileCollector.parsefile()
    print "\n**********@end@**********"


##################################################
if "__main__" == __name__:
    main()
