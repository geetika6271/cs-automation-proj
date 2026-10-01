from abc import ABC, abstractmethod

class Surface(ABC):

    # @abstractmethod
    # def observe(self):
    #     pass

    @abstractmethod
    def click(self,target):
        pass

    @abstractmethod
    def extract(self,target):
        pass

    @abstractmethod
    def screenshot(self,target):
        pass

    @abstractmethod
    def fill(self, target, value):
        pass

