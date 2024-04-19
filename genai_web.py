#!/usr/bin/python3

import websocket
import json
from contextlib import closing
from dataclasses import dataclass
from uuid import uuid4
import re

#from langchain import PromptTemplate
from langchain_core.prompts import PromptTemplate

import gradio as gr
import os

WORKSPACE_ID = os.environ['WORKSPACE_ID']
SOCKET_URL = "wss://datw9crxl8.execute-api.us-east-1.amazonaws.com/socket/"
API_TOKEN = os.environ['API_KEY']

TESTS_PER_CALL = 10

#MODEL = "mistral.mixtral-8x7b-instruct-v0:1"
#MODEL = "ai21.j2-ultra-v1"
#MODEL = "anthropic.claude-v2:1"
#MODEL = "amazon.titan-tg1-large"
#MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"
#MODEL = "anthropic.claude-3-haiku-20240307-v1:0"
#MODEL = "meta.llama2-70b-chat-v1"
#MODEL = "amazon.titan-tg1-large"


model_dict = {"mistral.mixtral-8x7b-instruct-v0:1" : 4096,
              "meta.llama2-70b-chat-v1" : 2048,
              "ai21.j2-ultra-v1" : 4096,
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
   if len(input) < 32:
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

  rc = ["", "{}", ""]

  if not validate_element(element):
    return "Invalid Element input"

  if not validate_service(service):
    return "Invalid Service input"
    

  if num_tests >= TESTS_PER_CALL:
    num_tests_to_ask_for = TESTS_PER_CALL
  else:
    num_tests_to_ask_for = num_tests

#  pattern = re.compile("generate test cases for (.*) element including (.*)")
#  m = re.search(pattern, input)
#  if m:
#    element = m.group(1)
#    service = m.group(2)

  #f"generate test cases for {element} including {service}"
  formatting_prefix = ""
  formatting_suffix = ""

  if format == "HTML":
    format = "Each test cases must be presented as row which can be added to a HTML table. Each row will be prefixed with <tr> & suffixed with </tr>; each of the headings will be a column, prefixed with <th> & suffixed with </th>. This table must easy to read. Do not include the tag <table>"
    formatting_prefix = "<table>"
    formatting_suffix = "</table>"

    idx = 0

  elif format == "JSON":
    format = "The resultant test cases must be presented in JSON format. Each test case wil be a JSON object in the table, and each of the headings will be a key value pair."
    idx = 1
  elif format == "CSV":
    format = "The resultant test cases must be presented in the format of a CSV table"
    idx = 2
  elif format == "Excel":
    format = "The resultant test cases must be presented in the format of a that can be easily pasted into a spreadsheet such as Excel"
    idx = 2
  elif format == "Text":
    format = "The resultant test cases must be presented in the format of a table in plain text"
    idx = 2

  prompt = f"""You are a {role}. Generate {num_tests_to_ask_for} unique test cases for {element} including the for the service service {service}. 

   The test cases must be {type} test cases.

   {format}
   
   The test cases must include the following elements, each corresponding to a heading: {HEADING_NO}, {HEADING_NAME}, {HEADING_DESC}, {HEADING_ID}, {HEADING_PRE}, {HEADING_STEPS}, and {HEADING_RESULTS}. 

   {HEADING_NO}' is an abbreviation for number. This is a unique integer for each test case, starting from 1 and incrementing by 1 for each test case. 
   {HEADING_NAME} is a useful short description of the test. 
   {HEADING_DESC} is a summary of the test and should end in -{element}. 
   {HEADING_ID} is an alpha-numeric ID, unique for each case and derived from {element}. 
   {HEADING_PRE} describes the preconditions needed for the tests to be executed. 
   {HEADING_STEPS} is a series of at least 3 steps that clearly describes how to execute the test case. Each step must be numbered. 
   {HEADING_RESULTS} describes the expected outcome for each step itemised in, each outcome must be numbered {HEADING_STEPS}.

   """

  output = ""
  tests_remaining = num_tests
  while tests_remaining > 0:
    query_output = send_query(model, prompt, session_id, temperature, topp, max_tokens)
    print("QOUTPUT:" + query_output)
    #output += query_output
    output =  output + query_output

    tests_remaining -= num_tests_to_ask_for
    if tests_remaining >= TESTS_PER_CALL:
      num_tests_to_ask_for = TESTS_PER_CALL
    else:
      num_tests_to_ask_for = tests_remaining
    prompt = f"Generate another {num_tests_to_ask_for} unique test cases using the same requirements in the same output format. All of the same fields must be included. The fields {HEADING_NO} and {HEADING_ID} should continue incrementing"

  rc[idx] = f"{formatting_prefix}{output}{formatting_suffix}"
  print("OUT:" + str(rc[idx]))
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
          #"modelName": MODEL,
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
    print("J1:" + str(j1))
    a1 = j1.get("action")
    print("A1:" + str(a1))
    if "final_response" == a1:
      r1 = j1.get("data", {}).get("content")
      s1 = j1.get("data", {}).get("sessionId")
      print("Response: " + str(r1))
    if "error" == a1:
      print("M1:" + str(m1))

  print("Session ID OUT:" + str(s1))

  return r1


##################################################################################
#
# Method that changes the default value of Max Tokens based on the model selected
#
##################################################################################
def change_max_token_default(model_name):
   #print("Model:" + str(model_name))
   number = model_dict[model_name] 
   #print("Number:" + str(number))
   return gr.Number(value=number, label="Max Tokens", scale=1)

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

  #prompt_template = """generate test cases for #network element including #service."""
  prompt_element_template = """element"""
  prompt_subsystem_template = """service"""

  url = SOCKET_URL
  ws = websocket.create_connection(url, header={"x-api-key": API_TOKEN})

  # Session ID
  session_id = uuid4()

  output_str = ""
  with gr.Blocks(theme=theme) as demo:
    #gr.Label("Generate Tests for")
    with gr.Row() as row1:
       element = gr.Textbox(label="Generate tests for ", value=prompt_element_template, scale=2)
       subsystem = gr.Textbox(label="Service ", value=prompt_subsystem_template, scale=1)

    with gr.Row() as row2:
       default_max_tokens = 2048
       model = gr.Dropdown(choices=model_dict.keys(), value=list(model_dict.keys())[0], label="Model", scale=2)
       temperature = gr.Number(value=0.4, label="Temperature", scale=1)
       topp = gr.Number(value=0.9, label="TopP", scale=1)
       max_tokens = gr.Number(value=4096, label="Max Tokens", scale=1)
       model.select(fn=change_max_token_default, inputs=model, outputs=max_tokens)

    with gr.Row() as row3:
       num_tests = gr.Number(value=10, label="Number")
       format = gr.Dropdown(choices=["HTML", "CSV", "Excel", "JSON", "Text"],
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

    gen_btn = gr.Button("Generate")
    output_list = [gr.HTML(visible=True), gr.JSON(visible=False), gr.Textbox(visible=False, show_label=False)]
    output_box = output_list[0]

    def change_output_box(format):
       value = format
       if value == "HTML":
          return  [gr.HTML(visible=True, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=False, value="")]
       elif value == "JSON":
          return  [gr.HTML(visible=False, value=""), gr.JSON(visible=True, value="{}"), gr.Textbox(visible=False, value="")]
       else: 
          return  [gr.HTML(visible=False, value=""), gr.JSON(visible=False, value="{}"), gr.Textbox(visible=True, value="")]

    format.select(fn=change_output_box, inputs=format, outputs=output_list)
    
    gen_btn.click(fn=generate_tests,
                  inputs=[
                      model, element, subsystem, format, temperature, topp, max_tokens, num_tests,
                      role, type
                  ],
                  outputs=output_list,
                  api_name="TCGen")

  #demo.launch(share=True, server_name="0.0.0.0")
  demo.launch(server_name="0.0.0.0")
  ws.close()
