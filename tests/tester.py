import os
import subprocess
import time
import datetime
import copy
import json
from threading import Thread, Semaphore, Lock
from math import ceil, floor
from instance_analysis import test_error, get_relevant_info_data
from random import randint, shuffle
from typing import Union, Dict, List, Tuple

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_pack(kwargs: Dict[str, Union[str, int, bool]]) -> str:
    common_kwargs = {}
    common_kwargs['suite'] = kwargs['suite']
    common_kwargs['cost_system'] = kwargs['cost_system']
    common_kwargs['memory_limit'] = kwargs['memory_limit']
    common_kwargs['time_limit'] = kwargs['time_limit']
    common_kwargs['algorithm'] = kwargs['algorithm']
    common_kwargs['open_limitness'] = kwargs['open_limitness']
    common_kwargs['heuristic'] = kwargs['heuristic']
    # return f'{hash(tuple(common_kwargs.items()))}'
    import operator
    return ','.join(list(map(operator.itemgetter(1), sorted(common_kwargs.items()))))

def get_command_line_args(kwargs: Dict[str, Union[str, int, bool]]) -> List[str]:
    hash_for_trash = f'{hash(tuple(kwargs.items()))}'

    command_line_args = []
    command_line_args.append('python3')
    command_line_args.append('./fast-downward.py')
    command_line_args.append('--validate')
    command_line_args.append('--overall-memory-limit')
    command_line_args.append(kwargs['memory_limit'])
    # command_line_args.append('--overall-time-limit')
    command_line_args.append('--translate-time-limit')
    command_line_args.append(kwargs['time_limit'])
    command_line_args.append('--sas-file')
    command_line_args.append(f'./tests/trash/{hash_for_trash}.sas')
    command_line_args.append(f'./instances/{kwargs["suite"]}/{kwargs["domain"]}/{kwargs["domain_pddl"]}.pddl')
    command_line_args.append(f'./instances/{kwargs["suite"]}/{kwargs["domain"]}/{kwargs["instance_pddl"]}.pddl')
    command_line_args.append('--search')
    command_line_args.append(f'{kwargs["algorithm_call"]}({kwargs["heuristic_call"]})')
    command_line_args.append('--time-limit')
    command_line_args.append(str(floor(1.2 * kwargs['time_limit_seconds'])))
    if 'open_limit' in kwargs.keys():
        command_line_args.append(f'--open-limit')
        command_line_args.append(kwargs['open_limit'])
    if 'is_using_partial_expansion' in kwargs.keys():
        command_line_args.append(f'--partial-expansion')
    if 'second_phase_lower_bound' in kwargs.keys():
        command_line_args.append(f'--second-phase-lower-bound')
        command_line_args.append(kwargs['second_phase_lower_bound'])

    return command_line_args

def get_command_line(kwargs: Dict[str, Union[str, int, bool]]) -> str:
    return subprocess.list2cmdline(get_command_line_args(kwargs))

def run_test(kwargs: Dict[str, Union[str, int, bool]]) -> Tuple[str, str, float]:
    process = subprocess.Popen(get_command_line_args(kwargs), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f'{bcolors.OKGREEN}Starting...{bcolors.ENDC} {get_command_line(kwargs)}')

    start_time = time.time()

    stdout, stderr  = process.communicate()
    if 'KeyboardInterrupt' in stderr.decode():
        lock.acquire()
        print(f'STDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}')
        lock.release()
        raise KeyboardInterrupt

    finish_time = time.time()

    print(f'{bcolors.OKBLUE}Finishing...{bcolors.ENDC} {get_command_line(kwargs)} {get_relevant_info_data(stdout.decode(), "solution_cost") or (test_error(stdout.decode()) or f"{bcolors.FAIL}?{bcolors.ENDC}")} {get_relevant_info_data(stdout.decode(), "total_expansions") or (test_error(stdout.decode()) or f"{bcolors.FAIL}?{bcolors.ENDC}")}')

    return stdout.decode(), stderr.decode(), (finish_time - start_time)

