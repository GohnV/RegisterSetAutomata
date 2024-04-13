import os
import re
import sys
from measuring import *

#SAMPLES = 5
#MAX_PUMP = 20
#TIMEOUT_SECS = 10
PUMP_VALUES = [5, 10, 20, 40, 80, 160]

def measure_times(folder_path):
    results = []
    succ_cnt = 0
    total_cnt = 0
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'r', errors='ignore') as file:
            file_content = file.read()
            if "VULNERABLE: YES" in file_content:
                total_cnt += 1
                pattern = re.search(r"INPUT: (.+)", file_content)
                prefix = re.search(r"PREFIX: (.+)", file_content)
                pump = re.search(r"PREFIX: .*?\nPUMPABLE: (.+)", file_content)
                suffix = re.search(r"SUFFIX: (.+)", file_content)
                
                pattern = "" if pattern is None else pattern.group(1)
                prefix = "" if prefix is None else prefix.group(1)
                pump = "" if pump is None else pump.group(1)
                suffix = "" if suffix is None else suffix.group(1)
                

                for pump_num in PUMP_VALUES:
                    attack_string = prefix + pump * pump_num + suffix


                    rsa_compile_time, rsa_match_time, rsa_match = measure_rsa(pattern, attack_string)

                    total_enemy_time, enemy_match = measure_enemy(pattern, attack_string)

                    if rsa_compile_time == PARSE_ERROR or rsa_compile_time == RSA_ERROR or rsa_compile_time == TIMEOUT:
                        total_rsa_time = rsa_compile_time
                    else:
                        total_rsa_time = rsa_match_time + rsa_compile_time

                    if isinstance(total_rsa_time, float) and isinstance(total_enemy_time, float) and rsa_match != enemy_match:
                        print(f"RESULTS NOT MATCHED FOR REGEX {pattern}", file=sys.stderr)
                        print(f"     rsa:{rsa_match}, enemy:{enemy_match}", file=sys.stderr)
                    else:
                        results.append({
                                    'pattern': pattern,
                                    'pumps': pump_num,
                                    'attack_string': attack_string,
                                    'rsa_match_time': rsa_match_time,
                                    'total_rsa_time': total_rsa_time,
                                    'total_enemy_time': total_enemy_time,
                                })
    return results

def format_time(time_value):
    if isinstance(time_value, float):
        return "{:.6f}".format(time_value)
    else:
        return time_value


def print_results_csv(results):
    headers = ["Pattern", "Attack String Pumps", "Total RsA Time", "RsA Match time", f"{get_enemy()} Time"]
    rows = []
    for result in results:
        pattern = '"' + result['pattern'].replace('"', '""') + '"'  # Quote and escape double quotes
        pumps = result['pumps']
        total_rsa_time = format_time(result['total_rsa_time'])
        rsa_match_time = format_time(result['rsa_match_time'])
        total_enemy_time = format_time(result['total_enemy_time'])
        rows.append([pattern, pumps, total_rsa_time, rsa_match_time, total_enemy_time])

    # Print headers
    print(','.join(headers))
    # Print rows
    for row in rows:
        print(','.join(map(str, row)))

if len(sys.argv) != 2:
    print("Usage: python bench_rxxr2.py (python|grep|perl)", file=sys.stderr)
    sys.exit(1)
set_enemy(sys.argv[1])
if get_enemy() not in ENEMIES:
    print("Invalid argument, Usage: python bench_rxxr2.py (python|grep|perl)", file=sys.stderr)

results = measure_times("../data/rxxr2")
print_results_csv(results)