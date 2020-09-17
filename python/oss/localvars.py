##################################################
# RENAME LOCAL VARS:                             #
#     a) args of function                        #
#     b) vars in function block                  #
##################################################


import sys
import getopt
import os
import time
import re
import logging


##################################################
class Config:
    WORKDIR_INIT = None
    WORKDIR_DEST = None
    WORKDIR_NEED = "framework/qt/QmlFramework"
    PRO_ARGS = False
    PRO_VARS = False
    PRO_FILELIST = ["NQText"]

    def __str__(self):
        return "\
	WORKDIR_INIT=%s\n\
	WORKDIR_DEST=%s\n\
	WORKDIR_NEED=%s\n\
	PRO_ARGS=%s\n\
	PRO_VARS=%s\n\
	PRO_FILELIST=%s" \
    % (Config.WORKDIR_INIT, \
       Config.WORKDIR_DEST, \
       Config.WORKDIR_NEED, \
       Config.PRO_ARGS, \
       Config.PRO_VARS, \
       Config.PRO_FILELIST)


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
class FileParser(object):
    FP_FINDCLASS_BEGIN = r"^\s*(class)\s+(NG_EXPORT)\s+(\S+).*"
    FP_FINDCLASS_BEGIN2 = r"^\s*(class)\s+(\S+).*"
    FP_FINDCLASS_END = r"^\s*(\};)"
    FP_FINDSTRUCT_BEGIN = r"^\s*(struct)\s+(NG_EXPORT)\s+(\S+).*"
    FP_FINDSTRUCT_BEGIN2 = r"^\s*(struct)\s+(\S+).*"
    FP_FINDENUM_BEGIN = r"^\s*(enum)\s+(\S+).*"
    FP_FINDENUM_ONELINE = ("{", "}", ";")
    FP_FINDENUM_RETTYPE = ("(", ")", ";")

    FP_DIRTY_SLASH = r"\s*//"
    FP_DIRTY_ASTERISK = r"\s*/\*.*\*/"
    FP_DIRTY_ASTERICK_BEGIN = r"\s*/\*"
    FP_DIRTY_ASTERICK_END = r".*\*/"
    FP_DIRTY_SIGN_BEGIN = r"\s*#(if|ifdef|ifndef)\s+\S+"
    FP_DIRTY_SIGN_END = r"\s*#endif"
    
    FP_CM_ARGS = r"^\s*.+\((.*)\)"
    FP_CM_ARGS_PREFIX_U = "_"
    FP_CM_ARGS_PREFIX_NQ = "nq"
    FP_CM_ARGS_PREFIX_UNQ = "_nq"

    def __init__(self, basename, filelist):
        super(FileParser, self).__init__()
        # without suffix
        self.basename = basename
        # [header, source, private]
        self.filelist = filelist

        # header
        self.classfound = False # may be embeded
        self.classname = None # current class name, only for class
        self.headercache = [] # line
        self.classesdict = {} # class/struct/enum: [beginno, endno]
        self.classdict = {} # class: [beginno, endno]
        self.headercache_p = []
        self.classesdict_p = {}
        self.classdict_p = {}

        # source
        self.sourcecache = [] # line
        self.classnamelist = [] # from classdict and classdict_p
        self.cmdict = {} # linenobegin: name
        self.cmblockdict = {} # linenobegin: linenoend
        self.cmlineno = None # current class method linenobegin
        self.cmfound = False # class method name
        self.cmentered = False # class method block
        self.cmbrace = [-1, -1] # class method block [beginno, endno]

        # dirty for source
        self.dirtyfound = False # multi-line
        self.dirtylist = [] # lineno
        self.dirtyflag = [[0, 0], [0, 0]] # [comment, pre-processor] [beginno, endno]
        self.dirtysign = False # pre-processor
        self.fileissafe = True # False if "{" or "}" in method block while dirtysign is True

    def __cleardata(self):
        self.classfound = False
        self.classname = None

    # note: embeded class
    def __saveclass(self, name, lineno, line, filetype, entry = True):
        # begin
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
        # end
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

    # for .h
    def __findclass(self, lineno, line, filetype):
        classname = None
        reresult = None
        # begin
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
        # end
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

    # for .cpp
    def __finddirty(self, lineno, line):
        # end
        if self.dirtyfound:
            self.dirtylist.append(lineno)
            # */ dirtyflag[0] [1, 1]
            if 1 == self.dirtyflag[0][0]:
                if re.match(FileParser.FP_DIRTY_ASTERICK_END, line):
                    self.dirtyflag[0][1] = 1
                if self.dirtyflag[0][0] == self.dirtyflag[0][1]:
                    self.dirtyfound = False
                    self.dirtyflag[0] = [0, 0]
            # #endif dirtyflag[1] [n, n]
            elif self.dirtyflag[1][0] > 0:
                # #if embeded
                if re.match(FileParser.FP_DIRTY_SIGN_BEGIN, line):
                    self.dirtyflag[1][0] += 1
                # #endif
                elif re.match(FileParser.FP_DIRTY_SIGN_END, line):
                    self.dirtyflag[1][1] += 1
                if self.dirtyflag[1][0] == self.dirtyflag[1][1]:
                    self.dirtyfound = False
                    self.dirtyflag[1] = [0, 0]
                    self.dirtysign = False
            else:
                logging.error("[__finddirty]" + str(lineno) + ":" + line)
                exit()
        # begin
        else:
            for i in (0, 1):
                for j in (0, 1):
                    assert 0 == self.dirtyflag[i][j]
            # //
            if re.match(FileParser.FP_DIRTY_SLASH, line):
                self.dirtylist.append(lineno)
                return
            # /**/
            if re.match(FileParser.FP_DIRTY_ASTERISK, line):
                self.dirtylist.append(lineno)
                return
            # /* dirtyflag[0] [1, 0]
            if re.match(FileParser.FP_DIRTY_ASTERICK_BEGIN, line):
                self.dirtylist.append(lineno)
                self.dirtyflag[0][0] = 1
                self.dirtyfound = True
            # #if dirtyflag[1] [1, 0]
            if re.match(FileParser.FP_DIRTY_SIGN_BEGIN, line):
                self.dirtylist.append(lineno)
                self.dirtyflag[1][0] = 1
                self.dirtyfound = True
                self.dirtysign = True

    # note: the rule for re is simple
    def __findclassmethod(self, lineno, line):
        if lineno in self.dirtylist:
            return
        if self.cmfound:
            return
        # simple return type
        rettype = r"^\s*(\S+)\s+"
        # simple method name and no wrapped
        methodname = r"::(\w+)\(.*\)"
        for clsname in self.classnamelist:
            cm = rettype + clsname + methodname
            recm = re.match(cm, line)
            if recm:
                assert lineno not in self.cmdict.keys()
                self.cmdict[lineno] = clsname + "::" + recm.group(2)
                self.cmfound = True
                self.cmlineno = lineno

    # finds class method block
    def __processclassmethod(self, lineno, line):
        if self.cmfound:
            # end
            if self.cmentered:
                if self.dirtysign:
                    if line.find("{") != -1 or line.find("}") != -1:
                        self.fileissafe = False
                        return
                if line.find("{") != -1 and lineno not in self.dirtylist:
                    self.cmbrace[0] += 1
                if line.find("}") != -1 and lineno not in self.dirtylist:
                    self.cmbrace[1] += 1
                if self.cmbrace[0] == self.cmbrace[1]:
                    self.cmblockdict[self.cmlineno] = lineno
                    self.cmentered = False
                    self.cmbrace = [-1, -1]
                    self.cmfound = False
                    self.__preparerename()
            # begin
            else:
                assert lineno not in self.cmblockdict.keys()
                self.cmblockdict[lineno] = -1
                self.cmentered = True
                assert 2 == len(self.cmbrace)
                assert -1 == self.cmbrace[0]
                assert -1 == self.cmbrace[1]
                if -1 != line.find("{"):
                    self.cmbrace[0] = 1
                if -1 != line.find("}"):
                    self.cmbrace[1] = 1
                if 1 ==  self.cmbrace[0] and 1 == self.cmbrace[1]:
                    self.cmblockdict[lineno] = lineno
                    self.cmentered = False
                    self.cmbrace = [-1, -1]
                    self.cmfound = False
                    self.__preparerename()

    # for args
    def __dorename(self, argdict):
        # header
        canrename_h = False
        clsmethodpos = ""
        # [lineno, line]
        line_h = [-1, ""]
        classname, methodname = self.cmdict[self.cmlineno].rsplit("::", 1)
        # note: simple re
        pattern = r"^\s*(\S+)\s+" + methodname + r"\(.+\);"
        if classname in self.classdict:
            for lineno in range(self.classdict[classname][0], self.classdict[classname][1] + 1):
                if lineno in self.dirtylist:
                    continue
                if re.match(pattern, self.headercache[lineno]):
                    line_h[1] = self.headercache[lineno]
                    reret = re.match(FileParser.FP_CM_ARGS, line_h[1]).group(1)
                    if reret:
                        argnamelist = []
                        for arg in reret.split(","):
                            # args only type, without name
                            if len(arg.split()) < 2:
                                continue
                            arg = arg.split()[-1]
                            arg = arg.rsplit("&")[-1]
                            arg = arg.rsplit("*")[-1]
                            # args only type, without name, too
                            if len(arg) < 1:
                                continue
                            assert arg not in argnamelist
                            argnamelist.append(arg)
                        # ignores args type of overloadded class method
                        if sorted(argnamelist) == sorted(argdict.keys()):
                            cangoon = True
                            for arg in argdict.keys():
                                if line_h[1].count(arg) > 1 or line_h[1].count(argdict[arg]) > 0:
                                    cangoon = False
                                    break
                            if cangoon:
                                if not canrename_h:
                                    line_h[0] = lineno
                                    for arg in argdict.keys():
                                        line_h[1] = line_h[1].replace(arg, argdict[arg])
                                    canrename_h = True
                                    clsmethodpos = "header"
                                else:
                                    print "warning: conflicted:", self.cmdict[self.cmlineno]
                                    canrename_h = False
                                    # exit()
        elif classname in self.classdict_p:
            for lineno in range(self.classdict_p[classname][0], self.classdict_p[classname][1] + 1):
                if lineno in self.dirtylist:
                    continue
                if re.match(pattern, self.headercache_p[lineno]):
                    line_h[1] = self.headercache_p[lineno]
                    reret = re.match(FileParser.FP_CM_ARGS, line_h[1]).group(1)
                    if reret:
                        argnamelist = []
                        for arg in reret.split(","):
                            # args only type, without name
                            if len(arg.split()) < 2:
                                continue
                            arg = arg.split()[-1]
                            arg = arg.rsplit("&")[-1]
                            arg = arg.rsplit("*")[-1]
                            # args only type, without name, too
                            if len(arg) < 1:
                                continue
                            assert arg not in argnamelist
                            argnamelist.append(arg)
                        # ignores args type of overloadded class method
                        if sorted(argnamelist) == sorted(argdict.keys()):
                            cangoon = True
                            for arg in argdict.keys():
                                if line_h[1].count(arg) > 1 or line_h[1].count(argdict[arg]) > 0:
                                    cangoon = False
                                    break
                            if cangoon:
                                if not canrename_h:
                                    line_h[0] = lineno
                                    for arg in argdict.keys():
                                        line_h[1] = line_h[1].replace(arg, argdict[arg])
                                    canrename_h = True
                                    clsmethodpos = "private"
                                else:
                                    print "warning: conflicted:", self.cmdict[self.cmlineno]
                                    canrename_h = False
                                    # exit()
        else:
            logging.error("invalid class: " + classname)
            exit()
        if not canrename_h:
            return
        # header rename
        if clsmethodpos == "header":
            self.headercache[line_h[0]] = line_h[1]
        else:
            self.headercache_p[line_h[0]] = line_h[1]
        # source rename
        cmblock = []
        for lineno in range(self.cmlineno, self.cmblockdict[self.cmlineno] + 1):
            cmblock.append(self.sourcecache[lineno])
            if lineno in self.dirtylist and self.dirtysign is False:
                continue
            for arg in argdict.keys():
                cmblock[-1] = cmblock[-1].replace(arg, argdict[arg])
                self.sourcecache[lineno] = cmblock[-1]
        # for line in cmblock:
        #     print line,

    # replace strategy:repeat time limitation
    def __canrename(self, arglist, mosttime):
        for lineno in range(self.cmlineno, self.cmblockdict[self.cmlineno] + 1):
            if lineno in self.dirtylist and self.dirtysign is False:
                continue
            for arg in arglist:
                line = self.sourcecache[lineno]
                if line.count(arg) > mosttime:
                    return False
                # xxxargxxx
                # .arg
                # ->arg
                if line.count(arg) == 1:
                    argindex = line.find(arg)
                    arglen = len(arg)
                    if argindex - 1 >= 0:
                        argpre = line[argindex -1]
                        if re.match(r"\w", argpre):
                            return False
                        elif argpre in [".", ">"]:
                            return False
                    if argindex + arglen <= len(line) - 1:
                        argrear = line[argindex + arglen]
                        if re.match(r"\w", argrear):
                            return False
        return True

    # Config.PRO_ARGS - FileParser.FP_CM_ARGS_PREFIX_NQ
    # Config.PRO_VARS - FileParser.FP_CM_ARGS_PREFIX_U
    def __preparerename(self):
        # 1 ()
        if Config.PRO_ARGS:
            line = self.sourcecache[self.cmlineno]
            reret = re.match(FileParser.FP_CM_ARGS, line).group(1)
            if reret:
                argnamedict = {}
                for arg in reret.split(","):
                    arg = arg.split()[-1]
                    arg = arg.rsplit("&")[-1]
                    arg = arg.rsplit("*")[-1]
                    assert arg not in argnamedict.keys()
                    argnamedict[arg] = FileParser.FP_CM_ARGS_PREFIX_NQ + arg
                if self.__canrename(argnamedict.keys(), 1):
                    if self.__canrename(argnamedict.values(), 0):
                        self.__dorename(argnamedict)
        # 2 {}
        if Config.PRO_VARS:
            vardict = {}
            docmblock = False
            for lineno in range(self.cmlineno, self.cmblockdict[self.cmlineno] + 1):
                line = self.sourcecache[lineno]
                # rule??
                if line.find(";") != -1 and line.find("=") != -1:
                    # type var =x yyy;
                    equalindex = line.find("=")
                    if line[equalindex + 1] == "=":
                        continue
                    localvar = line.split("=")[0]
                    if len(localvar.split()) == 2:
                        avar = localvar.split()[-1]
                        avar = avar.rsplit("*")[-1]
                        avar = avar.rsplit("&")[-1]
                        # weird re result
                        if not re.match(r"^[_|\w][_|\w]*[_|\w]$", avar):
                            continue
                        avarlist = []
                        avarlist.append(avar)
                        newvar = FileParser.FP_CM_ARGS_PREFIX_U + avar
                        newvarlist = []
                        newvarlist.append(newvar)
                        if self.__canrename(avarlist, 1):
                            if self.__canrename(newvarlist, 0):
                                vardict[avar] = newvar
                                docmblock = True
            if not docmblock:
                return
            cmblock = []
            for lineno in range(self.cmlineno, self.cmblockdict[self.cmlineno] + 1):
                line = self.sourcecache[lineno]
                line = line.replace(vardict.keys()[0], vardict[vardict.keys()[0]])
                cmblock.append((lineno, line))
                # block rename
                self.sourcecache[lineno] = line
            # for index in cmblock:
            #     print index[0], index[1],

    def __showclassmethod(self):
        print "SAFE=[%s]" % (self.fileissafe)
        print self.classnamelist
        keylist = sorted(self.cmdict.keys())
        for akey in keylist:
            print akey, self.cmdict[akey], self.cmblockdict.get(akey, "[Default]")

    # filelist[header, source, private]
    # True: at least header or private and source are non-None
    def parseready(self):
        assert 3 == len(self.filelist)
        if self.filelist[0] and self.filelist[1]:
            return True
        elif self.filelist[2] and self.filelist[1]:
            return True
        else:
            return False

    def parseheader(self):
        print self.basename, self.filelist[0]
        if self.filelist[0] is None:
            return
        fd = open(self.filelist[0], "r")
        for lineno, line in enumerate(fd):
            self.__findclass(lineno, line, FileInfo.FI_HEADER)
            self.headercache.append(line)
        fd.close()

    def parseprivate(self):
        print self.basename, self.filelist[2]
        if self.filelist[2] is None:
            return
        self.__cleardata()
        fd = open(self.filelist[2], "r")
        for lineno, line in enumerate(fd):
            self.__findclass(lineno, line, FileInfo.FI_PRIVATE)
            self.headercache_p.append(line)
        fd.close()

    def parsesource(self):
        print self.basename, self.filelist[1]
        assert self.filelist[1] is not None
        for clsnm in self.classdict:
            self.classnamelist.append(clsnm)
        for clsnm in self.classdict_p:
            self.classnamelist.append(clsnm)
        fd = open(self.filelist[1], "r")
        for lineno, line in enumerate(fd):
            self.sourcecache.append(line)
            self.__finddirty(lineno, line)
            self.__findclassmethod(lineno, line)
            if self.fileissafe:
                self.__processclassmethod(lineno, line)
        fd.close()
        # self.__showclassmethod()

    def complete(self):
        if not self.fileissafe:
            print self.basename, "@ unsafe"
        else:
            # header
            if self.filelist[0]:
                fd = open(self.filelist[0], "w")
                for line in self.headercache:
                    fd.write(line)
                fd.close()
            # source
            assert self.filelist[1] is not None
            fd = open(self.filelist[1], "w")
            for line in self.sourcecache:
                fd.write(line)
            fd.close()
            # private
            if self.filelist[2]:
                fd = open(self.filelist[2], "w")
                for line in self.headercache_p:
                    fd.write(line)
                fd.close()
            print self.basename, "@ completed"


