#!/usr/bin/env python

import os

class DayTime(object):
    def __init__(self):
        super(DayTime, self).__init__()
        self.year = 0
        self.month = 0
        self.day = 0
        self.weekday = 0
        self.onhour = 0
        self.onminute = 0
        self.onsecond = 0
        self.offhour = 0
        self.offminute = 0
        self.offsecond = 0
        self.overhour = 0.0

    def caclovertime(self):
        if self.day in WorkTime.WT_WEEKENDS:
            if 0 != self.onhour and 0 != self.offhour:
                self.overhour = self.offhour * 3600 + self.offminute * 60 + self.offsecond \
                                - self.onhour * 3600 - self.onminute * 60 - self.onsecond
        else:
            if self.onhour >= WorkTime.WT_ONTIME:
                self.overhour = self.offhour * 3600 + self.offminute * 60 + self.offsecond \
                                - self.onhour * 3600 - self.onminute * 60 - self.onsecond \
                                - WorkTime.WT_WORKTIME * 3600 - WorkTime.WT_SUPPERTIME * 3600
            else:
                self.overhour = self.offhour * 3600 + self.offminute * 60 + self.offsecond \
                                - WorkTime.WT_ONTIME * 3600 - 0 * 60 - 0 \
                                - WorkTime.WT_WORKTIME * 3600 - WorkTime.WT_SUPPERTIME * 3600
            if self.overhour < 0.0:
                self.overhour = 0.0
        self.overhour /= 3600.0
        self.overhour = round(self.overhour, 1)

class WorkTime(object):
    WT_YEAR = 2017
    WT_MONTH = 8
    WT_DAYS = 31
    WT_FIRSTDAYTOWEEK = 2
    WT_WEEKENDS = ()
    WT_ONTIME = 9
    WT_OFFTIME = 18
    WT_MIDOFFTIME = 12.5
    WT_MIDONTIME = 13.5
    WT_SUPPERTIME = 0.5
    WT_WORKTIME = 8 + 1
    WT_SUFFIX =".wt"

    def __init__(self):
        super(WorkTime, self).__init__()
        self.daytimelist = []

    def initfile(self):
        wtname = str(WorkTime.WT_YEAR) + self._int2string(WorkTime.WT_MONTH) + WorkTime.WT_SUFFIX
        if os.path.exists(wtname):
            print "info: %s exists." %(wtname)
            return
        wtfile = open(wtname, "w")
        wday = WorkTime.WT_FIRSTDAYTOWEEK
        for day in range(1, WorkTime.WT_DAYS + 1):
            dt = DayTime()
            dt.year = WorkTime.WT_YEAR
            dt.month = WorkTime.WT_MONTH
            dt.day = day
            dt.weekday = wday
            wday += 1
            if wday > 7:
                wday = 1
            wtfile.write(str(dt.year) + "-" + self._int2string(dt.month) + "-" + self._int2string(dt.day))
            wtfile.write(" " + str(dt.weekday))
            wtfile.write(" " + self._int2string(dt.onhour) + ":" + self._int2string(dt.onminute) + ":" + self._int2string(dt.onsecond))
            wtfile.write(" " + self._int2string(dt.offhour )+ ":" + self._int2string(dt.offminute) + ":" + self._int2string(dt.offsecond))
            wtfile.write(" " + str(dt.overhour))
            wtfile.write("\n")
        wtfile.close()

    def caclovertime(self):
        wtname = str(WorkTime.WT_YEAR) + self._int2string(WorkTime.WT_MONTH) + WorkTime.WT_SUFFIX
        if not os.path.exists(wtname):
            print "error: %s not exists." % (wtname)
            return
        wtfile = open(wtname, "r")
        for line in wtfile:
            wtlist = line.split()
            dt = DayTime()
            dt.year = int(wtlist[0].split("-")[0])
            dt.month = self._string2int(wtlist[0].split("-")[1])
            dt.day = self._string2int(wtlist[0].split("-")[2])
            dt.weekday = int(wtlist[1])
            dt.onhour = self._string2int(wtlist[2].split(":")[0])
            dt.onminute = self._string2int(wtlist[2].split(":")[1])
            dt.onsecond = self._string2int(wtlist[2].split(":")[2])
            dt.offhour = self._string2int(wtlist[3].split(":")[0])
            dt.offminute = self._string2int(wtlist[3].split(":")[1])
            dt.offsecond = self._string2int(wtlist[3].split(":")[2])
            dt.caclovertime()
            self.daytimelist.append(dt)
        wtfile.close()

    def output(self):
        overdaytime = 0.0
        overendtime = 0.0
        for line in self.daytimelist:
            print "%d-%02d-%02d %d %02d:%02d:%02d %02d:%02d:%02d %.1f" %(
                line.year, line.month, line.day, line.weekday,
                line.onhour, line.onminute, line.onsecond,
                line.offhour, line.offminute, line.offsecond,
                line.overhour
            )
            if line.day in WorkTime.WT_WEEKENDS:
                overendtime += line.overhour
            else:
                overdaytime += line.overhour
        print "weekday: %.1f\nweekeyend: %.1f" %(overdaytime, overendtime)

    def _string2int(self, astring):
        if str(astring).startswith("0"):
            if 1 == len(astring):
                return 0
            else:
                return int(astring[1:])
        else:
            return int(astring)

    def _int2string(self, aint):
        assert(0 <= aint < 100)
        if aint < 10:
            return "0" + str(aint)
        else:
            return str(aint)

if __name__ == '__main__':
    wt = WorkTime()
    wt.initfile()
    wt.caclovertime()
    wt.output()
