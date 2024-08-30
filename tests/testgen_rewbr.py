import json
import rstr
import random
import sys

from test_generator import generate_tests

lines = []
with open("../data/lf_rewbr.json", "r") as file:
    for line in file:
        lines.append(line)

generate_tests(lines)