##################################################
class FileCollector:
    FC_DIR_IGNORE = ("Designer", "doc", "iautoqmlconfig", "qml", "QmlAppLaunch", "tests",
                     "Animation", "API", "CustomControl", "mist", "PVRT", "ResourceManager", "System", "WindowSystem")
    FC_FILETYPE = r".+(\.h$|\.cpp$)"
    # key: in Config.PRO_FILELIST
    # value: [header, source, private]
    FC_FILEDICT = {}

    @staticmethod
    def findfile(path):
        fi = FileInfo(path)
        ft = fi.filetype()
        if ft:
            if not fi.keyname in FileCollector.FC_FILEDICT:
                FileCollector.FC_FILEDICT[fi.keyname] = [None, None, None]
            if ft == FileInfo.FI_HEADER:
                FileCollector.FC_FILEDICT[fi.keyname][0] = path
            elif ft == FileInfo.FI_SOURCE:
                FileCollector.FC_FILEDICT[fi.keyname][1] = path
            elif ft == FileInfo.FI_PRIVATE:
                FileCollector.FC_FILEDICT[fi.keyname][2] = path
            print "%s @ OK" % (path)
        else:
            print "%s > NG" % (path)

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
    def parsefile():
        for filekey in FileCollector.FC_FILEDICT:
            fp = FileParser(filekey, FileCollector.FC_FILEDICT[filekey])
            if not fp.parseready():
                print "warning: %s not a pair(h/cpp) and ignored" % (filekey)
                continue
            fp.parseheader()
            fp.parseprivate()
            fp.parsesource()
            fp.complete()


