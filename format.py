
from abc import ABC, abstractmethod

class Format(ABC):
#    def __init__(self, param2):
#        self.param1 = param1
#        self.param2 = param2

    self.json = None
    self.html = None
    self.text = None


    @abstractmethod
    def asHTML(self):
        # Method implementation here
        pass

