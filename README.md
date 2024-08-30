# rsa-matcher
* Jan Vašák, xvasak01@vutbr.cz, 2024

This is a prototype of a regex matcher based on register set automata [[1]](#1).

## Usage
To run use:
`python rsa-matcher [-h] [-d] [-f FILE] pattern`
* `pattern` regex to be matched to input data
* `-h` print help and exit
* `-d` don't determinise ahead of time (determinise the regex on for each input line)
* `-f FILE` specify file to read from

The program then reads lines from `stdin` (or `FILE` if specified) and prints out every line that matches the `pattern`.

As `rsaregex` has methods for drawing
the automata using graphviz, it requires installation of graphviz (`sudo apt-get install graphviz` on Linux) and its Python library (`pip install graphviz`).

## rsaregex package
Package implementing RsA-based regex matching and also a representation of register (set) automata
as the classes `RsA`, `DRsA`, and `NRA`.
Also provides the function `draw_automaton` to draw a specified automaton into a pdf file using `graphviz`. 

For regex matching use either
* `drsa = rsaregex.create_rsa(pattern)` to create the DRsA and then use `result = drsa.run_word(input)`
to match the input to the pattern, or
* `result = rsaregex.match(pattern, input)` to do the above in one operation (not recommended for repeated matching). Beware that `result` might be `-1` if the pattern cannot be determinised.

    
## References
<a id="1">[1]</a>
Gulčíková, S. and Lengál, O. Register Set Automata (Technical Report). arXiv.
2022. DOI: 10.48550/ARXIV.2205.12114. Available at:
https://arxiv.org/abs/2205.12114