def print_remaining_time() -> None:
    global lock, start_time, done, prunned, threads

    lock.acquire()

    try:
        elapsed_time = datetime.datetime.now() - start_time
        expected_end = datetime.datetime.now() + elapsed_time / len(done) * (len(threads) - len(done) - len(prunned))
    except ZeroDivisionError:
        expected_end = None

    print(f'{bcolors.BOLD}( {len(done)} / {len(threads) - len(prunned)} ){bcolors.ENDC} | Expected end: {bcolors.BOLD}{expected_end}{bcolors.ENDC}')

    lock.release()

def run_thread(kwargs: Dict[str, Union[str, int, bool]]) -> None:
    global lock, semaphore, done, prunned

    pack = get_pack(kwargs)

    filepath_json = f'./tests/results/{pack}/{kwargs["domain"]}_{kwargs["instance_pddl"]}.json'
    filepath_out = f'./tests/results/{pack}/{kwargs["domain"]}_{kwargs["instance_pddl"]}.out'
    filepath_err = f'./tests/results/{pack}/{kwargs["domain"]}_{kwargs["instance_pddl"]}.err'

    if prune and os.path.exists(filepath_out):
        is_disabled_pruning_for_this_experiment = False
        if not is_disabled_pruning_for_this_experiment:
            print(f'{bcolors.OKCYAN}Prunning...{bcolors.ENDC} {get_command_line(kwargs)}')
            lock.acquire()
            prunned.append('thread')
            lock.release()
            print_remaining_time()
            return

    semaphore.acquire()

    stdout, stderr, elapsed_time = run_test(kwargs)

    open(filepath_json, 'w').write(json.dumps(kwargs, indent=4, sort_keys=True))
    open(filepath_out, 'w').write(stdout)
    open(filepath_err, 'w').write(stderr)

    lock.acquire()
    done.append('thread')
    lock.release()
    print_remaining_time()

    semaphore.release()

def run_threads() -> None:
    global start_time, threads

    import sys
    exindex = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    excount = int(sys.argv[2]) if len(sys.argv) > 1 else 1
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

    threads = [thread for i, thread in enumerate(threads) if i % excount == exindex][:limit]
    shuffle(threads)

    print(f'Number of tests: {bcolors.BOLD}{len(threads)}{bcolors.ENDC}')

    start_time = datetime.datetime.now()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    while len(done) != 0:
        done.pop()
    while len(prunned) != 0:
        prunned.pop()
    while len(threads) != 0:
        threads.pop()

