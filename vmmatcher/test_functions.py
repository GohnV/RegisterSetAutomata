import sys
import os
import subprocess
import json

sys.path.append(os.path.abspath(".."))

import rsaregex

pattern = "a"
input = "a"

def run_old(pattern, input):
    nra = rsaregex.create_nra(pattern)

    
    rsaregex.draw_automaton(nra, "nra")
    



    
    prg, mem, nregs = nra.generate_vm_code()
    
    rsa = rsaregex.create_rsa(pattern)
    
    # nra.remove_eps()
    # nra.remove_unreachable()
    # nra.complete_updates()
    # nra.make_register_local()
    # nra.fill_with_bottom()
    rsaregex.draw_automaton(nra, "nra2")
    rsaregex.draw_automaton(rsa, "rsa")
    # return
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

def run(pattern, input):
    nregs = rsaregex.regex_vm_code(pattern, "prg.out", "mem.out")
    result = subprocess.run(
        ["./vmmatcher", "prg.out", "mem.out", str(nregs)],
        input=input,
        text=True,
        capture_output=True
    )
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


# print(run(r"ab?c", 'ac'))
# print(run(r"^([aá🍔]|[cč]b)$", "🍔"))
# print(run(r"", 'aaa'))
# print(run_old(r"(.).*\1.*\1", 'aa')) #TODO: EXAMPLE!
print(run_old(r"(.).*\1", 'aa'))
# print(run(r"ab{3,5}c", 'abbbbc'))
# print(run(r"^[^;]*([^;])[^;]*;.*(.).*\1\2.*$", 'aa')) #TODO: check whether overapprox is correct here?
# print(run(r"^[^;]*([^;])[^;]*;[^;]*([^;])[^;]*\2\1[^;]*$", 'aa')) #FIXME: and here! (this is a SIMPLIFIED version of the intro regex)
# print(run(r"^[^;]*([^;])[^;]*;[^;]*([^;])[^;]*;[^;]*\2[^;]*;[^;]*\1[^;]*$", 'aa')) # this one works??
