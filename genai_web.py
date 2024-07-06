#!/usr/bin/python3

import websocket
import json
from contextlib import closing
from dataclasses import dataclass
from uuid import uuid4
import re
import time
import datetime
import requests
import os
import glob
import gradio as gr
from xml_format import XMLFormat
from format import Format
from collections import OrderedDict
from pathlib import Path
from backend_enum import Backend
from backend_ge import BackendGenerativeEngine
from backend_sd import BackendSingleDoc


from langchain_core.prompts import PromptTemplate

DEFAULT_WORKSPACE = "e3a39d26-007d-4386-a6c3-86fa3a362857"
DEFAULT_DOCUMENT_ID = "ARC-Backup-Restore-HLD.docx"
#DEFAULT_DOCUMENT_ID = "ECN_MED_NFS_v1.docx"
#PROMPT_ELEMENT_TEMPLATE = """Parallel Ringing"""
#PROMPT_FOCUS_TEMPLATE = "Focus on the area Multiple Early Dialogue"
PROMPT_ELEMENT_TEMPLATE = """HLR"""
PROMPT_FOCUS_TEMPLATE = "Focus on the area Backup and Restore"

#DEFAULT_WORKSPACE = ""
#DEFAULT_DOCUMENT_ID = ""
#PROMPT_ELEMENT_TEMPLATE = """element"""
#PROMPT_FOCUS_TEMPLATE = "Focus on the area "

FILENAME_PREFIX = "gentests-"

g_backend = Backend.GENERATIVE_ENGINE

#WORKSPACE_ID = os.environ['WORKSPACE_ID']
#SOCKET_URL = "wss://datw9crxl8.execute-api.us-east-1.amazonaws.com/socket/"
API_TOKEN = os.environ['API_KEY']
UI_PASSWORD = os.environ['UI_PASSWORD']
UI_USER = os.environ['UI_USER']

TESTS_PER_CALL = 10

FORMAT_OPTIONS = ["HTML", "JSON", "Excel (CSV)", "XML"]
BACKEND_CHOICES=["Generative Engine", "Single Doc Engine"] 

ELEMENT_INFO="This is the element that is the subject of the tests" 
FOCUS_INFO = "The area you want the tests to focus on, it could be a subsystem or a new area of functionality. Or a freeform instruction to the LLM (optional)"
NUMBER_INFO="The number of tests to be generated"
FORMAT_INFO="The Format to display the tests in"
ROLE_INFO="Who are the tests for?"
TEST_INFO="Which types of tests are requried"
WORKSPACE_INFO="This is the workspace defined in Capgemini Generative Engine where the relevant documentation has been uploaded"
DOCUMENT_INFO="This is document in the workspace that the test cases will be inferred from"

DEFAULT_MODEL_IDX = 0
model_dict = {"mistral.mixtral-8x7b-instruct-v0:1" : ("bedrock", 4096),
              "mistral.mistral-large-2402-v1:0" : ("bedrock", 4096 ),
#               "mistral.mistral-7b-instruct-v0:2" : 4096,
              "meta.llama2-70b-chat-v1" : ("bedrock", 2048),
              "meta.llama3-70b-instruct-v1:0" : ("bedrock", 2048),
              "meta.llama3-8b-instruct-v1:0" : ("bedrock", 2048),
              "ai21.j2-ultra-v1" : ("bedrock", 4096),
              "amazon.titan-tg1-large" : ("bedrock", 4096) ,
#              "amazon.titan-text-premier-v1:0" : ("bedrock", 4096) ,
#              "amazon.titan-olympus-premier-v1:0" : ("bedrock", 4096) ,
#              "amazon.titan-text-lite-v1" : ("bedrock", 4096) ,
#              "amazon.titan-text-express-v1" : ("bedrock", 4096) ,
              "ai21.j2-grande-instruct" : ("bedrock", 4096),
              "ai21.j2-jumbo-instruct" : ("bedrock", 4096),
#              "ai21.j2-mid" : ("bedrock", 4096),
#              "ai21.j2-mid-v1" : ("bedrock", 4096),
              "ai21.j2-ultra" : ("bedrock", 4096),
              "ai21.j2-ultra-v1" : ("bedrock", 4096),
	      "anthropic.claude-instant-v1" : ("bedrock", 4096),
              "anthropic.claude-v2:1" : ("bedrock", 4096),
              "anthropic.claude-v2" : ("bedrock", 4096),
#              "anthropic.claude-3-sonnet-20240229-v1:0" : ("bedrock", 4096),
#              "anthropic.claude-3-haiku-20240307-v1:0" : ("bedrock", 4096),
              "cohere.command-text-v14" : ("bedrock", 4096),
              "cohere.command-r-v1:0" : ("bedrock", 4096),
              "cohere.command-r-plus-v1:0" : ("bedrock", 4096),
#              "cohere.command-light-text-v14" : ("bedrock", 4096),
              "openai.gpt-3.5-turbo" : ("azure", 4096),
              "openai.gpt-4" : ("azure", 4096),
              "openai.gpt-4o" : ("azure", 4096) }
            
