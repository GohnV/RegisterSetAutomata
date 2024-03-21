import signal
import time
import sys
import subprocess
sys.path.append('../')
import new_parser as rsa

PARSE_ERROR = "Error"
RSA_ERROR = "No DRsA"
TIMEOUT = "Timeout"
SAMPLES = 10
TIMEOUT_SECS = 100
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
    for _ in range(SAMPLES):
        try:
            with timeout(seconds=TIMEOUT_SECS):
                with subprocess.Popen(["grep", "-E", pattern], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as grep_process:
                    t0 = time.perf_counter()
                    stdout, stderr = grep_process.communicate(input=attack_string.encode())
                    t1 = time.perf_counter() 
                    if grep_process.returncode == 2:
                        return PARSE_ERROR
                
                avg_time += (t1-t0)/SAMPLES
        except TimeoutError:
            return TIMEOUT
        except Exception as e:  # Handling any other exceptions
            print(f"Exception: {e}", file=sys.stderr)
            return "int error"
    return avg_time


def measure_python(pattern, attack_string):
    pass

def measure_perl(pattern, attack_string):
    pass

def measure_rsa(pattern, attack_string):
    for _ in range(SAMPLES):
        print(f"Measuring RsA for pattern {pattern}", file=sys.stderr)
                
        avg_compile_time = 0 
        avg_match_time = 0

        try:
            t0 = time.perf_counter()
            rsa_result = rsa.create_rsa(pattern)
            t1 = time.perf_counter()
            avg_compile_time += (t1-t0)/SAMPLES
        except:
            return PARSE_ERROR, PARSE_ERROR
        if not rsa_result:
            return RSA_ERROR, RSA_ERROR
        t0 = time.perf_counter()
        match_rsa = rsa_result.runWord(attack_string)
        t1 = time.perf_counter()
        avg_match_time += (t1-t0)/SAMPLES
    return avg_compile_time, avg_match_time

def set_enemy(enemy):
    global g_enemy
    g_enemy = enemy

def get_enemy():
    global g_enemy
    return g_enemy

ENEMIES = {'grep': measure_grep, 'python': measure_python, 'perl': measure_perl}

def measure_enemy(pattern, attack_string):
    global g_enemy
    return ENEMIES[g_enemy](pattern, attack_string)

def format_time(time_value):
    if isinstance(time_value, float):
        return "{:.6f} s".format(time_value)
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
