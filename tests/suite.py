from os import listdir
from analyzer import Analyzer
from super_domain import SuperDomain
from functools import reduce
from statistics import geometric_mean

class Suite:
    def __init__(self, name):
        self.__name__ = name
        super_domains_names = set([domain_name.split('_')[0].split('-')[0].split('0')[0].split('9')[0] for domain_name in listdir(f'./instances/{name}/')])
        self.__super_domains = [SuperDomain(super_domain_name, name) for super_domain_name in sorted(super_domains_names)]

    def analyze(self):
        for super_domain in self.__super_domains:
            super_domain.analyze()

    def __str__(self):
        lines = []
        for header in ['heuristic', 'time_limit', 'memory_limit', 'cost_system', 'algorithm', 'open_limitness']:
            lines.append(',,,' + ''.join([vars(run_configuration)[header] + (4 + len(Analyzer.relevant_informations)) * ',' for run_configuration in Analyzer.run_configurations if run_configuration.suite == self.__name__]))
        lines.append('Super Domain,n,c,' + ','.join(['f.s.,f.i.,m.o.,t.o.,' + ','.join(Analyzer.relevant_informations) for run_configuration in Analyzer.run_configurations if run_configuration.suite == self.__name__]))
        lines.append(f'ALL,{self.number_of_instances},{self.coverage},' + ','.join(map(self.str_by_configuration, range(len([run_configuration for run_configuration in Analyzer.run_configurations if run_configuration.suite == self.__name__])))))
        lines.extend(map(lambda super_domain: str(super_domain), self.__super_domains))
        return '\n'.join(lines)

    def str_by_configuration(self, index):
        return f'{self.number_of_solutions_found(index)}' + ',' + f'{self.number_of_insolutions_found(index)}' + ',' + f'{self.number_of_failures_by_memory(index)}' + ',' + f'{self.number_of_failures_by_time(index)}' + ',' + ','.join(map(lambda information: f'{information_aggregation:.2f}' if (information_aggregation := self.get_information_aggregation(index, information)) != None else '–', Analyzer.relevant_informations))

    def save(self):
        open(f'./tests/analysis/{self.__name__}.csv', 'w').write(str(self))

    @property
    def number_of_instances(self):
        return sum([super_domain.number_of_instances for super_domain in self.__super_domains])

    @property
    def coverage(self):
        return reduce(lambda coverage, partial_coverage: coverage + partial_coverage, [super_domain.coverage for super_domain in self.__super_domains], 0)

    def number_of_solutions_found(self, index):
        return reduce(lambda number_of_solutions_found, partial_number_of_solutions_found: number_of_solutions_found + partial_number_of_solutions_found, [super_domain.number_of_solutions_found(index) for super_domain in self.__super_domains], 0)

    def number_of_insolutions_found(self, index):
        return reduce(lambda number_of_insolutions_found, partial_number_of_insolutions_found: number_of_insolutions_found + partial_number_of_insolutions_found, [super_domain.number_of_insolutions_found(index) for super_domain in self.__super_domains], 0)

    def number_of_failures_by_memory(self, index):
        return reduce(lambda number_of_failures_by_memory, partial_number_of_failures_by_memory: number_of_failures_by_memory + partial_number_of_failures_by_memory, [super_domain.number_of_failures_by_memory(index) for super_domain in self.__super_domains], 0)

    def number_of_failures_by_time(self, index):
        return reduce(lambda number_of_failures_by_time, partial_number_of_failures_by_time: number_of_failures_by_time + partial_number_of_failures_by_time, [super_domain.number_of_failures_by_time(index) for super_domain in self.__super_domains], 0)

    def get_information_aggregation(self, index, information):
        if self.coverage > 0:
            return geometric_mean([super_domain.get_information_aggregation(index, information) + 1 for super_domain in self.__super_domains if super_domain.coverage > 0]) - 1