HEADING_NO = "No."
HEADING_NAME = "Test Name"
HEADING_DESC = "Description"
HEADING_ID = "Test ID"
HEADING_PRE = "Pre-Conditions"
HEADING_STEPS = "Steps"
HEADING_RESULTS = "Expected Results"


XML_HEADING_NO = HEADING_NO.replace(".","")
XML_HEADING_NAME = HEADING_NAME.replace(" ","")
XML_HEADING_DESC = HEADING_DESC.replace(" ","")
XML_HEADING_ID = HEADING_ID.replace(" ","")
XML_HEADING_PRE = HEADING_PRE.replace(" ","").replace("-","")
XML_HEADING_STEPS = HEADING_STEPS.replace(" ","")
XML_HEADING_RESULTS = HEADING_RESULTS.replace(" ","")

XML_HEADINGS = OrderedDict({HEADING_NO : XML_HEADING_NO, HEADING_NAME : XML_HEADING_NAME, HEADING_DESC : XML_HEADING_DESC, HEADING_ID : XML_HEADING_ID, HEADING_PRE : XML_HEADING_PRE, HEADING_STEPS : XML_HEADING_STEPS, HEADING_RESULTS : XML_HEADING_RESULTS})

data_object = XMLFormat("", XML_HEADINGS)

##################################################################################
#
# Validate the Element Field
#
##################################################################################
def validate_element(input):
   rc = False
   el_len = len(input)
   if el_len < 32 and el_len > 0:
      rc = True

   return rc

##################################################################################
#
# Validate The Focus Field
#
##################################################################################
def validate_focus(input):
   rc = False
   if len(input) < 128: 
      rc = True

   return rc

############################################################
#
# Gets the backend
#
############################################################
def get_backend():
   if g_backend == Backend.GENERATIVE_ENGINE:
      return BackendGenerativeEngine(API_TOKEN)
   elif g_backend == Backend.SINGLE_DOC:
      return BackendSingleDoc()

############################################################
#
# Generates the tests
#
############################################################
def generate_tests(model, element, focus, format, workspace_id, document_id, temperature, topp, max_tokens, num_tests,
                   role, type):

   global data_object
   global g_backend

   session_id = uuid4()

   delete_files()
 
   focus = str(focus)
   element = str(element)
   print("Element:" + element)
   print("Focus(len):" + focus + ":" + str(len(focus)))
   print("Format:" + format)
  
   #response = [html_box, json_box, text_box, column, download_btn]
   rc = ["", "{}", "", gr.Column(visible=True), None ]

   if not validate_element(element):
      return "Invalid Element input"

   if not validate_focus(focus):
      return "Invalid Focus input"

   if num_tests >= TESTS_PER_CALL:
      num_tests_to_ask_for = TESTS_PER_CALL
   else:
      num_tests_to_ask_for = num_tests

   secondary_target = ""

   if 0 < len(focus):
      #secondary_target = f" including the for the service {focus}."
      secondary_target = f"{focus}."

   formatting_prefix = ""
   formatting_suffix = ""
   format_separator = ""

   formatting = f"""Each test cases must be presented as an XML object. The number must start from 1.
      Here is an example of the desired output for a single test case : 
         <tc>
           <{XML_HEADINGS[HEADING_NO]}>No</{XML_HEADINGS[HEADING_NO]}>
           <{XML_HEADINGS[HEADING_NAME]}>Name</{XML_HEADINGS[HEADING_NAME]}>
           <{XML_HEADINGS[HEADING_DESC]}>Description.</{XML_HEADINGS[HEADING_DESC]}>
           <{XML_HEADINGS[HEADING_ID]}>ID</{XML_HEADINGS[HEADING_ID]}>
           <{XML_HEADINGS[HEADING_PRE]}>Prerequisites.</{XML_HEADINGS[HEADING_PRE]}>
           <{XML_HEADINGS[HEADING_STEPS]}>1. Step one.; 2. Step two </{XML_HEADINGS[HEADING_STEPS]}>
           <{XML_HEADINGS[HEADING_RESULTS]}>1. Result one.; 2. Result two </{XML_HEADINGS[HEADING_RESULTS]}>
         </tc>
    """
