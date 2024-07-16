
from abc import ABC, abstractmethod
import json
import os
import glob
import datetime

FILENAME_PREFIX = "gentests-"


class Format(ABC):
   
   HTML_SUFFIX = ".html"
   JSON_SUFFIX = ".json"
   CSV_SUFFIX = ".csv"
#   TXT_SUFFIX = ".txt"
   XML_SUFFIX = ".xml"

   ##################################################################################
   #
   # Deletes all files with the given suffixes
   #
   ##################################################################################
   @staticmethod
   def delete_files():

      for suffix in [Format.HTML_SUFFIX, Format.JSON_SUFFIX, Format.CSV_SUFFIX, Format.XML_SUFFIX]:

         print(f"Deleting "+ FILENAME_PREFIX+"*"+suffix + " files")
         directory = "./"
         search_pattern = search_pattern = os.path.join(directory, FILENAME_PREFIX+"*"+suffix)
         files = glob.glob(search_pattern)

         for f in files:
            try:
               os.remove(f)
               print(f"Deleted: {f}")
            except Exception as e:
               print(f"Failed to delete: {f}: {e}")


   def __init__(self):
      self.html = None
      self.json = None
      self.csv = None
#      self.txt = None
      self.xml = None

      current_time = datetime.datetime.now()
      self.filename_base = FILENAME_PREFIX + current_time.strftime("%Y%m%d-%H%M")
      print("Filename Base:" + self.filename_base)


#      self.filename_base = "genai_tests_default"
#      txt_filename = self.filename_base + self.TXT_SUFFIX
#      self.filenames = {}


#   def set_filename_base(self, filename_base):
#      self.filename_base = filename_base

#   def get_filename(self):
#      return self.filename

   def get_filename(self, suffix):
      return self.filename_base + suffix
#      print("LOOKING FOR:" + str(suffix) + " FILES:" + str(self.filenames))
#      if suffix in self.filenames.keys():
#         return self.filenames[suffix]
#      else:
#         return self.filenames[self.XML_SUFFIX]

#########################################################################
#
# Writes the tests to file in Text
#
#########################################################################
   def write_to_file_as_text(self, text, suffix):
      #self.filename = self.filename_base + self.TXT_SUFFIX
      filename = self.filename_base + suffix

      print("Writing to file:" + filename)
#      self.filenames[suffix] = filename

      with open(filename, "w") as output_file:
         output_file.write(text)

      text_str = "Tests(text) written to file, " + filename
      print(text_str)

#########################################################################
#
# Writes the tests to file in Text
#
#########################################################################
   def write_to_file_as_html(self):
      filename = self.filename_base + self.HTML_SUFFIX
#      self.filenames[self.HTML_SUFFIX] = filename
 

      with open(filename, "w") as output_file:
         output_file.write(self.html)

      text_str = "Tests(HTML) written to file, " + filename
      print(text_str)

#########################################################################
#
# Writes the tests to file in JSON
#
#########################################################################
   def write_to_file_as_json(self):
      filename = self.filename_base + self.JSON_SUFFIX
#      self.filenames[self.JSON_SUFFIX] = filename

      with open(filename, "w") as output_file:
         json.dump(self.json, output_file, indent=3)

      text_str = "Tests(json) written to file, " + filename
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

#   def asExcel(self):
#       # Method implementation here
#       pass


   def getHTMLFilename(self):
      return self.get_filename(self.HTML_SUFFIX)

   def getJSONFilename(self):
      return self.get_filename(self.JSON_SUFFIX)

   def getCSVFilename(self):
      return self.get_filename(self.CSV_SUFFIX)

#   def getTxtFilename(self):
#      return self.get_filename(self.TXT_SUFFIX)

   def getXMLFilename(self):
      return self.get_filename(self.XML_SUFFIX)
