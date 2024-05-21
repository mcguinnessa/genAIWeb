
from abc import ABC, abstractmethod
import json


class Format(ABC):
   
   HTML_SUFFIX = ".html"
   JSON_SUFFIX = ".json"
   CSV_SUFFIX = ".csv"
   TXT_SUFFIX = ".txt"

   def __init__(self):
      self.json = None
      self.html = None
      self.xml = None
      self.csv = None

      self.filename_base = "genai_tests_default"
      self.filename = self.filename_base + self.TXT_SUFFIX


   def set_filename_base(self, filename_base):
      self.filename_base = filename_base

   def get_filename(self):
      return self.filename

#########################################################################
#
# Writes the tests to file in Text
#
#########################################################################
   def write_to_file_as_text(self, text, suffix):
      #self.filename = self.filename_base + self.TXT_SUFFIX
      self.filename = self.filename_base + suffix

      with open(self.filename, "w") as output_file:
         output_file.write(text)

      text_str = "Tests(text) written to file, " + self.filename
      print(text_str)

#########################################################################
#
# Writes the tests to file in Text
#
#########################################################################
   def write_to_file_as_html(self):
      self.filename = self.filename_base + self.HTML_SUFFIX

      with open(self.filename, "w") as output_file:
         output_file.write(self.html)

      text_str = "Tests(HTML) written to file, " + self.filename
      print(text_str)

#########################################################################
#
# Writes the tests to file in JSON
#
#########################################################################
   def write_to_file_as_json(self):
      self.filename = self.filename_base + self.JSON_SUFFIX

      with open(self.filename, "w") as output_file:
         json.dump(self.json, output_file, indent=3)

      text_str = "Tests(json) written to file, " + self.filename
      print(text_str)

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