#      <tc>
#        <{XML_HEADINGS[HEADING_NO]}>1</{XML_HEADINGS[HEADING_NO]}>
#        <{XML_HEADINGS[HEADING_NAME]}>Backup and Restore of Filesystem Data</{XML_HEADINGS[HEADING_NAME]}>
#        <{XML_HEADINGS[HEADING_DESC]}>Verify that the ARC supports backup and restore of filesystem data.</{XML_HEADINGS[HEADING_DESC]}>
#        <{XML_HEADINGS[HEADING_ID]}>XID_001</{XML_HEADINGS[HEADING_ID]}>
#        <{XML_HEADINGS[HEADING_PRE]}>The ARC is properly configured and connected to the storage system.</{XML_HEADINGS[HEADING_PRE]}>
#        <{XML_HEADINGS[HEADING_STEPS]}>1. Create a backup.\n 2. Restore the filesystem data from the backup.\n 3. Verify backup\n</{XML_HEADINGS[HEADING_STEPS]}>
#        <{XML_HEADINGS[HEADING_RESULTS]}>1. The backup is created\n 2, The backup is restored.\n 3. The backup is verified\n</{XML_HEADINGS[HEADING_RESULTS]}>
#      </tc>
#  """

   display_idx = 0
   formatting_prefix = "<test-cases>"
   formatting_suffix = "</test-cases>"
   format_separator = ""

   prompt = f"""You are a {role}. Generate {num_tests_to_ask_for} unique test cases for {element}. {secondary_target}. Test should be inferred from the documentation: {document_id}. Include information obtained from this documentation explicity rather than referring to the document in the test case.

     The test cases must be {type} test cases.
 
     {formatting} 
     Do not generate any superfluous output that is not part of test case.

     The test cases must contain the fields in the following order: {HEADING_NO}, {HEADING_NAME}, {HEADING_DESC}, {HEADING_ID}, {HEADING_PRE}, {HEADING_STEPS}, and {HEADING_RESULTS} as specified by the definition of a Test Case as specified in Test_Case_definition.txt.

     """

#   {HEADING_NO}' is an abbreviation for number. This is a unique integer for each test case, starting from 1 and incrementing by 1 for each test case. 
#   {HEADING_NAME} is a useful short description of the test. 
#   {HEADING_DESC} is a summary of the test and should end in -{element}. 
#   {HEADING_ID} is an alpha-numeric ID, unique for each case and derived from {element}. 
#   {HEADING_PRE} describes the preconditions needed for the tests to be executed. 
#   {HEADING_STEPS} is a series of at least 3 steps that clearly describes how to execute the test case. Each step must be numbered. 
#   {HEADING_RESULTS} describes the expected outcome for each step itemised in, each outcome must be numbered {HEADING_STEPS}.

#   if g_backend == Backend.GENERATIVE_ENGINE:
#      backend = BackendGenerativeEngine(API_TOKEN)
#   elif g_backend == Backend.GENERATIVE_ENGINE:
#      backend = BackendSingleDoc()
   backend = get_backend()

#   ws = websocket.create_connection(url, header={"x-api-key": API_TOKEN})
   output_array = []
   tests_remaining = num_tests
   while tests_remaining > 0:




      provider = model_dict[model][0]

      #query_output = send_query(ws, model, prompt, session_id, workspace_id, temperature, topp, max_tokens)
      #query_output = send_query_be(ws, model, prompt, session_id, workspace_id, temperature, topp, max_tokens)
      output = backend.send_query(model, provider, prompt, session_id, workspace_id, temperature, topp, max_tokens)
      stripped = enforce_format(output, "XML")
  
      if stripped:
         output_array.append(stripped)

      tests_remaining -= num_tests_to_ask_for
      if tests_remaining >= TESTS_PER_CALL:
         num_tests_to_ask_for = TESTS_PER_CALL
      else:
         num_tests_to_ask_for = tests_remaining
      prompt = f"Generate another {num_tests_to_ask_for} unique test cases using the same requirements in the same output format. Ensure the numbering is continuous"

      print("Response Length:" + str(len(output)))