def add_threads(common_kwargs: Dict[str, Union[str, int, bool]]) -> None:
    pack = get_pack(common_kwargs)
    if not os.path.exists(f'./tests/results/{pack}'):
        os.mkdir(f'./tests/results/{pack}')
        open(f'./tests/results/{pack}/_config.json', 'w').write(json.dumps(common_kwargs, indent=4, sort_keys=True))

    for domain in os.listdir(f'./instances/{common_kwargs["suite"]}'):
        domain_pddls = list(sorted([x[:-5] for x in os.listdir(f'./instances/{common_kwargs["suite"]}/{domain}') if 'domain' in x and x.endswith('.pddl')]))
        instances_pddls = list(sorted([x[:-5] for x in os.listdir(f'./instances/{common_kwargs["suite"]}/{domain}') if not 'domain' in x and x.endswith('.pddl')]))

        for instance_index, instance_pddl in enumerate(instances_pddls):
            try:
                kwargs = copy.deepcopy(common_kwargs)

                kwargs['domain'] = domain
                kwargs['instance_index'] = instance_index
                kwargs['instance_pddl'] = instance_pddl
                if len(domain_pddls) == 1:
                    kwargs['domain_pddl'] = domain_pddls[0]
                else:
                    kwargs['domain_pddl'] = domain_pddls[instance_index]

                if kwargs['time_limit'][-1] == 's':
                    kwargs['time_limit_seconds'] = int(kwargs['time_limit'][:-1])
                if kwargs['time_limit'][-1] == 'm':
                    kwargs['time_limit_seconds'] = 60 * int(kwargs['time_limit'][:-1])
                if kwargs['time_limit'][-1] == 'h':
                    kwargs['time_limit_seconds'] = 60 * 60 * int(kwargs['time_limit'][:-1])

                if kwargs['memory_limit'][-1] == 'K':
                    kwargs['memory_limit_bytes'] = 1000 * int(kwargs['memory_limit'][:-1])
                if kwargs['memory_limit'][-1] == 'M':
                    kwargs['memory_limit_bytes'] = 1000 * 1000 * int(kwargs['memory_limit'][:-1])
                if kwargs['memory_limit'][-1] == 'G':
                    kwargs['memory_limit_bytes'] = 1000 * 1000 * 1000 * int(kwargs['memory_limit'][:-1])

                if kwargs['heuristic'] == 'operatorcounting':
                    kwargs['heuristic_call'] = kwargs['heuristic'] + '([lmcut_constraints(), pho_constraints(patterns=systematic(2)), state_equation_constraints()])'
                else:
                    kwargs['heuristic_call'] = kwargs['heuristic'] + '()'

                if 'pe' in kwargs['algorithm']:
                    kwargs['is_using_partial_expansion'] = True

                kwargs['algorithm_call'] = 'pea_ida'

                if kwargs['open_limitness'] == 'unlimited' and kwargs['heuristic'] == 'blind':
                    for other_pack in os.listdir(f'./tests/results'):
                        other_common_kwargs: Dict[str, Union[str, int, bool]] = json.loads(open(f'./tests/results/{other_pack}/_config.json').read())
                        if any(item != other_item and item[0] != 'heuristic' for item, other_item in zip(sorted(common_kwargs.items()), sorted(other_common_kwargs.items()))):
                            continue
                        other_stdout = open(f'./tests/results/{other_pack}/{domain}_{instance_pddl}.out').read()
                        if 'Solution found' in other_stdout:
                            break
                    else:
                        raise AssertionError

                if kwargs['open_limitness'] != 'unlimited':
                    astar_common_kwargs = copy.deepcopy(common_kwargs)
                    astar_common_kwargs['time_limit'] = '10m'
                    astar_common_kwargs['algorithm'] = 'edd-eh'
                    astar_common_kwargs['open_limitness'] = 'unlimited'
                    astar_pack = get_pack(astar_common_kwargs)
                    astar_stdout = open(f'./tests/results/{astar_pack}/{domain}_{instance_pddl}.out').read()
                    if not 'Solution found' in astar_stdout:
                        raise AssertionError

                    blind_astar_common_kwargs = copy.deepcopy(common_kwargs)
                    blind_astar_common_kwargs['time_limit'] = '10m'
                    blind_astar_common_kwargs['algorithm'] = 'edd-eh'
                    blind_astar_common_kwargs['open_limitness'] = 'unlimited'
                    blind_astar_common_kwargs['heuristic'] = 'blind'
                    blind_astar_pack = get_pack(blind_astar_common_kwargs)
                    blind_astar_stdout = open(f'./tests/results/{blind_astar_pack}/{domain}_{instance_pddl}.out').read()
                    if 'Solution found' in blind_astar_stdout:
                        raise AssertionError

                    limited_factor = float(kwargs['open_limitness'].split('limited')[1].split('-')[1])
                    value = next(line for line in astar_stdout.split('\n') if 'Open peak size:' in line).split('Open peak size:')[1].split(' ')[1]
                    kwargs['open_limit'] = str(ceil(int(value) * limited_factor / 100))

                    if 'pebound' in kwargs['open_limitness']:
                        for other_algorithm in ['pe-edd-eh', 'edd-eh']:
                            for other_open_limitness in ['limited-10', 'limited-50', 'limited-10']:
                                hybrid_common_kwargs = copy.deepcopy(common_kwargs)
                                hybrid_common_kwargs['algorithm'] = other_algorithm
                                hybrid_common_kwargs['open_limitness'] = other_open_limitness
                                hybrid_pack = get_pack(hybrid_common_kwargs)
                                if not os.path.exists(f'./tests/results/{hybrid_pack}/{domain}_{instance_pddl}.out') or not 'Solution found' in open(f'./tests/results/{hybrid_pack}/{domain}_{instance_pddl}.out').read():
                                    raise AssertionError
                        reference_common_kwargs = copy.deepcopy(common_kwargs)
                        reference_common_kwargs['algorithm'] = 'pe-edd-eh'
                        reference_common_kwargs['open_limitness'] = f'limited-{kwargs["open_limitness"].split("-")[3]}'
                        reference_pack = get_pack(reference_common_kwargs)
                        reference_data = open(f'./tests/results/{reference_pack}/{domain}_{instance_pddl}.out').read()
                        if 'Mininum F-value at phase transition:' in reference_data:
                            kwargs['second_phase_lower_bound'] = next(line for line in reference_data.split('\n') if 'Mininum F-value at phase transition:' in line).split('Mininum F-value at phase transition:')[1].split(' ')[1]
                        else:
                            kwargs['second_phase_lower_bound'] = next(line for line in reference_data.split('\n') if 'Plan cost:' in line).split('Plan cost:')[1].split(' ')[1]

                threads.append(Thread(target=run_thread, args=(kwargs,)))
            except AssertionError:
                continue
            except Exception as e:
                print(e)

