def test_error(data):
    if data == None:
        return 'Test not found'
    if 'Time limit reached. Abort search.' in data:
        return 'S Timeout'
    if 'Time limit has been reached' in data:
        return 'S Timeout'
    if 'Memory limit has been reached' in data:
        return 'S Memory out'
    if 'Translator hit the time limit' in data:
        return 'T Timeout'
    if 'Translator ran out of memory' in data:
        return 'T Memory out'
    if 'Initial state is a dead end' in data:
        return 'Dead End'
    if 'Expansion limit reached' in data:
        return 'Limit'
    if 'KeyboardInterrupt' in data:
        return 'Interrupt'
    if 'search exit code: -9' in data:
        return 'Search Error -9'
    if 'search exit code: -11' in data:
        return 'Search Error -11'
    if 'translate exit code: -9' in data:
        return 'Translate Error -9'
    if 'Given pattern is too large! (Overflow occured):' in data:
        return 'PDB too large'
    if 'std::invalid_argument' in data:
        return 'Invalid argument'
    if 'FileNotFoundError' in data:
        return 'Some file not found'

def get_relevant_info_data(raw_data, relevant_info_data):
    if raw_data == None:
        return

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

    splitted_raw_data = raw_data.split('\n')

    for line in splitted_raw_data:
        if trigger_keywords[relevant_info_data] in line:
            value = line.split(trigger_keywords[relevant_info_data])[1].split(' ')[1]
            if relevant_info_data == 'time':
                return value[:-1]
            return value
    else:
        if relevant_info_data == 'solution_cost' and 'Insolution' in raw_data:
            return 'Unsovable'
