from abc import abstractmethod


class Action:
    @abstractmethod
    def run(self):
        pass
