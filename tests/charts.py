import os
from matplotlib import pyplot as plt
from math import floor, ceil, log10

heuristic = 'lmcut'

algorithms = [('limited-90', 'pe-edd-eh'), ('limited-50', 'pe-edd-eh'), ('limited-10', 'pe-edd-eh'), ('limited-90', 'edd-eh'), ('limited-50', 'edd-eh'), ('limited-10', 'edd-eh')]

instances = []

for domain in os.listdir(f'./instances/FD-IPC-opt-strips/'):
    domain_pddls = list(sorted([x[:-5] for x in os.listdir(f'./instances/FD-IPC-opt-strips/{domain}/') if 'domain' in x and x.endswith('.pddl')]))
    instances_pddls = list(sorted([x[:-5] for x in os.listdir(f'./instances/FD-IPC-opt-strips/{domain}/') if not 'domain' in x and x.endswith('.pddl')]))

    for instanceIndex, instance_pddl in enumerate(instances_pddls):
        if len(domain_pddls) == 1:
            domain_pddl = domain_pddls[0]
        else:
            domain_pddl = domain_pddls[instanceIndex]

        f_pack = ','.join(['edd-eh', 'real-costs', heuristic, '2G', 'unlimited', 'FD-IPC-opt-strips', '10m'])
        f = open(f'./tests/results/{f_pack}/{domain}_{instance_pddl}.out').read()
        if not 'Solution found!' in f:
            continue

        g_pack = ','.join(['edd-eh', 'real-costs', 'blind', '2G', 'unlimited', 'FD-IPC-opt-strips', '10m'])
        g = open(f'./tests/results/{g_pack}/{domain}_{instance_pddl}.out').read()
        if 'Solution found!' in g:
            continue

        some_algorithm_failed = False

        flag_pea = False
        flag_a = False

        for x, y in algorithms:
            h_pack = ','.join([y, 'real-costs', heuristic, '2G', x, 'FD-IPC-opt-strips', '360m'])
            h = open((f'./tests/results/{h_pack}/{domain}_{instance_pddl}.out')).read()
            if not 'Solution found!' in h:
                some_algorithm_failed = True
                if x == 'limited-10' and y == 'edd-eh':
                    flag_a = True
                if x == 'limited-10' and y == 'pe-edd-eh':
                    flag_pea = True

        if flag_a and not flag_pea:
            print('only pea solves', domain, instance_pddl)
        if flag_pea and not flag_a:
            print('only a solves', domain, instance_pddl)

        if some_algorithm_failed:
            continue

        for x in ['limited-90-pebound-90', 'limited-50-pebound-50', 'limited-10-pebound-10']:
            h_pack = ','.join(['edd-eh', 'real-costs', heuristic, '2G', x, 'FD-IPC-opt-strips', '360m'])
            h = open((f'./tests/results/{h_pack}/{domain}_{instance_pddl}.out')).read()
            if not 'Solution found!' in h:
                some_algorithm_failed = True
                break

        if some_algorithm_failed:
            continue

        instances.append((domain, instance_pddl))

boths = {algorithm: [] for algorithm in algorithms}
firsts = {algorithm: [] for algorithm in algorithms}
seconds = {algorithm: [] for algorithm in algorithms}

for x, y in algorithms:
    h_pack = ','.join([y, 'real-costs', heuristic, '2G', x, 'FD-IPC-opt-strips', '360m'])

    for domain, instance_pddl in instances:
        h = open(f'./tests/results/{h_pack}/{domain}_{instance_pddl}.out').read().split('\n')
        for line in h:
            if 'Expanded' in line:
                both = int(line.split('Expanded')[1].split(' ')[1])
            if 'Number of first phase expansions:' in line:
                first = int(line.split('Number of first phase expansions:')[1].split(' ')[1])
            if 'Number of second phase expansions:' in line:
                second = int(line.split('Number of second phase expansions:')[1].split(' ')[1])

        boths[(x, y)].append(both)
        firsts[(x, y)].append(first)
        seconds[(x, y)].append(second)

maximum_both = 0
maximum_first = 0
maximum_second = 0
max_ratio = 0
min_ratio = float('inf')
for x in ['limited-90', 'limited-50', 'limited-10']:
    maximum_both = max(max(boths[(x,'edd-eh')] + boths[(x,'pe-edd-eh')]), maximum_both)
    maximum_first = max(max(firsts[(x,'edd-eh')] + firsts[(x,'pe-edd-eh')]), maximum_first)
    maximum_second = max(max(seconds[(x,'edd-eh')] + seconds[(x,'pe-edd-eh')]), maximum_second)

    for a, b in zip(boths[(x,'edd-eh')], boths[(x,'pe-edd-eh')]):
        max_ratio = max(a / b, max_ratio)
        min_ratio = min(a / b, min_ratio)

