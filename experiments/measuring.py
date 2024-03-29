import signal
import time
import sys
import subprocess
import shlex
import pcre2
sys.path.append('../')
import new_parser as rsa

PARSE_ERROR = "Error"
RSA_ERROR = "No DRsA"
TIMEOUT = "Timeout"
MATCH_LIMIT = "Match limit"
SAMPLES = 3
TIMEOUT_SECS = 10
g_enemy = ""

# Timeout class from StackOverflow, by Thomas Ahle, https://stackoverflow.com/a/22348885
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

def measure_grep(pattern, attack_string):
    print(f"Measuring grep with pattern {pattern} and string {attack_string}", file=sys.stderr)
    avg_time = 0
    match = False
    for _ in range(SAMPLES):
        try:
            
            command = ["timeout", "100s", "grep", "-Ez", pattern]

            GREP_REPETITIONS = 100
            input_string = (attack_string + "\0") * GREP_REPETITIONS

            t0 = time.perf_counter()
            result = subprocess.run(command, input=input_string, capture_output=True, text=True, shell=False)
            t1 = time.perf_counter()

            if result.returncode == 124:
                return TIMEOUT, False
            avg_time += (t1-t0)/(SAMPLES*GREP_REPETITIONS)
            if result.returncode == 0:
                match = True
            if result.returncode == 1:
                match == False

        #     with timeout(seconds=TIMEOUT_SECS):
        #         with subprocess.Popen(["grep", "-E", pattern], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as grep_process:
        #             t0 = time.perf_counter()
        #             stdout, stderr = grep_process.communicate(input=attack_string.encode())
        #             t1 = time.perf_counter() 
        #             if grep_process.returncode == 2:
        #                 return PARSE_ERROR
                
        #         avg_time += (t1-t0)/SAMPLES
        # except TimeoutError:
        #     return TIMEOUT
        except Exception as e:
            print(f"Exception: {e}", file=sys.stderr)
            return "int error"
    return avg_time, match


def measure_python(pattern, attack_string):
    pass

def measure_pcre2(pattern, attack_string):
    print(f"Measuring pcre2 with pattern {pattern} and string {attack_string}", file=sys.stderr)
    avg_time = 0
    match = False
    for _ in range(SAMPLES):
        try:
            with timeout(seconds=TIMEOUT_SECS):
                t0 = time.perf_counter()
                compiled_pattern = pcre2.compile(pattern)
                match = compiled_pattern.match(attack_string)
                t1 = time.perf_counter()
                avg_time += (t1-t0)/SAMPLES
        except TimeoutError:
            return TIMEOUT, False
        except Exception as e:
            t1 = time.perf_counter()
            if str(e) == "No match":
                avg_time += (t1-t0)/SAMPLES
                match = False
            elif str(e) == "Match limit exceeded":
                return MATCH_LIMIT, False
            else:
                return PARSE_ERROR, False
    return avg_time, (match is not None)

def measure_rsa(pattern, attack_string):
    print(f"Measuring RsA for pattern {pattern}", file=sys.stderr)
    for _ in range(SAMPLES):                
        avg_compile_time = 0 
        avg_match_time = 0

        try:
            with timeout(seconds=TIMEOUT_SECS):
                t0 = time.perf_counter()
                rsa_result = rsa.create_rsa(pattern)
                t1 = time.perf_counter()
                avg_compile_time += (t1-t0)/SAMPLES
        except TimeoutError:
            return TIMEOUT, TIMEOUT, False        
        except Exception as e:
            print("Exception:",str(e), file=sys.stderr)
            return PARSE_ERROR, PARSE_ERROR, False
        if not rsa_result:
            return RSA_ERROR, RSA_ERROR, False
        t0 = time.perf_counter()
        match_rsa = rsa_result.runWord(attack_string)
        t1 = time.perf_counter()
        avg_match_time += (t1-t0)/SAMPLES
    return avg_compile_time, avg_match_time, match_rsa

def set_enemy(enemy):
    global g_enemy
    g_enemy = enemy

def get_enemy():
    global g_enemy
    return g_enemy

ENEMIES = {'grep': measure_grep, 'python': measure_python, 'pcre2': measure_pcre2}

def measure_enemy(pattern, attack_string):
    global g_enemy
    return ENEMIES[g_enemy](pattern, attack_string)

def format_time(time_value):
    if isinstance(time_value, float):
        return "{:.6f}".format(time_value)
    else:
        return time_value


# from tabulate import tabulate
# def print_results_table(results):
#     headers = ["Pattern", "Total RsA Time", "RsA Match time", "Total Python Time", "Python Match Time"]
#     rows = []
#     for result in results:
#         pattern = result['pattern']
#         total_rsa_time = format_time(result['total_rsa_time'])
#         rsa_match_time = format_time(result['rsa_match_time'])
#         total_py_time = format_time(result['total_py_time'])
#         py_match_time = format_time(result['py_match_time'])
#         rows.append([pattern, total_rsa_time, rsa_match_time, total_py_time, py_match_time])
#     print(tabulate(rows, headers=headers, tablefmt="grid"))