##################################################
def filterfile(path):
    pattern = re.compile(FileCollector.FC_FILETYPE)
    obj = pattern.match(path)
    if obj is None:
        print path, "...ignored"
        return
    print obj.group(), "...matched"
    FileCollector.findfile(path)


##################################################
def scanfile(path):
    path_abs = os.path.abspath(path)
    if os.path.isfile(path_abs):
        filterfile(path_abs)
        time.sleep(.001)
    elif os.path.isdir(path_abs):
        for afile in os.listdir(path_abs):
            if afile in FileCollector.FC_DIR_IGNORE:
                print "%s/%s ...ignored" % (path_abs, afile)
                continue
            if afile.startswith("."):
                print "%s/%s ...ignored" % (path_abs, afile)
                continue
            os.chdir(path_abs)
            scanfile(afile)


##################################################
def scanfiles():
    scanfile(Config.WORKDIR_DEST)


##################################################
def usage():
    print "******************************************************************"
    print "*\tusage:"
    print "*\t\tthis '%s' will re-name the local variables of your codes, " \
          "includes args of function and vars of function block." % (sys.argv[0])
    print "*\tformat:"
    print "*\t\tpython %s [options] <path>" % (sys.argv[0])
    print "*\t\tpath: must be 'QmlFramework' repository, both absolute and relative path are supported."
    print "*\t\toptions: -a -v --all --help"
    print "*\t\t\t-a: re-name for args of function"
    print "*\t\t\t-v: re-name for vars of function block"
    print "*\t\t\t--all: means '-a' and '-v'"
    print "*\t\t\t--help: help usage"
    print "*\tnote:"
    print "*\t\tat least one of '-a' '-v' and '--all' is needed."
    print "******************************************************************"
    exit()


