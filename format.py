
from abc import ABC, abstractmethod

class Format(ABC):

    def __init__(self):
       self.json = None
       self.html = None
       self.xml = None
       self.csv = None
       self.excel = None


    @abstractmethod
    def asHTML(self, headers):
        # Method implementation here
        pass

    def asJSON(self):
        # Method implementation here
        pass

    def asCSV(self):
        # Method implementation here
        pass

    def asExcel(self):
        # Method implementation here
        pass
