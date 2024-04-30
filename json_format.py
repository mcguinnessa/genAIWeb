
from format import Format

class JSONFormat(Format):
    def __init__(self, body):
        self.json = body
        self.html = None
        self.text = None

    def method1(self):
        # Method implementation here
        pass
