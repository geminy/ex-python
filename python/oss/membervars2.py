##################################################
# MEMBER VARIANTS RULE                           #
# NICE: LINENO:WORDPOS                           #
##################################################


import re
import sys
import os
import getopt


# type name;
# type: no space
# name: maybe bit
def rename_simple(filepath, beginno, endno):
    print "********** rename begin **********"
    print filepath, beginno, endno
    fd = open(filepath, "r")
    for lineno, line in enumerate(fd):
        if beginno <= lineno + 1 <= endno:
            if line.find(";") != -1 and line.find("(") == -1:
                wordlist = line.split()
                if len(wordlist) >= 2:
                    mname = wordlist[1].strip(";").strip("*").strip("&").strip(":")
                    pos = line.find(mname)
                    if mname.startswith("m_nq"):
                        pass
                    elif mname.startswith("m_"):
                        line = line[:pos + 2] + "nq" + line[pos + 2:]
                    # elif mname.startswith("m"):
                    #     line = line[:pos + 1] + "_nq" + line[pos + 1:]
                    else:
                        line = line.replace(mname, "m_nq" + mname)
            print line,
    fd.close()
    print "********** rename end **********"


def replace_help(astring, keyword, prefix = "m_nq", suffix = None):
    line = astring
    _keyword = keyword
    _prefix = prefix
    linelen = len(line)
    wordlen = len(_keyword)
    prelen = len(_prefix)
    findpos = 0
    pos = line.find(keyword, findpos)
    while -1 != pos:
        canreplace = True
        if pos > 0:
            if re.match(r"\w|_", line[pos - 1]):
                canreplace = False
        if pos + wordlen < linelen:
            if re.match(r"\w|_", line[pos + wordlen]):
                canreplace = False
        if canreplace:
            if _keyword.startswith("m_nq"):
                pass
            elif _keyword.startswith("m_"):
                line = line[:pos + 2] + "nq" + line[pos + 2:]
                findpos = pos + 2 + wordlen
            # elif _keyword.startswith("m"):
            #     line = line[:pos + 1] + "_nq" + line[pos + 1:]
            #     findpos = pos + 3 + wordlen
            else:
                line = line[:pos] + _prefix + line[pos:]
                findpos = pos + prelen + wordlen
        else:
            findpos = pos + wordlen
        pos = line.find(keyword, findpos)
    return line


def parse_errors(obj):
    print "********** parse error begin **********"
    # key: filepath
    # value: {"lineno:wordpos": keyword}
    filepathdict = {}
    # key: filepath
    # value: [line]
    filecontentdict = {}
    fd = open(obj, "r")
    # finds filepath:{"lineno:wordpos": keyword}
    for line in fd:
        found = False
        linesplit = line.split(":")
        filepath = linesplit[0]
        lineno = linesplit[1]
        wordpos = linesplit[2]
        innerkey = str(lineno) + ":" + str(wordpos)
        keywords = linesplit[-1]
        keyword = re.match(r"^\s*'(.+)'\swas\snot\sdeclared\sin\sthis\sscope", keywords)
        if keyword:
            found = True
            keyword = keyword.group(1)
        if not found:
            keyword = re.match(r"^\s*(class|struct)\s'.+'\sdoes\snot\shave\sany\sfield\snamed\s'(.+)'", keywords)
            if keyword:
                found = True
                keyword = keyword.group(2)
            if not found:
                keyword = re.match(r"^\s*.+'\sdoes\snot\shave\sany\sfield\snamed\s'(.+)'", keywords)
                if keyword:
                    found = True
                    keyword = keyword.group(1)
        if not found:
            keyword = re.match(r"^\s*'(const\s|)(class|struct)\s.+'\shas\sno\smember\snamed\s'(.+)'", keywords)
            if keyword:
                found = True
                keyword = keyword.group(3)
            if not found:
                keyword = re.match(r"^\s*.+'\shas\sno\smember\snamed\s'(.+)'", keywords)
                if keyword:
                    found = True
                    keyword = keyword.group(1)

        if found:
            if filepath not in filepathdict:
                filepathdict[filepath] = {}
            if innerkey in filepathdict[filepath].keys():
                print "error:[conflicted] %s %s" % (filepath, innerkey)
                del filepathdict[filepath][innerkey]
                # exit()
            else:
                filepathdict[filepath][innerkey] = keyword
        else:
            print "warning:[not matched]", line,

    for filepath in filepathdict.keys():
        print "----------"
        print filepath
        print filepathdict[filepath]
        print "----------"
    fd.close()

    # replace
    for filepath in filepathdict:
        if filepath not in filecontentdict:
            filecontentdict[filepath] = []
        # key: lineno
        # value: {wordpos:keyword}
        _filepathdict = {}
        # re-finds by line
        for innerkey in filepathdict[filepath].keys():
            lineno = str(innerkey.split(":")[0])
            wordpos = str(innerkey.split(":")[1])
            if lineno not in _filepathdict.keys():
                _filepathdict[lineno] = {}
            _filepathdict[lineno][wordpos] = filepathdict[filepath][innerkey]
        fd = open(filepath, "r")
        for lineno, line in enumerate(fd):
            if str(lineno + 1) in _filepathdict.keys():
                worddict = _filepathdict[str(lineno + 1)]
                wordposlist = worddict.keys()
                wordposlist = sorted(wordposlist, key=lambda x:int(x))
                posadd = 0
                for wordpos in wordposlist:
                    word = worddict[wordpos]
                    wordpos = int(wordpos) - 1 + posadd
                    # strip m_nq
                    if word.startswith("m_nq"):
                        line = line[:wordpos] + line[wordpos + 4:]
                        posadd -= 4
                    # add nq
                    elif word.startswith("m_"):
                        line = line[:wordpos + 2] + "nq" + line[wordpos + 2:]
                        posadd += 2
                    # add _nq
                    # elif word.startswith("m"):
                    #     line = line[:wordpos + 1] + "_nq" + line[wordpos + 1:]
                    #     posadd += 3
                    # add m_nq
                    else:
                        line = line[:wordpos] + "m_nq" + line[wordpos:]
                        posadd += 4
            filecontentdict[filepath].append(line)
        fd.close()

    # complete
    for filepath in filecontentdict:
        fd = open(filepath, "w")
        for line in filecontentdict[filepath]:
            fd.write(line)
        fd.close()

    print "********** parse error end **********"


def main():
    filepath = None
    beginno = None
    endno = None
    parseerror = False

    opts, args = getopt.getopt(sys.argv[1:], "f:b:e:", ["error"])
    if 0 < len(args):
        print "error: invalid args [%s]!!" % (sys.argv[1:])
        exit()
    for opt, value in opts:
        if "-f" == opt:
            filepath = os.path.abspath(value)
            if not os.path.exists(filepath):
                print "error: [%s] not exists!!" % (filepath)
                exit()
        elif "-b" == opt:
            beginno = int(value)
        elif "-e" == opt:
            endno = int(value)
        elif "--error" == opt:
            parseerror = True

    if parseerror:
        parse_errors("errors")

    if filepath and beginno and endno:
        rename_simple(filepath, beginno, endno)


if "__main__" == __name__:
    main()