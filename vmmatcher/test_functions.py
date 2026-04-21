import sys
import os
import subprocess
import json

sys.path.append(os.path.abspath(".."))

import rsaregex

pattern = "a"
input = "a"

def run(pattern, input):
    nra = rsaregex.create_nra(pattern)

    prg, mem, nregs = nra.generate_vm_code()

    with open("prg.rsa", "w") as f:
        for i in prg:
            print(i, file=f)


    with open("mem.rsa", "w") as f:
        json.dump(mem, f, indent=2)

    subprocess.run(
        ["python", "preproc_code.py"],
        text=True
    )


    result = subprocess.run(
        ["./vmmatcher", "prg.out", "mem.out", str(nregs)],
        input=input,
        text=True,
        capture_output=True
    )

    if 0:
        print("STDOUT:")
        print(result.stdout,file=sys.stderr)
        print("STDERR:")
        print(result.stderr,file=sys.stderr)
    
    return result.returncode

RED = '\033[91m'
GREEN = '\033[92m'
WHITE = '\033[0m'



def test(pattern, input, expected, name):
    print(f"TEST {name}")
    
    out = run(pattern, input)
    if out == 0:
        val = True
    elif out == 1:
        val = False
    else:
        print(f"\tgot: {out}")
        print("\t{RED}UNEXPECTED RETURN CODE{WHITE}")
        return
    
    
    if val == expected:
        print(f"\t{GREEN}PASSED{WHITE}")
    else:
        print(f"\tpattern: /{pattern}/")
        print(f"\tinput: '{input}'")
        print(f"\texpected: {expected}")
        print(f"\tgot: {val}")
        print(f"\t{RED}FAILED{WHITE}")



# run(r"(.)\1\1", 'aaa')
