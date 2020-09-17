import sys

BASE = 11
EXPONENT = 10

if len(sys.argv) == 2:
	EXPONENT = int(sys.argv[1])

print "base=%d exponent=%d" %(BASE, EXPONENT)

for e in range(0, EXPONENT + 1):
	num = BASE ** e
	strnum = str(num)
	count = strnum.count("1")
	print "%d^%d=%d %d" %(BASE, e, num, count)
	
