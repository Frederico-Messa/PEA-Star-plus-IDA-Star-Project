import os
import json

trigger_keywords = {
                'solution_cost': 'Plan cost:',
                'solution_length': 'Plan length:',
                'search_time': 'Search time:',
                'total_expansions': 'Expanded',
                'first_phase_expansions': 'Number of first phase expansions:',
                'second_phase_expansions': 'Number of second phase expansions:',
                'total_generations': 'Generated',
                'first_phase_generations': 'Number of first phase generations:',
                'second_phase_generations': 'Number of second phase generations:',
                'second_phase_iterations': 'Number of second phase iterations:',
                'open_peak_size': 'Open peak size:',
                'closed_peak_size': 'Closed peak size:',
                'min_f_at_phase_change' : 'Mininum F-value at phase transition:',
                'mean_f_at_phase_change' : 'Mean F-value at phase transition:',
                'max_f_at_phase_change' : 'Maximum F-value at phase transition:',
                'pct_min_f_at_phase_change': 'Percentage of minimum F-values at phase transition:',
                'min_depth_at_phase_change' : 'Mininum depth at phase transition:',
                'mean_depth_at_phase_change' : 'Mean depth at phase transition:',
                'max_depth_at_phase_change' : 'Maximum depth at phase transition:'
            }

if not os.path.exists(f'./tests/processed_results'):
    os.mkdir(f'./tests/processed_results')

for folder in os.listdir(f'./tests/results/'):
    if not os.path.exists(f'./tests/processed_results/{folder}'):
        os.mkdir(f'./tests/processed_results/{folder}')
    for instance in {'.'.join(file.split('.')[:-1]) for file in os.listdir(f'./tests/results/{folder}/') if file != '_config.json'}:
        data = open(f'./tests/results/{folder}/{instance}.out').read() + open(f'./tests/results/{folder}/{instance}.err').read()
        output_path = f'./tests/processed_results/{folder}/{instance}.json'
        # kwargs = {information: '?' for information in trigger_keywords.keys()} | json.loads(open(f'./tests/results/{folder}/{instance}.json').read())
        kwargs = {information: '?' for information in trigger_keywords.keys()}
        kwargs.update(json.loads(open(f'./tests/results/{folder}/{instance}.json').read()))
        for line in data.split('\n'):
            for information, keyword in trigger_keywords.items():
                if keyword in line:
                    value = line.split(keyword)[1].split(' ')[1]
                    if information == 'search_time':
                        value = value[:-1]
                    kwargs[information] = value
        open(output_path, 'w').write(json.dumps(kwargs, indent=4, sort_keys=True))
