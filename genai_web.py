#!/usr/bin/python3

import websocket
import json
from contextlib import closing
from dataclasses import dataclass
from uuid import uuid4
import re
import time
import datetime

#from langchain import PromptTemplate
from langchain_core.prompts import PromptTemplate

import gradio as gr
import os

WORKSPACE_ID = os.environ['WORKSPACE_ID']
SOCKET_URL = "wss://datw9crxl8.execute-api.us-east-1.amazonaws.com/socket/"
API_TOKEN = os.environ['API_KEY']

TESTS_PER_CALL = 10

FORMAT_OPTIONS = ["HTML", "CSV", "Excel", "JSON", "Text"]

#g_tests_generated = False

#MODEL = "mistral.mixtral-8x7b-instruct-v0:1"
#MODEL = "ai21.j2-ultra-v1"
#MODEL = "anthropic.claude-v2:1"
#MODEL = "amazon.titan-tg1-large"
#MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"
#MODEL = "anthropic.claude-3-haiku-20240307-v1:0"
#MODEL = "meta.llama2-70b-chat-v1"
#MODEL = "amazon.titan-tg1-large"


model_dict = {"mistral.mixtral-8x7b-instruct-v0:1" : 4096,
              "mistral.mistral-large-2402-v1:0" : 4096,
#               "mistral.mistral-7b-instruct-v0:2" : 4096,
              "meta.llama2-70b-chat-v1" : 2048,
              "meta.llama3-70b-instruct-v1:0" : 2048,
              "meta.llama3-8b-instruct-v1:0" : 2048,
              "ai21.j2-ultra-v1" : 4096,
#              "anthropic.claude-3-sonnet-20240229-v1:0" : 4096,
#              "anthropic.claude-3-haiku-20240307-v1:0" : 4096,
              "amazon.titan-tg1-large" : 4096 }
            


HEADING_NO = "No."
HEADING_NAME = "Test Name"
HEADING_DESC = "Description"
HEADING_ID = "External Test ID"
HEADING_PRE = "Pre-Conditions"
HEADING_STEPS = "Test Steps"
HEADING_RESULTS = "Expected Results"


def validate_element(input):
   rc = False
   el_len = len(input)
   if el_len < 32 and el_len > 0:
      rc = True

   return rc

def validate_service(input):
   rc = False
   if len(input) < 32: 
      rc = True

   return rc
     

     

