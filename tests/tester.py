import sys
import json
import re
sys.path.append("..")
import rsaregex

tests_failed = 0
uncompiled_regex = 0
total_regex = 0

RED = '\033[91m'
GREEN = '\033[92m'
END = '\033[0m'

# Timeout class from StackOverflow, by Thomas Ahle, https://stackoverflow.com/a/22348885
import signal
class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

def replace_dollars_except_last(s):
    if s.endswith('$'):
        main_part = s[:-1]
        main_part = main_part.replace('$', '')
        result = main_part + '$'
    else:
        result = s.replace('$', '')
    return result

lines = []
# with open("generated.json", "r") as file:
#     for line in file:
#         lines.append(line)

with open("rewbr_generated.json", "r") as file:
    for line in file:
        lines.append(line)

num = 0
with open("failed.txt", "w") as failed, open("uncompiled.txt", "w") as uncompiled:
    for line in lines:
        num += 1
        #if num%20 == 0: 
        print(f"Testing regex {num}", file=sys.stderr)
        data = json.loads(line)
        pattern = data["pattern"]
        total_regex += 1
        print(repr(pattern), file=sys.stderr)
        #TODO: solve weird stuff happening with results
        try:
            with timeout(seconds=30):
                try:
                    rsa = rsaregex.create_rsa(pattern)
                    print(f"rsa={rsa}", file=sys.stderr)
                    backup_pattern = replace_dollars_except_last(pattern)
                    rsa_backup = rsaregex.create_rsa(backup_pattern)
                except:
                    print("exception1", file=sys.stderr)
                    print(repr(pattern), file=uncompiled)
                    uncompiled_regex += 1
                    continue
                if rsa == False:
                    print("rsa=False", file=sys.stderr)
                    print(repr(pattern), file=uncompiled)
                    uncompiled_regex += 1
                    continue
                for word in data["inputs"]:
                    expected = (re.search(pattern, word, re.MULTILINE) != None)
                    actual = rsa.run_word(word)
                    #print(expected, file=sys.stderr)
                    #print(actual, file=sys.stderr)
                    #TODO: separate condition into 2 for clarity

                    if expected != actual and (re.search(backup_pattern, word, re.MULTILINE) != None) != rsa_backup.run_word(word):
                        print(" FAILED", file=sys.stderr)
                        tests_failed += 1
                        print(f"{RED}FAILED{END}", file=failed)
                        print(f"    regex:{repr(pattern)}", file=failed)
                        print(f"    input:{repr(word)}", file=failed)
                        print(f"    expected:{expected}, got:{actual}", file=failed)
                        print(f"    re:{expected}", file=failed)
        except TimeoutError:
            print("TIMEOUT", file=sys.stderr)
            continue
if tests_failed == 0:
    print(f"{GREEN}ALL TESTS PASSING{END}")
else:
    print(f"{RED} FAILED {tests_failed} TESTS{END}")
    print("see 'failed.txt' for a report")
print("see uncompiled for a list of regexes which were not compiled by rsaregex")