##################################################
def checkinput():
    print "input checking..."
    print "your command:",
    for arg in sys.argv:
        print arg,
    print
    opts, args = getopt.getopt(sys.argv[1:], "av", ["help", "all"])
    if len(args) != 1:
        usage()
    else:
        if not os.path.exists(args[0]):
            logging.error("invalid path: " + args[0])
            exit()
        path = os.path.abspath(args[0])
        if not re.search(Config.WORKDIR_NEED, path):
            usage()
        else:
            Config.WORKDIR_DEST = path
    for opt, value in opts:
        if "--help" == opt:
            usage()
        elif "-a" == opt:
            Config.PRO_ARGS = True
        elif "-v" == opt:
            Config.PRO_VARS = True
        elif "--all" == opt:
            Config.PRO_ARGS = True
            Config.PRO_VARS = True
    if Config.PRO_ARGS is False and Config.PRO_VARS is False:
        usage()
    Config.WORKDIR_INIT = os.path.abspath(".")
    for filename in os.listdir(Config.WORKDIR_DEST + "/basicControl"):
        if filename.endswith(".cpp"):
            Config.PRO_FILELIST.append(filename.strip(".cpp"))
    print Config()
    print "input checked successfully!"


##################################################
def main():
    print "!!!!!!!!!!begin!!!!!!!!!!"
    # 1 confirms command line args
    checkinput()
    # 2 filters some files
    scanfiles()
    # 3 files will be processed
    FileCollector.collectorinfo()
    # 4 real work
    FileCollector.parsefile()
    print "!!!!!!!!!!end!!!!!!!!!!"


##################################################
if "__main__" == __name__:
    main()
