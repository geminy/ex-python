########################################################
#                    AUTO TEST                         #
########################################################
# 1.getevent output
# mt2712:/ # getevent
# add device 1: /dev/input/event4
#   name:     "m_alsps_input"
# add device 2: /dev/input/event3
#   name:     "hwmdata"
# add device 3: /dev/input/event1
#   name:     "mtk-kpd"
# could not get driver version for /dev/input/mouse0, Not a typewriter
# could not get driver version for /dev/input/mice, Not a typewriter
# add device 4: /dev/input/event0
#   name:     "kpd"
# add device 5: /dev/input/event2
#   name:     "mtk-tpd"
#
# 2.touchscreen event
# /dev/input/event2: 0003 0039 000001e5
# /dev/input/event2: 0003 0035 00000060
# /dev/input/event2: 0003 0036 0000015b
# /dev/input/event2: 0003 0030 0000002d
# /dev/input/event2: 0003 0032 0000002d
# /dev/input/event2: 0001 014a 00000001
# /dev/input/event2: 0003 0000 00000060
# /dev/input/event2: 0003 0001 0000015b
# /dev/input/event2: 0000 0000 00000000
# /dev/input/event2: 0003 0039 ffffffff
# /dev/input/event2: 0001 014a 00000000
# /dev/input/event2: 0000 0000 00000000
#
# 3.keyboard event
# /dev/input/event1: 0001 0072 00000001
# /dev/input/event1: 0000 0000 00000000
# /dev/input/event1: 0001 0072 00000000
# /dev/input/event1: 0000 0000 00000000
##################################################
#version 0.1.0
#!/usr/bin/env python

import re

AUTOTEST_RECORD_FILE = "autotest.record"
AUTOTEST_DATA_FILE = "autotest.data"

EVENT_RE_PATTERN = "^(/dev/input/event[12]{1}):\s(\w{4})\s(\w{4})\s(\w{8})$"
EVENT_RE_OBJECT = re.compile(EVENT_RE_PATTERN)

data = []

f = file(AUTOTEST_RECORD_FILE, "r")
for l in f:
	m = EVENT_RE_OBJECT.match(l)
	if m:
		event_device = m.group(1)
		event_type = int(m.group(2), 16)
		event_code = int(m.group(3), 16)
		event_value = int(m.group(4), 16)
		data.append("sendevent " + str(event_device) + " " + str(event_type) + " " + str(event_code) + " " + str(event_value))
f.close()

f = file(AUTOTEST_DATA_FILE, "w")
for l in data:
	f.write(l + "\n")
f.close()

print '"' + AUTOTEST_DATA_FILE + '"', "generated."