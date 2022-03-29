import json

class RunConfiguration:
    def __init__(self, pack):
        self.__name__ = pack
        self.data = json.loads(open(f'./tests/results/{pack}/_config.json').read())
        self.algorithm = self.data['algorithm']
        self.cost_system = self.data['cost_system']
        self.heuristic = self.data['heuristic']
        self.memory_limit = self.data['memory_limit']
        self.open_limitness = self.data['open_limitness']
        self.suite = self.data['suite']
        self.time_limit = self.data['time_limit']

    def __lt__(self, other):
        if self.suite != other.suite:
            return self.suite < other.suite

        if self.cost_system != other.cost_system:
            return self.cost_system < other.cost_system

        if self.heuristic != other.heuristic:
            return self.heuristic < other.heuristic

        if int(self.time_limit[:-1]) * {'s': 1, 'm': 60, 'h': 3600}[self.time_limit[-1]] != int(other.time_limit[:-1]) * {'s': 1, 'm': 60, 'h': 3600}[other.time_limit[-1]]:
            return int(self.time_limit[:-1]) * {'s': 1, 'm': 60, 'h': 3600}[self.time_limit[-1]] < int(other.time_limit[:-1]) * {'s': 1, 'm': 60, 'h': 3600}[other.time_limit[-1]]

        if int(self.memory_limit[:-1]) * {'M': 1000 ** 2, 'G': 1000 ** 3}[self.memory_limit[-1]] != int(other.memory_limit[:-1]) * {'M': 1000 ** 2, 'G': 1000 ** 3}[other.memory_limit[-1]]:
            return int(self.memory_limit[:-1]) * {'M': 1000 ** 2, 'G': 1000 ** 3}[self.memory_limit[-1]] < int(other.memory_limit[:-1]) * {'M': 1000 ** 2, 'G': 1000 ** 3}[other.memory_limit[-1]]

        # if int(self.number_of_threads) != int(other.number_of_threads):
        #     return int(self.number_of_threads) < int(other.number_of_threads)

        if ('unlimited' in self.open_limitness) != ('unlimited' in other.open_limitness):
            return ('unlimited' in self.open_limitness) < ('unlimited' in other.open_limitness)

        if not 'unlimited' in self.open_limitness and not 'unlimited' in other.open_limitness and int(self.open_limitness.split('-')[1]) != int(other.open_limitness.split('-')[1]):
            return int(self.open_limitness.split('-')[1]) < int(other.open_limitness.split('-')[1])

        if ('pe' in self.algorithm) != ('pe' in other.algorithm):
            return ('pe' in self.algorithm) < ('pe' in other.algorithm)

        if ('edd' in self.algorithm) != ('edd' in other.algorithm):
            return ('edd' in self.algorithm) < ('edd' in other.algorithm)

        if ('ipc' in self.algorithm) != ('ipc' in other.algorithm):
            return ('ipc' in self.algorithm) < ('ipc' in other.algorithm)

        return self.__name__ < other.__name__

    def __eq__(self, other):
        return self.__name__ == other.__name__
