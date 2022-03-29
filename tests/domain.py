from os import listdir
from instance import Instance
from functools import reduce
from statistics import geometric_mean

class Domain:
    def __init__(self, name, suite_name):
        self.__name__ = name
        self.__suite_name = suite_name
        instances_names = [x[:-5] for x in listdir(f'./instances/{suite_name}/{name}/') if not 'domain' in x and x.endswith('.pddl')]
        self.__instances = [Instance(instance_name, name, suite_name) for instance_name in instances_names]

    def analyze(self):
        for instance in self.__instances:
            instance.analyze()

    @property
    def number_of_instances(self):
        return len(self.__instances)

    @property
    def coverage(self):
        return reduce(lambda coverage, covered: coverage + (1 if covered else 0), [instance.covered for instance in self.__instances], 0)

    def number_of_solutions_found(self, index):
        return reduce(lambda number_of_solutions_found, found_solution: number_of_solutions_found + (1 if found_solution else 0), [instance.found_solution(index) for instance in self.__instances], 0)

    def number_of_insolutions_found(self, index):
        return reduce(lambda number_of_insolutions_found, found_insolution: number_of_insolutions_found + (1 if found_insolution else 0), [instance.found_insolution(index) for instance in self.__instances], 0)

    def number_of_failures_by_memory(self, index):
        return reduce(lambda number_of_failures_by_memory, failed_by_memory: number_of_failures_by_memory + (1 if failed_by_memory else 0), [instance.failed_by_memory(index) for instance in self.__instances], 0)

    def number_of_failures_by_time(self, index):
        return reduce(lambda number_of_failures_by_time, failed_by_time: number_of_failures_by_time + (1 if failed_by_time else 0), [instance.failed_by_time(index) for instance in self.__instances], 0)

    def get_information_aggregation(self, index, information):
        if self.coverage > 0:
            return geometric_mean([instance.get_information_data(index, information) + 1 for instance in self.__instances if instance.covered]) - 1
