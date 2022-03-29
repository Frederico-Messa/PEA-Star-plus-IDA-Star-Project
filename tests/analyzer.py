import os
from run_configuration import RunConfiguration

class Analyzer:
    relevant_informations = ['total_expansions', 'total_generations', 'closed_peak_size']
    # relevant_informations = ['second_phase_expansions', 'second_phase_iterations']
    # relevant_informations = ['min_f_at_phase_change', 'mean_f_at_phase_change', 'max_f_at_phase_change', 'pct_min_f_at_phase_change', 'solution_cost', 'solution_length']
    run_configurations = sorted([RunConfiguration(pack) for pack in os.listdir(f'./tests/processed_results/') if 'lmcut' in pack and not 'pebound' in pack])
    # run_configurations = sorted([RunConfiguration(pack) for pack in os.listdir(f'./tests/processed_results/') if 'lmcut' in pack])
    # run_configurations = sorted([RunConfiguration(pack) for pack in os.listdir(f'./tests/processed_results/') if 'limited-10' in pack and not 'pebound' in pack and 'lmcut' in pack])

    def __init__(self):
        if not os.path.exists(f'./tests/analysis/'):
            os.mkdir(f'./tests/analysis/')

    def run(self):
        from suite import Suite
        suites = [Suite(suite_name) for suite_name in os.listdir(f'./instances/')]

        for suite in suites:
            suite.analyze()
            suite.save()

if __name__ == '__main__':
    Analyzer().run()
