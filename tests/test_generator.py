import json
import sys
import rstr

MATCHING = 10
NON_MATCHING = 20

def generate_tests(lines):
    num = 0
    for line in lines:
        num += 1
        if num % 20 == 0:
            print(f"processing line {num} of {len(lines)}", file=sys.stderr)
            sys.stderr.flush()
        try: data = json.loads(line)
        except: continue
        pattern = data["pattern"]
        if not isinstance(pattern, str): continue
        inputs = []
        for _ in range(MATCHING):
            try:
                inputs.append(rstr.xeger(pattern))
            except: continue
        for _ in range(NON_MATCHING):
            inputs.append(rstr.normal(0,128))
        print(json.dumps({"pattern":pattern, "inputs":inputs}))