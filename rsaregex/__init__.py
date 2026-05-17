from rsaregex.new_parser import create_nra, create_rsa, process_vm_code, print_vm_code_debug
from rsaregex.RsAtools import NRA, RsA, DRsA
from rsaregex.rsa_draw import draw_automaton
from typing import Union

def match(pattern: str, input: str) -> Union[bool, int]:
    drsa = create_rsa(pattern)
    if not drsa:
        return -1
    return drsa.run_word(input)

def regex_vm_code(pattern: str, prg_file, mem_file):
    nra = create_nra(pattern)
    prg, mem, nregs = nra.generate_vm_code()
    process_vm_code(prg, mem, prg_file, mem_file)
    return nregs

__all__ = ["create_nra", "create_rsa", "NRA", "RsA", "DRsA", "draw_automaton"]