#   ws.close()








   output = format_separator.join(output_array)

   data_object = XMLFormat(f"{formatting_prefix}{output}{formatting_suffix}", XML_HEADINGS)

   current_time = datetime.datetime.now()
  
   filename_base = FILENAME_PREFIX + current_time.strftime("%Y%m%d-%H%M")
   print("Filename Base:" + filename_base)
   data_object.set_filename_base(filename_base)
  
   if format == FORMAT_OPTIONS[0]: #HTML
      rc[0] = data_object.asHTML()
      filename = filename_base + ".html"
   elif format == FORMAT_OPTIONS[1]: #JSON
      rc[1] = data_object.asJSON()
      filename = filename_base + ".json"
   elif format == FORMAT_OPTIONS[2]: #CSV
      rc[2] = data_object.asCSV()
      filename = filename_base + ".csv"
   elif format == FORMAT_OPTIONS[3]: #XML
      rc[2] = data_object.asXML()
      filename = filename_base + ".xml"
   else:
      rc[2] = data_object.asCSV() #OTHER
      filename = filename_base + ".txt"

   print("Download Filename:" + str(filename))
   rc[4] = gr.DownloadButton(value=filename, visible=True)

   return rc

############################################################
#
# Send the query to the internal backend
#
############################################################
#def send_query_be(sock, model, prompt, session_id, workspace_id, temperature, topp, max_tokens):
#
#   provider = model_dict[model][0]
#
#   print("Provider      :" + str(provider))
#   print("Model         :" + str(model))
#   print("Max Tokens    :" + str(max_tokens))
#   print("Session ID IN :" + str(session_id))
#   print("Workspace ID  :" + str(workspace_id))
#   print("Temperature   :" + str(temperature))
#   print("TopP          :" + str(topp))
#   print("Prompt Size   :" + str(len(prompt)))
#   print("Prompt        :" + str(prompt))
#
#
#   headers = {
#      'Content-Type': 'application/json',
#   }
#
#   payload = {
#      #"model": "amazon.titan-text-express-v1",
#      "model": "mistral.mixtral-8x7b-instruct-v0:1",
#      "temperature": temperature,
#      "maxTokenCount": 600,
#      "topP": topp,
#      "prompt": prompt
#   }
#
#   json_payload = json.dumps(payload)
#
#
#   resp = requests.post("http://192.168.0.121:5000/generate", headers=headers, data=json_payload)
#
#   resp_json = resp.json()
#   if resp.status_code == 200:
#      print('Request was successful.')
#      print('Response:',resp_json)
#      return resp_json["answer"]
#   else: 
#      print(f'Request failed with status code: {resp.status_code}')
#      print('Response:', resp.text)

   




############################################################
#
# Sends the query to the playground
#
############################################################
#def send_query_ge(sock, model, prompt, session_id, workspace_id, temperature, topp, max_tokens):
#
#  provider = model_dict[model][0]
#
#  print("Provider      :" + str(provider))
#  print("Model         :" + str(model))
#  print("Max Tokens    :" + str(max_tokens))
#  print("Session ID IN :" + str(session_id))
#  print("Workspace ID  :" + str(workspace_id))
#  print("Temperature   :" + str(temperature))
#  print("TopP          :" + str(topp))
#  print("Prompt Size   :" + str(len(prompt)))
#  print("Prompt        :" + str(prompt))
#
#  data = {
#      "action": "run",
#      "modelInterface": "langchain",
#      "data": {
#          "mode": "chain",
#          "text": prompt,
#          "files": [],
#          "modelName": model,
#          "provider": provider,
##          "provider": "bedrock",
#          "sessionId": str(session_id),
##          "workspaceId": WORKSPACE_ID,
#          "workspaceId": workspace_id,
#          "modelKwargs": {
#              "streaming": False,
#              "maxTokens": max_tokens,
#              "temperature": temperature,
#              "topP": topp
#          }
#      }
#  }
#  sock.send(json.dumps(data))
#
#  r1 = None
#  s1 = None
#  while r1 is None:
#    m1 = sock.recv()
#    j1 = json.loads(m1)
#    #print("J1:" + str(j1))
#    a1 = j1.get("action")
#    #print("A1:" + str(a1))
#    if "final_response" == a1:
#      r1 = j1.get("data", {}).get("content")
#      s1 = j1.get("data", {}).get("sessionId")
#      print("Response: " + str(r1))
#    if "error" == a1:
#      print("M1:" + str(m1))
#
#  print("Session ID OUT:" + str(s1))
#
#  return r1.strip()

  
##################################################################################
#
# Enforce Format Helper
#
##################################################################################
def strip_leading_and_trailing(text_block, start_str, end_str):
 
   output = ""
   idx = text_block.find(start_str)
   print("leading idx=" + str(idx)) 
   if idx != -1:
      output = text_block[idx:]
      #print("Output:" + str(output))
   idx = output.rfind(end_str)
   print("trailing idx=" + str(idx)) 
   if idx != -1:
      output = output[:idx + len(end_str)]

   print("Stripped Output:" + str(output))

   if len(output) == 0:
      return None
   else:
      return output

