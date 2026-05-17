#!/bin/python3
import sys
import re

if len(sys.argv) > 1:
    prgname = sys.argv[1]
else:
    prgname = "prg.rsa"

if len(sys.argv) > 2:
    memname = sys.argv[2]
else:
    memname = "mem.rsa"

prgfile = open(prgname)
memfile = open(memname)
outprgname = re.sub("rsa","out", prgname)
outmemname = re.sub("rsa","out", memname)
outprgfile = open(outprgname, "w")
outmemfile = open(outmemname, "w")

labelmap = {}
cnt = 0
code = []

# first pass
for line in prgfile:
    line = re.sub(r'#.*$', '', line)
    line = line.strip()
    if line == "":
        continue

    if line.endswith(":"):
        labelstr = line[:-1]
        if labelstr in labelmap.keys():
            # error
            print(f"label '{labelstr}' redefined", file=sys.stderr)
            exit(1)
        labelmap[labelstr] = str(cnt)
    else:
        cnt += 1
        code.append(line)

# second pass
for line in code:
    words = line.split()
    outstr = ""
    for word in words:
        if word in labelmap.keys():
            outstr += labelmap[word] + " "
        else:
            outstr += word + " "
    print(outstr, file=outprgfile)

for line in memfile:
    print(
        re.sub(
            r'("label":\s*)"([^"]+)"',
            lambda m: f'{m.group(1)}{labelmap[m.group(2)]}',
            line
        ), file=outmemfile, end=''
    )
