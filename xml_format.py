
from format import Format

import xml.etree.ElementTree as ET

################################################################################
#
# Display Data as XML
#
################################################################################
class XMLFormat(Format):
    def __init__(self, body, headings):
       super(XMLFormat, self).__init__()
       self.xml = body
       self.headings = headings
       #self.asXML()
       self.write_to_file_as_text(self.xml, Format.XML_SUFFIX)

################################################################################
#
# Display Data as XML
#
################################################################################
    def asXML(self):
#       if not self.xml or len(self.xml) == 0:
#
#          if len(self.xml) <= 0:
#             return ""
#
#          self.write_to_file_as_text(self.xml, Format.XML_SUFFIX)
#
       print("Returning XML Format:" + str(self.xml))  
       return self.xml

################################################################################
#
# Display Data as HTML
#
################################################################################
    def asHTML(self):
       if not self.html or len(self.html) == 0:

          if len(self.xml) <= 0:
             return  ""

          print("XML:" + str(self.xml))
          root = ET.fromstring(self.xml)
          
          print("Root:" + str(root))

          tc_objs = {}
          for tc in root.findall('tc'):
             tc_obj = {}
             for el in tc:
                print("El Tag:" + str(el.tag))
                print("El text:" + str(el.text))
                tc_obj[el.tag] = el.text
             tc_objs[tc_obj[list(self.headings.values())[0]]] = tc_obj

          html = "<tr>"
          for hdr in self.headings.keys():
             html += f"<th>{hdr}</th>"
          html += "</tr>\n"
 
          print("ALL OBJS:" + str(tc_objs))
          print("Headers:" + str(self.headings))
          for id, tc_obj in tc_objs.items():
            print("OBJ:" + str(tc_obj))
            html += "<tr>\n"
            for htag, xtag in self.headings.items():
               print("Looking for " + xtag + " in object")
               html += f"<td>{tc_obj[xtag]}</td>\n"
            html += "</tr>\n"

          self.html = f"""<table>{html}</table>\n"""

          self.write_to_file_as_html()

       print("Returning HTML Format:" + str(self.html))  
       return self.html


################################################################################
#
# Display Data as JSON
#
################################################################################
    def asJSON(self):
       if not self.json or len(self.json) == 0:

          self.json = []

          if len(self.xml) <= 0:
             return {} 
 
          print("XML:" + str(self.xml))
          root = ET.fromstring(self.xml)
          print("Root:" + str(root))

          tc_objs = {}
          for tc in root.findall('tc'):
             print("TC:" + str(tc))
             print("TC Type:" + str(type(tc)))
             tc_obj = {}
             for htag, xtag in self.headings.items():
                tc_obj[htag] = tc.find(xtag).text
                #tc_obj[htag] = tc[xtag]
             self.json.append(tc_obj)  

          self.write_to_file_as_json()
       print("Returning JSON Format:" + str(self.json))  
       return self.json

################################################################################
#
# Display Data as CSV
#
################################################################################
    def asCSV(self):
       
       if not self.csv or len(self.csv) == 0:

          self.csv = ""
          self.csv += ",".join(self.headings.keys())
          self.csv += "\n"

          if len(self.xml) <= 0:
             return "" 

          print("XML:" + str(self.xml))
          root = ET.fromstring(self.xml)
          print("Root:" + str(root))

          for tc in root.findall('tc'):
             print("TC:" + str(tc))
             print("TC Type:" + str(type(tc)))
             row = []
             for htag, xtag in self.headings.items():
                row_text = tc.find(xtag).text
                row_text = row_text.replace(',', ';')
                row.append(row_text.replace('\n', ''))
                #tc_obj[htag] = tc.find(xtag).text
                #tc_obj[htag] = tc[xtag]
             #self.json.append(tc_obj)  
             self.csv += ",".join(row) + '\n'


          self.write_to_file_as_text(self.csv, Format.CSV_SUFFIX)
       print("Returning CSV Format:" + str(self.csv))  
       return self.csv



