# rsa-matcher
* Jan Vašák, xvasak01@vutbr.cz, 2026

This is a regex matcher implemented based on register set automata (RSA) [[1]](#1).
There are actually two parts of the matcher, the Python package `rsaregex`, which can be used
as a standalone package to match regexes, and the C++-implemented VM `vmmatcher`, which can
be used to match regexes more efficiently. Code for `vmmatcher` can be generated
from the `rsaregex` package.

## Usage

### rsaregex package standalone
Package implementing RsA-based regex matching and also a representation of register (set) automata
as the classes `RsA`, `DRsA`, and `NRA`.
Provides the function `draw_automaton` to draw a specified automaton into a pdf file using `graphviz`. 

For regex matching use either
* `drsa = rsaregex.create_rsa(pattern)` to create the DRsA and then use `result = drsa.run_word(input)`
to match the input to the pattern, or
* `result = rsaregex.match(pattern, input)` to do the above in one operation (not recommended for repeated matching). Beware that `result` might be `-1` if the pattern cannot be determinised.

### vmmatcher
    
Using the VM matcher requires more steps,
to compile it, run `make opt` in the `vmmatcher` directory. This creates the binary `vmmatcher`.

To generate code, use the function `regex_vm_code(pattern, program_filename, memory_filename)` provided in `rsaregex`. It will return the number of registers needed for the RSA, which we need to pass to `vmmatcher`
and write the generated code to `program_filename` and the generated memory to `memory_filename`.
If an error is encountered a matching exception will be raised.

For matching, run `./vmmatcher PROGRAM MEMORY NREGS`, where PROGRAM is the program file,
MEMORY is the memory file, and NREGS is the number of registers.
The program reads input from stdin. After the input is over, it returns 0 if a match was
found and 1 otherwise. It also reports the time spent matching (i.e., not loading/parsing)
to stdout.

To run tests, run the python script `run_tests` in the `vmmatcher` directory. The file `test_functions`
contains functions for used testing `vmmatcher`.
You can use the function `run` as a starting point when using `vmmatcher`.

## References
<a id="1">[1]</a>
Havlena, V.; Holík, L.; Lengál, O.; Vašák, J. and Gulčíková, S. Towards
Efficient Matching of Regexes with Backreferences using Register Set Automata
(Technical Report). 2026. Available at: https://arxiv.org/abs/2205.12114. Accepted
to PLDI’26.