##################################################################################
#
# Enforce Format
#
##################################################################################
def enforce_format(text_block, format):
 
  print("Format=" + format) 
  if format == FORMAT_OPTIONS[0]:
     return strip_leading_and_trailing(text_block, "<tr>", "</tr>")
  elif format == FORMAT_OPTIONS[1]:
     return strip_leading_and_trailing(text_block, "{", "}")
#  elif format == FORMAT_OPTIONS[2]:
#     return strip_leading_and_trailing(text_block, "{", "}")
  elif format == FORMAT_OPTIONS[3]:
     return strip_leading_and_trailing(text_block, "<tc>", "</tc>")
  else:
     return text_block

##################################################################################
#
# Method that changes the default value of Max Tokens based on the model selected
#
##################################################################################
def change_max_token_default(model_name):
   number = model_dict[model_name][1] 
   return gr.Number(value=number, label="Max Tokens", scale=1)


##################################################################################
#
# Change the backend and reformat the GUI
#
##################################################################################
def change_backend(backend, workspace, documentation, upload):
   print("Changing Backend")
   global g_backend

   value = backend
   if value == BACKEND_CHOICES[0]:
      workspace = gr.Textbox(visible=True, interactive=True)
      documentation = gr.Textbox(visible=True, interactive=True, value="")
      upload = gr.UploadButton(visible=False)
      g_backend = Backend.GENERATIVE_ENGINE
   elif value == BACKEND_CHOICES[1]:
      workspace = gr.Textbox(visible=True, interactive=False, value="")
      documentation = gr.Textbox(visible=True, interactive=False, value="")
      upload = gr.UploadButton(visible=True)
      g_backend = Backend.SINGLE_DOC

   return [workspace, documentation, upload]

##################################################################################
#
# Deletes all files with the given suffixes
#
##################################################################################
def delete_files():

   for suffix in [Format.HTML_SUFFIX, Format.JSON_SUFFIX, Format.CSV_SUFFIX, Format.TXT_SUFFIX]:
      
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


##################################################################################
#
# Upload file
#
##################################################################################
def upload_file(filepath, documentation):
   name = Path(filepath).name
#   print("Uploading file:" + filepath)
   print("name:" + name)
#   print("filepath.name:" + name)

   rc = name + ":"
   backend = get_backend()

   try:
      id = backend.upload_file(filepath.name)
   except Exception as e:
      id = str(e)

#   with open(filepath.name, "rb") as file:
#
#      files = {'file': file}
#      resp = requests.post("http://192.168.0.121:5000/upload", files=files)
#
#      if resp.status_code == 200:
#         print('File uploaded successfully.')
#         #print('Response:', resp.json())
#      else:
#         print(f'File upload failed with status code: {resp.status_code}')
#         print('Response:', resp.text)

   return id, name


