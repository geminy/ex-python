from random import randint


def randGen(aList):
    while len(aList) > 0:
        yield aList.pop(randint(0, len(aList) - 1))


for item in randGen(['rock', 'paper', 'scissors']):
    print item


def counter(start_at=0):
    count = start_at
    while True:
        val = (yield count)
        if val is not None:
            count = val
        else:
            count += 1


count = counter(5)
print count.next()
print count.next()
print count.send(9)
print count.next()
print count.close()
# print count.next()