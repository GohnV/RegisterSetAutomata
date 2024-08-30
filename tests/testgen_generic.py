import json
import rstr
import random
import sys

MATCHING = 10
NON_MATCHING = 20
SAMPLE_SIZE = 5000

lines = []
with open("../data/linguafranca.json", "r") as file:
    for line in file:
        lines.append(line)

sampled_lines = random.sample(lines, min(SAMPLE_SIZE, len(lines)))

num = 0
for line in sampled_lines:
    num += 1
    if num % 20 == 0:
        print(f"processing line {num} of {SAMPLE_SIZE}", file=sys.stderr)
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