if not os.path.exists(f'./tests/trash'):
    os.mkdir(f'./tests/trash')
else:
    for trash in os.listdir(f'./tests/trash'):
        os.remove(f'./tests/trash/{trash}')

if not os.path.exists(f'./tests/results'):
    os.mkdir(f'./tests/results')

# heuristics = ['lmcut', 'hmax', 'operatorcounting']
heuristics = ['lmcut']

number_of_threads = 12
prune = True
semaphore = Semaphore(number_of_threads)
lock = Lock()

done = []
prunned = []
threads = []

def run_astar_tests() -> None:
    common_kwargs = {}
    common_kwargs['suite'] = 'FD-IPC-opt-strips'
    common_kwargs['cost_system'] = 'real-costs'
    common_kwargs['memory_limit'] = '2G'
    common_kwargs['time_limit'] = '10m'
    common_kwargs['algorithm'] = 'edd-eh'
    common_kwargs['open_limitness'] = 'unlimited'
    for heuristic in heuristics:
        common_kwargs['heuristic'] = heuristic
        add_threads(common_kwargs)
    run_threads()

def run_blind_astar_tests() -> None:
    common_kwargs = {}
    common_kwargs['suite'] = 'FD-IPC-opt-strips'
    common_kwargs['cost_system'] = 'real-costs'
    common_kwargs['memory_limit'] = '2G'
    common_kwargs['time_limit'] = '10m'
    common_kwargs['algorithm'] = 'edd-eh'
    common_kwargs['open_limitness'] = 'unlimited'
    common_kwargs['heuristic'] = 'blind'
    add_threads(common_kwargs)
    run_threads()

def run_hybrid_tests() -> None:
    common_kwargs = {}
    common_kwargs['suite'] = 'FD-IPC-opt-strips'
    common_kwargs['cost_system'] = 'real-costs'
    common_kwargs['memory_limit'] = '2G'
    common_kwargs['time_limit'] = '360m'
    for algorithm in ['pe-edd-eh', 'edd-eh']:
        common_kwargs['algorithm'] = algorithm
        for open_limitness in ['limited-90', 'limited-50', 'limited-10']:
            common_kwargs['open_limitness'] = open_limitness
            for heuristic in heuristics:
                common_kwargs['heuristic'] = heuristic
                add_threads(common_kwargs)
    run_threads()

def run_artificial_hybrid_tests() -> None:
    common_kwargs = {}
    common_kwargs['suite'] = 'FD-IPC-opt-strips'
    common_kwargs['cost_system'] = 'real-costs'
    common_kwargs['memory_limit'] = '2G'
    common_kwargs['time_limit'] = '360m'
    common_kwargs['algorithm'] = 'edd-eh'
    for open_limitness in ['limited-90-pebound-90', 'limited-50-pebound-50', 'limited-10-pebound-10']:
        common_kwargs['open_limitness'] = open_limitness
        for heuristic in heuristics:
            common_kwargs['heuristic'] = heuristic
            add_threads(common_kwargs)
    run_threads()

def run_processor() -> None:
    subprocess.Popen(['python3', './tests/processor.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

run_astar_tests()
run_processor()
run_blind_astar_tests()
run_processor()
run_hybrid_tests()
run_processor()
run_artificial_hybrid_tests()
run_processor()

# while True:
#     print('\a')
#     sleep(1.8)
