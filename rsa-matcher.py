import rsaregex
import re
import argparse
import sys

parser = argparse.ArgumentParser(
                    prog='rsa-matcher',
                    description='A regex matcher based on register set automata',
                    epilog='')
parser.add_argument('pattern',
                    help='pattern to be matched to input data')
# parser.add_argument('-z', '--nulldata',
#                     action='store_true',
#                     help='Input data are terminated by zero bytes instead of newlines')
parser.add_argument('-d', '--nodeter',
                    action='store_true',
                    help='Don\'t determinise ahead of time')
parser.add_argument("-f", "--file",
                    help="increase output verbosity")

def cant_determinise():
    print(f'Unable to determinise regex "{args.pattern}", aborting.', file=sys.stderr)
    exit()

args = parser.parse_args()

if not args.nodeter:
    drsa = rsaregex.create_rsa(args.pattern)
    if drsa == False:
        cant_determinise()

FILE = sys.stdin
if args.file:
    FILE = open(args.file, "r")

for line in FILE:
    line = line.rstrip("\n")
    if args.nodeter:
        result = rsaregex.match(args.pattern, line)
        if result == -1:
            cant_determinise()
    else:
        result = drsa.run_word(line)
    if result:
        print(line)
FILE.close()