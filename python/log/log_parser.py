#!/usr/bin/env python

import re

class LogItem(object):
    def __init__(self):
        super(LogItem, self).__init__()
        self.begin = False
        self.end = False
        self.transbegin = 0
        self.transend = 0
        self.transanim = 0
        self.fromview = ""
        self.fromscreen = ""
        self.toview = ""
        self.toscreen = ""
        self.view = []
        self.loadtime = {}
        self.preload = {}

class LogParser(object):
    LP_RE_NORMAL = r'(\d\d)-(\d\d)\s(\d\d):(\d\d):(\d\d)\.(\d\d\d)'
    LP_PATTERN_NORMAL = re.compile(LP_RE_NORMAL)
    LP_TRANS_BEGIN = r'^\d\d-\d\d\s(\d\d):(\d\d):(\d\d)\.(\d\d\d).+NQTransferManager::transView start'
    LP_TRANS_END = r'^\d\d-\d\d\s(\d\d):(\d\d):(\d\d)\.(\d\d\d).+NQTransferManager::onTransEnd.+'
    LP_TRANS_ANIM = r'^\d\d-\d\d\s\d\d:\d\d:\d\d\.\d\d\d.+NQTransView.+Anim.+cost=(\d+)ms'
    LP_FROM_VIEW = r'^\d\d-\d\d\s\d\d:\d\d:\d\d\.\d\d\d.+NQTransView.+from=(\w+)'
    LP_FROM_SCREEN = r'^\d\d-\d\d\s\d\d:\d\d:\d\d\.\d\d\d.+NQTransView.+fromScrn=(\w+)'
    LP_TO_VIEW = r'^\d\d-\d\d\s\d\d:\d\d:\d\d\.\d\d\d.+NQTransView.+to=(\w+)'
    LP_TO_SCREEN = r'^\d\d-\d\d\s\d\d:\d\d:\d\d\.\d\d\d.+NQTransView.+toScrn=(\w+)'
    LP_LOAD_TIME = r'^.+PerformanceTag.+NQQmlFileLoader::load.+load:\s(\w+)\.qml.+time:\s(\d+)\sms'

    lp_debug = True
    lp_logitemcount = 0
    lp_logitem = LogItem()

    @staticmethod
    def output():
        LogParser.lp_logitemcount += 1
        print "*" * 50,
        print LogParser.lp_logitemcount
        print "from: %s/%s to: %s/%s" %(LogParser.lp_logitem.fromview, LogParser.lp_logitem.fromscreen,
                                        LogParser.lp_logitem.toview, LogParser.lp_logitem.toscreen)
        count = len(LogParser.lp_logitem.view)
        for index in range(0, count):
            view = LogParser.lp_logitem.view[index]
            print "view: %s preload: %s loadtime: %s" %(view, LogParser.lp_logitem.preload[view], LogParser.lp_logitem.loadtime[view])
        print "transtime: %d" %(LogParser.lp_logitem.transend - LogParser.lp_logitem.transbegin - LogParser.lp_logitem.transanim)
        print "*" * 50,
        print LogParser.lp_logitemcount

    @staticmethod
    def parseline(lineno, line):
        if not LogParser.LP_PATTERN_NORMAL.search(line):
            return
        if not LogParser.lp_logitem.begin:
            match_begin = re.match(LogParser.LP_TRANS_BEGIN, line)
            if match_begin:
                _hour = int(match_begin.group(1))
                _min = int(match_begin.group(2))
                _sec = int(match_begin.group(3))
                _msec = int(match_begin.group(4))
                LogParser.lp_logitem.transbegin = _msec + _sec * 1000 + _min * 60000 + _hour * 3600000
                LogParser.lp_logitem.begin = True
                if LogParser.lp_debug:
                    print "debug: %d %s" %(lineno, line),
                    print "debug: %d=%d:%d:%d.%d" %(LogParser.lp_logitem.transbegin, _hour, _min, _sec, _msec)
        else:
            if not LogParser.lp_logitem.end:
                match_load = re.match(LogParser.LP_LOAD_TIME, line)
                if match_load:
                    _view = match_load.group(1)
                    _time = int(match_load.group(2))
                    LogParser.lp_logitem.view.append(_view)
                    LogParser.lp_logitem.loadtime[_view] = _time
                    LogParser.lp_logitem.preload[_view] = "N"
                    fd = open("preload_view", "r")
                    for line in fd:
                        if -1 != line.find(_view):
                            LogParser.lp_logitem.preload[_view] = "Y"
                    fd.close()
                    if LogParser.lp_debug:
                        print "debug:", LogParser.lp_logitem.view, LogParser.lp_logitem.preload, LogParser.lp_logitem.loadtime
                match_end = re.match(LogParser.LP_TRANS_END, line)
                if match_end:
                    _hour = int(match_end.group(1))
                    _min = int(match_end.group(2))
                    _sec = int(match_end.group(3))
                    _msec = int(match_end.group(4))
                    LogParser.lp_logitem.transend = _msec + _sec * 1000 + _min * 60000 + _hour * 3600000
                    LogParser.lp_logitem.end = True
                    if LogParser.lp_debug:
                        print "debug: %d %s" % (lineno, line),
                        print "debug: %d=%d:%d:%d.%d" % (LogParser.lp_logitem.transend, _hour, _min, _sec, _msec)
            match_fromview = re.match(LogParser.LP_FROM_VIEW, line)
            if match_fromview:
                LogParser.lp_logitem.fromview = match_fromview.group(1)
                if LogParser.lp_debug:
                    print "debug: fromview: %s" % (LogParser.lp_logitem.fromview),
            match_fromscreen = re.match(LogParser.LP_FROM_SCREEN, line)
            if match_fromscreen:
                LogParser.lp_logitem.fromscreen = match_fromscreen.group(1)
                if LogParser.lp_debug:
                    print "fromscreen: %s" % (LogParser.lp_logitem.fromscreen),
            match_toview = re.match(LogParser.LP_TO_VIEW, line)
            if match_toview:
                LogParser.lp_logitem.toview = match_toview.group(1)
                if LogParser.lp_debug:
                    print "toview: %s" % (LogParser.lp_logitem.toview),
            match_toscreen = re.match(LogParser.LP_TO_SCREEN, line)
            if match_toscreen:
                LogParser.lp_logitem.toscreen = match_toscreen.group(1)
                if LogParser.lp_debug:
                    print "toscreen: %s" % (LogParser.lp_logitem.toscreen)
            match_anim = re.match(LogParser.LP_TRANS_ANIM, line)
            if match_anim:
                LogParser.lp_logitem.transanim = int(match_anim.group(1))
                if LogParser.lp_debug:
                    print "debug: %d=%d-%d-%d(anim)" % (
                    LogParser.lp_logitem.transend - LogParser.lp_logitem.transbegin - LogParser.lp_logitem.transanim,
                    LogParser.lp_logitem.transend,
                    LogParser.lp_logitem.transbegin,
                    LogParser.lp_logitem.transanim)
        if LogParser.lp_logitem.begin and LogParser.lp_logitem.end:
            match_begin = re.match(LogParser.LP_TRANS_BEGIN, line)
            if -1 == lineno or match_begin:
                LogParser.output()
                LogParser.lp_logitem = LogItem()
                LogParser.parseline(lineno, line)

def main():
    print "\n========== begin ==========\n"

    fd = open("trans.log", "r")
    for lineno, line in enumerate(fd):
        LogParser.parseline(lineno, line)
    LogParser.parseline(-1, "00-00 00:00:00.000")
    fd.close()

    print "\n========== end ==========\n"

if '__main__' == __name__:
    main()