for x in ['limited-90', 'limited-50', 'limited-10']:
    plt.figure(figsize=(5.2, 4.4), dpi=300)

    plt.scatter(boths[(x,'edd-eh')], boths[(x,'pe-edd-eh')], c='black', marker='o')

    # plt.xlabel('A*+IDA* number of expansions')
    # plt.ylabel('PEA*+IDA* number of expansions')

    plt.xscale('symlog', linthresh = 9)
    plt.yscale('symlog', linthresh = 9)

    plt.grid(True)
    plt.xticks(size=30, ticks=[10, 1000, 10**5, 10**7, 10**9], labels=['', '', '', '', ''])
    plt.yticks(size=30, ticks=[10, 1000, 10**5, 10**7, 10**9], labels=['$10^1$', '$10^3$', '$10^5$', '$10^7$', '$10^9$'])

    plt.xlim(-1, 10**(ceil(log10(2 * maximum_both))))
    plt.ylim(-1, 10**(ceil(log10(2 * maximum_both))))

    plt.axline([0, 0], [1, 1], color='black', linestyle='-')

    plt.tick_params(length=10)
    plt.minorticks_off()
    plt.tight_layout()
    plt.subplots_adjust(left=0.2, bottom=0.05)

    plt.savefig(f'./tests/analysis/tasks_scatter_{x}.png')

    plt.figure(figsize=(5.2, 4.4), dpi=300)

    plt.scatter(firsts[(x,'edd-eh')], firsts[(x,'pe-edd-eh')], c='black', marker='o')

    # plt.xlabel('A*+IDA* number of expansions')
    # plt.ylabel('PEA*+IDA* number of expansions')

    plt.xscale('symlog', linthresh = 9)
    plt.yscale('symlog', linthresh = 9)

    plt.grid(True)
    plt.xticks(size=30, ticks=[10, 1000, 10**5, 10**7, 10**9], labels=['', '', '', '', ''])
    plt.yticks(size=30, ticks=[10, 1000, 10**5, 10**7, 10**9], labels=['$10^1$', '$10^3$', '$10^5$', '$10^7$', '$10^9$'])

    plt.xlim(-1, 10**(ceil(log10(2 * maximum_first))))
    plt.ylim(-1, 10**(ceil(log10(2 * maximum_first))))

    plt.axline([0, 0], [1, 1], color='black', linestyle='-')

    plt.tick_params(length=10)
    plt.minorticks_off()
    plt.tight_layout()
    plt.subplots_adjust(left=0.2, bottom=0.05)

    plt.savefig(f'./tests/analysis/tasks_first_scatter_{x}.png')

    plt.figure(figsize=(5.2, 4.4), dpi=300)

    plt.scatter(seconds[(x,'edd-eh')], seconds[(x,'pe-edd-eh')], c='black', marker='o')

    # plt.xlabel('A*+IDA* number of expansions')
    # plt.ylabel('PEA*+IDA* number of expansions')

    plt.xscale('symlog', linthresh = 9)
    plt.yscale('symlog', linthresh = 9)

    plt.grid(True)
    plt.xticks(size=30, ticks=[10, 1000, 10**5, 10**7, 10**9], labels=['', '', '', '', ''])
    plt.yticks(size=30, ticks=[10, 1000, 10**5, 10**7, 10**9], labels=['$10^1$', '$10^3$', '$10^5$', '$10^7$', '$10^9$'])

    plt.xlim(-1, 10**(ceil(log10(2 * maximum_second))))
    plt.ylim(-1, 10**(ceil(log10(2 * maximum_second))))

    plt.axline([0, 0], [1, 1], color='black', linestyle='-')

    plt.tick_params(length=10)
    plt.minorticks_off()
    plt.tight_layout()
    plt.subplots_adjust(left=0.2, bottom=0.05)

    plt.savefig(f'./tests/analysis/tasks_second_scatter_{x}.png')

    ratios = []

    for a, b in zip(boths[(x,'edd-eh')], boths[(x,'pe-edd-eh')]):
        ratios.append(a / b)

    plt.figure(figsize=(2.6, 2.2), dpi=300)
    plt.rc('font', size=12)
    plt.subplots_adjust(left=0.25)

    plt.plot(sorted(ratios), color='black', marker='.', linestyle='')

    # plt.xlabel('Tasks')
    # plt.ylabel('A*+IDA*:PEA*+IDA* ratio of number of expansions')

    plt.yscale('log')

    plt.ylim(10**(floor(log10(min_ratio / 2))), 10**(ceil(log10(2 * max_ratio))))

    plt.grid(True)
    plt.xticks([0, len(instances)])
    plt.yticks(list(map(lambda x: 10**x, range(floor(log10(min_ratio / 2)), ceil(log10(2 * max_ratio)) + 2, 2))))

    plt.axhline(y=1, color='black', linestyle='-')

    plt.savefig(f'./tests/analysis/tasks_ratios_{x}.png')