############################################################
#
# Generates the tests
#
############################################################
def generate_tests(model, element, service, format, temperature, topp, max_tokens, num_tests,
                   role, type):

  session_id = uuid4()

  service = str(service)
  element = str(element)
  print("Element:" + element)
  print("Service(len):" + service + ":" + str(len(service)))
  print("Format:" + format)

  #rc = ["", "{}", "", gr.Button("Download", visible=True) ]
  rc = ["", "{}", "", gr.Column(visible=True), None ]

  if not validate_element(element):
    return "Invalid Element input"

  if not validate_service(service):
    return "Invalid Service input"

  if num_tests >= TESTS_PER_CALL:
    num_tests_to_ask_for = TESTS_PER_CALL
  else:
    num_tests_to_ask_for = num_tests

  secondary_target = ""

  if 0 < len(service):
     secondary_target = f" including the for the service {service}."

  formatting_prefix = ""
  formatting_suffix = ""
  format_separator = ""

  formatting = ""
  if format == "HTML":
    formatting = f"""Each test cases must be presented as row which can be added to a HTML table. Each row will be prefixed with <tr> & suffixed with </tr>. This table must easy to read. Do not include the tag <table>, do not generate the header row or use the <th> tags.
    Here is an example of the desired output format <tr><td>{HEADING_NO}</td><td>{HEADING_NAME}</td><td>{HEADING_DESC}</td><td>{HEADING_ID}</td><td>{HEADING_PRE}</td><td>{HEADING_STEPS}</td><td>{HEADING_RESULTS}</td></tr>"""

    formatting_prefix = f"<table><tr><th>{HEADING_NO}</th><th>{HEADING_NAME}</th><th>{HEADING_DESC}</th><th>{HEADING_ID}</th><th>{HEADING_PRE}</th><th>{HEADING_STEPS}</th><th>{HEADING_RESULTS}</th></tr>"
    formatting_suffix = "</table>"

    display_idx = 0

  elif format == "JSON":
    formatting = f"""The output must use strict JSON format. Each Test case will be a JSON object. Each of the fields will be property in the JSON object. Each row must be separated with a ',' character. Do not generate the enclosing "[" or "]" of the top level list.
    Here is an example of the desired output format: 
      {{ "{HEADING_NO}" : "Value 1", "{HEADING_NAME}": "Value 1", "{HEADING_DESC}": "Value 1", "{HEADING_ID}": "Value 1", "{HEADING_PRE}": "Value 1", "{HEADING_STEPS}": "Value 1", "{HEADING_RESULTS}": "Value 1" }}, {{ "{HEADING_NO}" : "Value 2", "{HEADING_NAME}": "Value 2", "{HEADING_DESC}": "Value 2", "{HEADING_ID}": "Value 2", "{HEADING_PRE}": "Value 2", "{HEADING_STEPS}": "Value 2", "{HEADING_RESULTS}": "Value 2" }},"""

    formatting_prefix = f"["
    formatting_suffix = "]"
    format_separator = ","

    display_idx = 1
  elif format == "CSV":
    formatting = "The resultant test cases must be presented in the format of a CSV table"
    display_idx = 2
  elif format == "Excel":
    formatting = "The resultant test cases must be presented in the format of a that can be easily pasted into a spreadsheet such as Excel"
    display_idx = 2
  elif format == "Text":
    formatting = "The resultant test cases must be presented in the format of a table in plain text"
    display_idx = 2

  #prompt = f"""You are a {role}. Generate {num_tests_to_ask_for} unique test cases for {element} including the for the service {service}. 
  prompt = f"""You are a {role}. Generate {num_tests_to_ask_for} unique test cases for {element}{secondary_target}. 

   The test cases must be {type} test cases.

   {formatting} 
   Do not generate any superfluous output that is not part of test case.

   The test cases must contain the fields in the following order: {HEADING_NO}, {HEADING_NAME}, {HEADING_DESC}, {HEADING_ID}, {HEADING_PRE}, {HEADING_STEPS}, and {HEADING_RESULTS} as specified by the Test Case Definition.

   """

#   The test cases must conform to the definition specified in your knowledge base.
#   The test cases must conform to the definition specified.
#   The test cases must conform to the definition of a Test Case in your understanding.
#   The test cases must conform to your understanding of the definition of a test case.
#   The test cases must conform to the definition of a test case provided. 
#   The test cases must conform to the definition specified in 'Test Definition.txt' 
#   The test cases must include the following elements, each corresponding to a heading: {HEADING_NO}, {HEADING_NAME}, {HEADING_DESC}, {HEADING_ID}, {HEADING_PRE}, {HEADING_STEPS}, and {HEADING_RESULTS}. 
#
#   {HEADING_NO}' is an abbreviation for number. This is a unique integer for each test case, starting from 1 and incrementing by 1 for each test case. 
#   {HEADING_NAME} is a useful short description of the test. 
#   {HEADING_DESC} is a summary of the test and should end in -{element}. 
#   {HEADING_ID} is an alpha-numeric ID, unique for each case and derived from {element}. 
#   {HEADING_PRE} describes the preconditions needed for the tests to be executed. 
#   {HEADING_STEPS} is a series of at least 3 steps that clearly describes how to execute the test case. Each step must be numbered. 
#   {HEADING_RESULTS} describes the expected outcome for each step itemised in, each outcome must be numbered {HEADING_STEPS}.

  #output = ""
  output_array = []
  tests_remaining = num_tests
  while tests_remaining > 0:
    query_output = send_query(model, prompt, session_id, temperature, topp, max_tokens)
    stripped = enforce_format(query_output, format)
  
    if stripped:
       output_array.append(stripped)

    tests_remaining -= num_tests_to_ask_for
    if tests_remaining >= TESTS_PER_CALL:
      num_tests_to_ask_for = TESTS_PER_CALL
    else:
      num_tests_to_ask_for = tests_remaining
    prompt = f"Generate another {num_tests_to_ask_for} unique test cases using the same requirements in the same output format. Ensure the numbering is continuous"

  output = format_separator.join(output_array)

  rc[display_idx] = f"{formatting_prefix}{output}{formatting_suffix}"
  print("TOTAL OUT:" + str(rc[display_idx]))



  current_time = datetime.datetime.now()
  filename = "gentests-" + current_time.strftime("%Y%m%d-%H%M") + ".tst"


  #filename = "genai.tst"
  download_to_file(rc[0], rc[1], rc[2], format, filename)
  rc[4] = gr.DownloadButton(value=filename)

