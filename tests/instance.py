from os import remove
from analyzer import Analyzer
from enum import Enum
import json

class Instance:
    def __init__(self, name, domain_name, suite_name):
        self.__name__ = name
        self.__suite_name = suite_name
        results_paths = [f'./tests/processed_results/{run_configuration.__name__}/{domain_name}_{name}.json' for run_configuration in Analyzer.run_configurations if run_configuration.suite == suite_name]
        self.__results = [self.Result(result_path) for result_path in results_paths]

    def analyze(self):
        for result in self.__results:
            result.analyze()

    @property
    def covered(self):
        return all([result.covered for result in self.__results])

    def found_solution(self, index):
        return self.__results[index].found_solution

    def found_insolution(self, index):
        return self.__results[index].found_insolution

    def failed_by_memory(self, index):
        return self.__results[index].failed_by_memory

    def failed_by_time(self, index):
        return self.__results[index].failed_by_time

    def get_information_data(self, index, information):
        return vars(self.__results[index])[information]

    class Result:
        def __init__(self, path: str) -> None:
            self.__path: str = path
            self.__out_path: str = path.replace('processed_results', 'results').replace('.json', '.out')
            self.__err_path: str = path.replace('processed_results', 'results').replace('.json', '.err')
            try:
                self.__data: dict[str, str|int]|None = json.loads(open(self.__path).read())
            except:
                self.__data: dict[str, str|int]|None = None
            try:
                self.__out_data: str|None = open(self.__out_path).read()
            except:
                self.__out_data: str|None = None
            try:
                self.__err_data: str|None = open(self.__err_path).read()
            except:
                self.__err_data: str|None = None

        def analyze(self):
            self.set_status()

            if self.__status == self.Status.NONEXISTENT:
                self.__covered = False
                return

            if self.__status == self.Status.INTERRUPTED:
                print(f'Interrupted: {self.__path}')
                # remove(self.__path)
                self.__covered = False
                return

            if self.__status == self.Status.FAILED_BY_ERROR:
                print(f'Error: {self.__path} | {vars(self).get("_Result__status_description", "Unknown error")}')
                # remove(self.__path)
                self.__covered = False
                return

            self.__covered = True
            for information in Analyzer.relevant_informations:
                try:
                    information_data = self.get_information_data(information)
                    if information in ['search_time', 'mean_f_at_phase_change', 'mean_depth_at_phase_change', 'pct_min_f_at_phase_change']:
                        information_data = float(information_data)
                    else:
                        information_data = int(information_data)
                    setattr(self, information, information_data)
                except:
                    self.__covered = False

        @property
        def covered(self):
            return self.__covered

        @property
        def found_solution(self):
            return self.__status == self.Status.FOUND_SOLUTION

        @property
        def found_insolution(self):
            return self.__status == self.Status.FOUND_INSOLUTION

        @property
        def failed_by_memory(self):
            return self.__status == self.Status.FAILED_BY_LIMIT and 'Memory out' in self.__status_description

        @property
        def failed_by_time(self):
            return self.__status == self.Status.FAILED_BY_LIMIT and 'Timeout' in self.__status_description

        def get_information_data(self, information):
            if self.__data != None:
                if self.__data[information] != '?':
                    return self.__data[information]

        def set_status(self):
            if self.__data == None:
                self.__status = self.Status.NONEXISTENT
                return
            if 'Solution found!'in self.__out_data + self.__err_data:
                self.__status = self.Status.FOUND_SOLUTION
                return
            if 'Insolution found!'in self.__out_data + self.__err_data:
                self.__status = self.Status.FOUND_INSOLUTION
                return
            if 'Initial state is a dead end'in self.__out_data + self.__err_data:
                self.__status = self.Status.FOUND_INSOLUTION
                return
            if 'Time limit reached. Abort search.'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_LIMIT
                self.__status_description = 'S Timeout'
                return
            if 'Time limit has been reached'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_LIMIT
                self.__status_description = 'S Timeout'
                return
            if 'Memory limit has been reached'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_LIMIT
                self.__status_description = 'S Memory out'
                return
            if 'Translator hit the time limit'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_LIMIT
                self.__status_description = 'T Timeout'
                return
            if 'Translator ran out of memory'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_LIMIT
                self.__status_description = 'T Memory out'
                return
            if 'Expansion limit reached'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_LIMIT
                self.__status_description = 'Limit'
                return
            if 'KeyboardInterrupt'in self.__out_data + self.__err_data:
                self.__status = self.Status.INTERRUPTED
                return
            if 'search exit code: -9'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_ERROR
                self.__status_description = 'Search Error -9'
                return
            if 'search exit code: -11'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_ERROR
                self.__status_description = 'Search Error -11'
                return
            if 'translate exit code: -9'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_ERROR
                self.__status_description = 'Translate Error -9'
                return
            if 'Given pattern is too large! (Overflow occured):'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_ERROR
                self.__status_description = 'PDB too large'
                return
            if 'std::invalid_argument'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_ERROR
                self.__status_description = 'Invalid argument'
                return
            if 'FileNotFoundError'in self.__out_data + self.__err_data:
                self.__status = self.Status.FAILED_BY_ERROR
                self.__status_description = 'Some file not found'
                return
            self.__status = self.Status.FAILED_BY_ERROR

        class Status(Enum):
            FOUND_SOLUTION = 1
            FOUND_INSOLUTION = 2
            FAILED_BY_LIMIT = 3
            FAILED_BY_ERROR = 4
            INTERRUPTED = 5
            NONEXISTENT = 6
