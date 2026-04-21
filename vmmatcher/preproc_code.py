#!/bin/python3
import sys
import re

#TODO: labels in decode stuff must be replaced too

labelmap = {}
cnt = 0
code = []

prgfile = open("prg.rsa") 
memfile = open("mem.rsa")

outprgfile = open("prg.out", "w") 
outmemfile = open("mem.out", "w")

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
            print("label redefinition", sys.stderr)
            exit(1)
        labelmap[labelstr] = str(cnt)

    # tokens = line.split()
    # if tokens[0] == "LABEL":
    #     labelstr = tokens[1]
    #     if labelstr in labelmap.keys():
    #         # error
    #         print("label redefinition", sys.stderr)
    #         exit(1)
    #     labelmap[labelstr] = cnt
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