#       #download_btn.click(fn=download_to_file,
#                          inputs=[html_box, json_box, text_box, format_file, format_gen],
#                          outputs=downloaded_md)

  return rc

############################################################
#
# Sends the query to the playground
#
############################################################
def send_query(model, prompt, session_id, temperature, topp, max_tokens):

  print("Model         :" + str(model))
  print("Max Tokens    :" + str(max_tokens))
  print("Session ID IN :" + str(session_id))
  print("Temperature   :" + str(temperature))
  print("TopP          :" + str(topp))
  print("Prompt        :" + str(prompt))

  data = {
      "action": "run",
      "modelInterface": "langchain",
      "data": {
          "mode": "chain",
          "text": prompt,
          "files": [],
          "modelName": model,
          "provider": "bedrock",
          "sessionId": str(session_id),
          "workspaceId": WORKSPACE_ID,
          "modelKwargs": {
              "streaming": False,
              "maxTokens": max_tokens,
              "temperature": temperature,
              "topP": topp
          }
      }
  }
  ws.send(json.dumps(data))

  r1 = None
  s1 = None
  while r1 is None:
    m1 = ws.recv()
    j1 = json.loads(m1)
    #print("J1:" + str(j1))
    a1 = j1.get("action")
    #print("A1:" + str(a1))
    if "final_response" == a1:
      r1 = j1.get("data", {}).get("content")
      s1 = j1.get("data", {}).get("sessionId")
      print("Response: " + str(r1))
    if "error" == a1:
      print("M1:" + str(m1))

  print("Session ID OUT:" + str(s1))

  return r1.strip()

  
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
  if format == "HTML":
     return strip_leading_and_trailing(text_block, "<tr>", "</tr>")
  elif format == "JSON":
     return strip_leading_and_trailing(text_block, "{", "}")
  else:
     return text_block

##################################################################################
#
# Method that changes the default value of Max Tokens based on the model selected
#
##################################################################################
def change_max_token_default(model_name):
   number = model_dict[model_name] 
   return gr.Number(value=number, label="Max Tokens", scale=1)


##################################################################################
#
# Downloads the output to a file
#
##################################################################################
#def download_to_file(html, json_data, text, format_in, format_out):
def download_to_file(html, json_data, text, format_in, filename):

   #file_path = "genai.tst"
   with open(filename, "w") as output_file:
      if format_in == "HTML":
         output_file.write(str(html))
      if format_in == "JSON":
         json.dump(json_data, output_file, indent=3)
      else:
         output_file.write(str(text))
   

   #text_str = str(format_in) + " tests written to file, " + file_path + " as " + str(format_out)
   text_str = str(format_in) + " tests written to file, " + filename
   print(text_str)
   #return gr.Markdown(visible=True, value=text_str)
   #return file_path
   time.sleep(1)
   return