#########################################################################################################
#
# MAIN
#
#########################################################################################################
if __name__ == "__main__":

   theme = gr.themes.Glass(primary_hue=gr.themes.colors.blue,
                          secondary_hue=gr.themes.colors.cyan)
   #theme = gr.themes.Default()
   #theme = gr.themes.Base()
   #theme = gr.themes.Soft()
   #theme = gr.themes.Monochrome()

   #url = SOCKET_URL

   output_str = ""
   with gr.Blocks(theme=theme) as demo:
      with gr.Tab("Definition"):

         #generated_state = gr.State(False)
         #gr.Label("Generate Tests for")
         with gr.Row() as row1:
            element = gr.Textbox(label="Generate tests for ", value=PROMPT_ELEMENT_TEMPLATE, info=ELEMENT_INFO, scale=1)
            subsystem = gr.Textbox(label="Focus ", value=PROMPT_FOCUS_TEMPLATE, info=FOCUS_INFO, scale=2)

         with gr.Row() as row2:
            #num_tests = gr.Number(value=10, label="Number", info=NUMBER_INFO)
            num_tests = gr.Number(value=10, label="Number")
            format_gen = gr.Dropdown(choices=FORMAT_OPTIONS,
                                     label="Format",
#                                    info=FORMAT_INFO,
                                     value="HTML")

            role = gr.Dropdown(choices=["Tester", "Software Engineer", "Customer", "Analyst"],
#                              info=ROLE_INFO,
                               value="Tester",
                               label="Role")
            type = gr.Dropdown(choices=[ "Sunny Day", "Rainy Day", "Functional", "High Availability", "Resilience", "Acceptance", "End-to-End" ],
#                              info=TEST_INFO,
                               value="Functional",
                               label="Test Type")

      with gr.Tab("Settings"):
         with gr.Row() as row3:
            backend = gr.Dropdown(choices=BACKEND_CHOICES, value=BACKEND_CHOICES[0], label="Backend Engine", scale=1)
         with gr.Row() as row4:
            workspace = gr.Textbox(label="Workspace ID", value=DEFAULT_WORKSPACE, info=WORKSPACE_INFO, scale=1)
            documentation = gr.Textbox(label="Document Title", value=DEFAULT_DOCUMENT_ID, info=DOCUMENT_INFO, scale=1)
         with gr.Row() as row5:
            upload = gr.UploadButton(label="Upload a HLD file", file_count="single", visible=False, scale=1)
            upload.upload(upload_file, inputs=[upload, documentation], outputs=[workspace, documentation])
         with gr.Row() as row6:
            default_max_tokens = 2048
            model = gr.Dropdown(choices=model_dict.keys(), value=list(model_dict.keys())[DEFAULT_MODEL_IDX], label="Model", scale=2)
            temperature = gr.Number(value=0.4, label="Temperature", scale=1)
            topp = gr.Number(value=0.9, label="TopP", scale=1)
            max_tokens = gr.Number(value=4096, label="Max Tokens", scale=1)
            model.select(fn=change_max_token_default, inputs=model, outputs=max_tokens)

         #workspace, documentation, upload = change_backend(backend, workspace, documentation, upload)
         backend.select(fn=change_backend, inputs=[backend, workspace, documentation, upload], outputs=[workspace, documentation, upload])

      gen_btn = gr.Button("Generate")
      html_box = gr.HTML(visible=True) 
      json_box = gr.JSON(visible=False)  
      text_box = gr.Textbox(visible=False, show_label=False)

      with gr.Column(visible=False) as col1:
         with gr.Row() as row4:
            download = "Download"
            download_btn = gr.DownloadButton(label=download)

      #
      # Inline function to change visibility
      #
      def change_output_box(format):
         value = format

         if value == "HTML":
            return  [gr.HTML(visible=True, value=data_object.asHTML()), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=False, value=""),
                     gr.DownloadButton(value=data_object.get_filename())]
         elif value == "XML":
            return  [gr.HTML(visible=False, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=True, value=data_object.asXML()), 
                     gr.DownloadButton(value=data_object.get_filename())]
         elif value == "JSON":
            return  [gr.HTML(visible=False, value=""), gr.JSON(visible=True, value=data_object.asJSON()), gr.Textbox(visible=False, value=""), 
                     gr.DownloadButton(value=data_object.get_filename())]
         elif value == "CSV":
            return  [gr.HTML(visible=False, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=True, value=data_object.asCSV()),
                     gr.DownloadButton(value=data_object.get_filename())]
         else: 
            return  [gr.HTML(visible=False, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=True, value=data_object.asCSV()), 
                     gr.DownloadButton(value=data_object.get_filename())]

      format_gen.select(fn=change_output_box, inputs=format_gen, outputs=[html_box, json_box, text_box, download_btn])
    
      gen_btn.click(fn=generate_tests,
                    inputs=[
                       model, element, subsystem, format_gen, workspace, documentation, temperature, topp, max_tokens, num_tests, role, type,
                    ],
                    #outputs=output_list,
                    outputs=[html_box, json_box, text_box, col1, download_btn],
                    #outputs=[html_box, col1, download_btn],
                    api_name="TCGen")


   #demo.launch(share=True, server_name="0.0.0.0")
   #demo.launch(server_name="0.0.0.0", auth=(UI_USER, UI_PASSWORD))
   demo.launch(server_name="0.0.0.0")
