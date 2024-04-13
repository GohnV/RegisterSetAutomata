import os
import re
import sys

from measuring import *



def measure_times(directory):
    results = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content_lines = file.readlines()
                pattern = content_lines[0].strip()
                attack_string_regex = re.compile(r'^Attack success, attack string is:\n((?:.|\n)*)\n', re.MULTILINE)
                attack_string_match = attack_string_regex.search(''.join(content_lines))

                if attack_string_match:
                    attack_string = attack_string_match.group(1)

                    rsa_compile_time, rsa_match_time, rsa_match = measure_rsa(pattern, attack_string)
                    if rsa_compile_time == PARSE_ERROR or rsa_compile_time == RSA_ERROR or rsa_compile_time == TIMEOUT:
                        total_rsa_time = rsa_compile_time
                    else:
                        total_rsa_time = rsa_match_time + rsa_compile_time

                    enemy_time, enemy_match = measure_enemy(pattern, attack_string)

                    if isinstance(total_rsa_time, float) and isinstance(enemy_time, float) and rsa_match != enemy_match:
                        print(f"RESULTS NOT MATCHED FOR REGEX {pattern}", file=sys.stderr)
                        print(f"     rsa:{rsa_match}, enemy:{enemy_match}", file=sys.stderr)
                    else:
                        results.append({
                            'filename': filename,
                            'pattern': pattern,
                            'attack_string': attack_string,
                            'rsa_match_time': rsa_match_time,
                            'total_rsa_time': total_rsa_time,
                            'total_enemy_time': enemy_time,
                        })
    return results

def print_results_csv(results):
    headers = ["Pattern", "Total RsA Time", "RsA Match time", f"{get_enemy()} Time"]
    rows = []
    for result in results:
        pattern = '"' + result['pattern'].replace('"', '""') + '"'  # Quote and escape double quotes
        total_rsa_time = format_time(result['total_rsa_time'])
        rsa_match_time = format_time(result['rsa_match_time'])
        total_enemy_time = format_time(result['total_enemy_time'])
        rows.append([pattern, total_rsa_time, rsa_match_time, total_enemy_time])

    print(','.join(headers))

    for row in rows:
        print(','.join(map(str, row)))

if len(sys.argv) != 2:
    print("Usage: python bench_rescue.py (python|grep|perl)", file=sys.stderr)
    sys.exit(1)
set_enemy(sys.argv[1])
if get_enemy() not in ENEMIES:
    print("Invalid argument, Usage: python bench_rescue.py (python|grep|perl)", file=sys.stderr)
results = measure_times('../data/rescue')
print_results_csv(results)