#########################################################################################################
#
# MAIN
#
#########################################################################################################
if __name__ == "__main__":

  global tests_generated

  theme = gr.themes.Glass(primary_hue=gr.themes.colors.blue,
                          secondary_hue=gr.themes.colors.cyan)
  #theme = gr.themes.Default()
  #theme = gr.themes.Base()
  #theme = gr.themes.Soft()
  #theme = gr.themes.Monochrome()

  prompt_element_template = """element"""
  #prompt_element_template = """HSS"""
  prompt_subsystem_template = ""
  #prompt_subsystem_template = "Backup And Restore"

  url = SOCKET_URL
  ws = websocket.create_connection(url, header={"x-api-key": API_TOKEN})

  # Session ID
  #session_id = uuid4()

  output_str = ""
  with gr.Blocks(theme=theme) as demo:

    generated_state = gr.State(False)
    #gr.Label("Generate Tests for")
    with gr.Row() as row1:
       element = gr.Textbox(label="Generate tests for ", value=prompt_element_template, scale=2)
       subsystem = gr.Textbox(label="Service ", value=prompt_subsystem_template, scale=1)

    with gr.Row() as row2:
       num_tests = gr.Number(value=10, label="Number")
       format_gen = gr.Dropdown(choices=FORMAT_OPTIONS,
                           label="Format",
                           value="HTML")

       role = gr.Dropdown(
          choices=["Tester", "Software Engineer", "Customer", "Analyst"],
          value="Tester",
          label="Role")
       type = gr.Dropdown(choices=[
          "Sunny Day", "Rainy Day", "Functional", "High Availability",
          "Resilience", "Acceptance"
       ],
          value="Functional",
          label="Test Type")

    with gr.Row() as row3:
       default_max_tokens = 2048
       model = gr.Dropdown(choices=model_dict.keys(), value=list(model_dict.keys())[1], label="Model", scale=2)
       temperature = gr.Number(value=0.4, label="Temperature", scale=1)
       topp = gr.Number(value=0.9, label="TopP", scale=1)
       max_tokens = gr.Number(value=4096, label="Max Tokens", scale=1)
       model.select(fn=change_max_token_default, inputs=model, outputs=max_tokens)



    gen_btn = gr.Button("Generate")
    html_box = gr.HTML(visible=True) 
    json_box = gr.JSON(visible=False)  
    text_box = gr.Textbox(visible=False, show_label=False)

    with gr.Column(visible=False) as col1:
       with gr.Row() as row4:
          #format_file = gr.Dropdown(choices=FORMAT_OPTIONS, label="File Format", value="JSON")
          #download_btn = gr.Button("Download")
          download_btn = gr.DownloadButton("Download")
          #download_btn = gr.DownloadButton("Download", value=download_to_file, inputs=[html_box, json_box, text_box, format_file, format_gen])
       #downloaded_md = gr.Markdown("""LLM Parameters""", visible=False)
       #download_btn.click(fn=download_to_file,
       #                   inputs=[html_box, json_box, text_box, format_file, format_gen],
       #                   outputs=downloaded_md)


    #output_box = output_list[0]

    #
    # Inline function to change visibility
    #
    def change_output_box(format):
       value = format

       #dd = gr.Dropdown(value=format)
       col = gr.Column(visible=False)
       if value == "HTML":
          #return  [gr.HTML(visible=True, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=False, value=""), dd, col]
          return  [gr.HTML(visible=True, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=False, value=""), col]
       elif value == "JSON":
          #return  [gr.HTML(visible=False, value=""), gr.JSON(visible=True, value="{}"), gr.Textbox(visible=False, value=""), dd, col]
          return  [gr.HTML(visible=False, value=""), gr.JSON(visible=True, value="{}"), gr.Textbox(visible=False, value=""), col]
       else: 
          #return  [gr.HTML(visible=False, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=True, value=""), dd, col]
          return  [gr.HTML(visible=False, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=True, value=""), col]

    #format_gen.select(fn=change_output_box, inputs=format_gen, outputs=[html_box, json_box, text_box, format_file, col1])
    format_gen.select(fn=change_output_box, inputs=format_gen, outputs=[html_box, json_box, text_box, col1])
    
    gen_btn.click(fn=generate_tests,
                  inputs=[
                      model, element, subsystem, format_gen, temperature, topp, max_tokens, num_tests,
                      role, type,
                  ],
                  #outputs=output_list,
                  outputs=[html_box, json_box, text_box, col1, download_btn],
                  api_name="TCGen")


  #demo.launch(share=True, server_name="0.0.0.0")
  demo.launch(server_name="0.0.0.0")
  ws.close()
