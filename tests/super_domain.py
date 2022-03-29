from os import listdir
from analyzer import Analyzer
from domain import Domain
from functools import reduce
from statistics import geometric_mean

class SuperDomain:
    def __init__(self, name, suite_name):
        self.__name__ = name
        self.__suite_name = suite_name
        domains_names = [domain_name for domain_name in listdir(f'./instances/{suite_name}/') if domain_name.split('_')[0].split('-')[0].split('0')[0].split('9')[0] == name]
        self.__domains = [Domain(domain_name, suite_name) for domain_name in domains_names]

    def analyze(self):
        for domain in self.__domains:
            domain.analyze()

    def __str__(self):
        return f'{self.__name__}' + ',' + f'{self.number_of_instances}' + ',' + f'{self.coverage}' + ',' + ','.join(map(self.str_by_configuration, range(len([run_configuration for run_configuration in Analyzer.run_configurations if run_configuration.suite == self.__suite_name]))))

    def str_by_configuration(self, index):
        return f'{self.number_of_solutions_found(index)}' + ',' + f'{self.number_of_insolutions_found(index)}' + ',' + f'{self.number_of_failures_by_memory(index)}' + ',' + f'{self.number_of_failures_by_time(index)}' + ',' + ','.join(map(lambda information: f'{information_aggregation:.2f}' if (information_aggregation := self.get_information_aggregation(index, information)) != None else '-', Analyzer.relevant_informations))

    @property
    def number_of_instances(self):
        return sum([domain.number_of_instances for domain in self.__domains])

    @property
    def coverage(self):
        return reduce(lambda coverage, partial_coverage: coverage + partial_coverage, [domain.coverage for domain in self.__domains], 0)

    def number_of_solutions_found(self, index):
        return reduce(lambda number_of_solutions_found, partial_number_of_solutions_found: number_of_solutions_found + partial_number_of_solutions_found, [domain.number_of_solutions_found(index) for domain in self.__domains], 0)

    def number_of_insolutions_found(self, index):
        return reduce(lambda number_of_insolutions_found, partial_number_of_insolutions_found: number_of_insolutions_found + partial_number_of_insolutions_found, [domain.number_of_insolutions_found(index) for domain in self.__domains], 0)

    def number_of_failures_by_memory(self, index):
        return reduce(lambda number_of_failures_by_memory, partial_number_of_failures_by_memory: number_of_failures_by_memory + partial_number_of_failures_by_memory, [domain.number_of_failures_by_memory(index) for domain in self.__domains], 0)

    def number_of_failures_by_time(self, index):
        return reduce(lambda number_of_failures_by_time, partial_number_of_failures_by_time: number_of_failures_by_time + partial_number_of_failures_by_time, [domain.number_of_failures_by_time(index) for domain in self.__domains], 0)

    def get_information_aggregation(self, index, information):
        if self.coverage > 0:
            return geometric_mean([domain.get_information_aggregation(index, information) + 1 for domain in self.__domains if domain.coverage > 0]) - 1

