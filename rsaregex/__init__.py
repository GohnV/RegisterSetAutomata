from rsaregex.new_parser import create_nra, create_rsa
from rsaregex.RsAtools import NRA, RsA, DRsA
from rsaregex.rsa_draw import draw_automaton
from typing import Union

def match(pattern: str, input: str) -> Union[bool, int]:
    drsa = create_rsa(pattern)
    if not drsa:
        return -1
    return drsa.run_word(input)

__all__ = ["create_nra", "create_rsa", "NRA", "RsA", "DRsA", "draw_automaton"]