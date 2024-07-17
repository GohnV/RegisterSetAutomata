import json

from measuring import *

rengar_data = "../data/rengar_attacks.json"

print("Pattern, Attack_string, grep_time, rsa_time")

def csv_quotes(string):
    return '"' + string.replace('"', '""') + '"'

with open(rengar_data, "r") as file:
    for line in file:
        data = json.loads(line)
        pattern = data["pattern"]
        for att_str in data["attack_strings"]:
            prefix = att_str["prefix"]
            pump = att_str["pump"]
            pump_n = att_str["pump_n"]
            suffix = att_str["suffix"]
            grep_time, grep_match = measure_grep(pattern, prefix+pump*pump_n+suffix)
            att_str_short = f"{prefix} + {pump} * {pump_n} + {suffix}"
            print(f"{csv_quotes(pattern)}, {csv_quotes(att_str_short)}, {format_time(grep_time)}")