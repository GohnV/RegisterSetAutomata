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
            attack_string =  prefix+pump*pump_n+suffix
            grep_time, grep_match = measure_grep(pattern, attack_string)
            
            
            # TODO: make this a function
            rsa_compile_time, rsa_match_time, rsa_match = measure_rsa(pattern, attack_string)
            if rsa_compile_time == PARSE_ERROR or rsa_compile_time == RSA_ERROR or rsa_compile_time == TIMEOUT:
                total_rsa_time = rsa_compile_time
            else:
                total_rsa_time = rsa_match_time + rsa_compile_time
            # TODO

            if isinstance(total_rsa_time, float) and isinstance(grep_time, float) and rsa_match != grep_match:
                print(f"RESULTS NOT MATCHED FOR REGEX {pattern}", file=sys.stderr)
                print(f"     rsa:{rsa_match}, enemy:{grep_match}", file=sys.stderr)
                att_str["result_match"] = False
            else:
                att_str["result_match"] = True

            att_str["grep_time"] = format_time(grep_time)
            att_str["rsa_time"] = format_time(total_rsa_time)
            att_str["rsa_compile_time"] = format_time(rsa_compile_time)
        print(json.dumps(data))