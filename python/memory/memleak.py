##################################################
# FINDS NEW FOR MEMORY LEAK                      #
##################################################


import os


SourceTuple = ("QtWindowManager.source", "QmlFramework.source")


def main():
    print "********** begin **********"

    for source in SourceTuple:
        print source, "processing..."
        newsource = source.replace("source", "new")
        fd = open(source, "r")
        fd2 = open(newsource, "w")
        for line in fd:
            newindex = line.rfind("new")
            assert(-1 != newindex)
            line = line[newindex:]
            line = line.split()[1]
            line = line.split("(")[0]
            line = line.split(";")[0]
            line = "new " + line
            fd2.write(line + os.linesep)
        fd.close()
        fd2.close()
        print newsource, "done!"

    print "********** end **********"


if "__main__" == __name__:
    main()
