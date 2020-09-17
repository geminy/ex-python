#!/usr/bin/env python

import os
import glob
import Image
import math

def convert_pixel(p):
    index = 32
    while (1 << index) & p == 0:
        index -= 1
    if (1 << index) == p:
        return p
    else:
        return 1 << (index + 1)

def parse_png(path):
    print "%s ..." % (path)
    root, ext = os.path.splitext(path)
    png = Image.open(path)
    width, height = png.size
    width2 = convert_pixel(width)
    height2 = convert_pixel(height)
    if width != width2 or height != height2:
        png2 = png.resize((width2, height2), Image.ANTIALIAS)
        png2.save(root + "_" + ext)
        print "%s (%d, %d) > (%d, %d)" % (path, width, height, width2, height2)

def main():
    print "*" * 10, "begin", "*" * 10
    pngList = glob.glob(os.getcwd() + "/*.png")
    for png in pngList:
        parse_png(png)
    print "*" * 10, "end", "*" * 10

if __name__ == '__main__':
    main()
