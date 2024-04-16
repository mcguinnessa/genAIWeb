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

MODEL = "mistral.mixtral-8x7b-instruct-v0:1"
#MODEL = "ai21.j2-ultra-v1"
#MODEL = "anthropic.claude-v2:1"
#MODEL = "amazon.titan-tg1-large"
#MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"
#MODEL = "anthropic.claude-3-haiku-20240307-v1:0"
#MODEL = "meta.llama2-70b-chat-v1"
#MODEL = "amazon.titan-tg1-large"


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
def generate_tests(element, service, format, temperature, topp, max_tokens, num_tests,
                   role, type):

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
    #format = "The generated test cases must be presented as a HTML table using the <table> tag. Each test case must be a row in the table, delimited with the <tr></tr> tag; each of the headings will be a column, delimited with the <th></th> tag. You cannot use the | character. This table must be asthetically pleasing and easy to read"
    format = "Each genrated test cases must be presented as row which will be added to a HTML table. Each row will be prefixed with the <tr> tag and suffixed with the </tr> tag; each of the headings will be a column, prefixed with the <th> tag and suffixed with the </th> tag. This table must be asthetically pleasing and easy to read. Do not use the tag <table>."
    formatting_prefix = "<table>"
    formatting_suffix = "</table>"
  elif format == "JSON":
    format = "The resultant test cases must be presented in JSON format. Each test case wil be a JSON object in the table, and each of the headings will be a key value pair."
  elif format == "CSV":
    format = "The resultant test cases must be presented in the format of a CSV table"
  elif format == "Excel":
    format = "The resultant test cases must be presented in the format of a that can be easily pasted into a spreadsheet such as Excel"
  elif format == "Text":
    format = "The resultant test cases must be presented in the format of a table in plain text"

  prompt = f"""You are a {role}. Generate unique test cases for {element} including the service {service} based on your knowledge. 

   There should be {num_tests_to_ask_for} test cases.

   The test cases must include {type} test cases.

   {format}
   
   The test cases must have the following column headings: {HEADING_NO}, {HEADING_NAME}, {HEADING_DESC}, {HEADING_ID}, {HEADING_PRE}, {HEADING_STEPS}, and {HEADING_RESULTS}. 

   '{HEADING_NO}' is shorthand for number. This should be a unique integer for each test case, starting from 1 and incrementing by for each test case. 
   
   The {HEADING_NAME} should be a useful short description of the test. The {HEADING_DESC} should be summary of the test and should end in -{element}. The {HEADING_ID} must be an alpha-numeric key, unique for each test. The {HEADING_PRE} field must describe and preconditions needed before the tests can be executed. The {HEADING_STEPS} field must describe clearly how to execute the test and each step shall be numbered. The {HEADING_RESULTS} field must correspond to the test steps, with an expected outcome for each step enumberated step. 

   Do not use the , character in any of the output.
   
   """
  

  tests_remaining = num_tests
  output = ""
  while tests_remaining > 0:
    query_output = send_query(prompt, session_id, temperature, topp, max_tokens)
    print("QOUTPUT:" + query_output)
    output += query_output

    tests_remaining -= num_tests_to_ask_for
    if tests_remaining >= TESTS_PER_CALL:
      num_tests_to_ask_for = TESTS_PER_CALL
    else:
      num_tests_to_ask_for = tests_remaining
    prompt = f"Generate {num_tests_to_ask_for} more unique test cases using the same requirements. All of the same fields must be included. The fields {HEADING_NO} and {HEADING_ID} should continue incrementing from the last logical integer"

  return f"{formatting_prefix}{output}{formatting_suffix}"

############################################################
#
# Sends the query to the playground
#
############################################################
def send_query(prompt, session_id, temperature, topp, max_tokens):

  print("Session ID IN :" + str(session_id))
  print("Temperature :" + str(temperature))
  print("TopP        :" + str(topp))
  print("Prompt      :" + str(prompt))

  data = {
      "action": "run",
      "modelInterface": "langchain",
      "data": {
          "mode": "chain",
          "text": prompt,
          "files": [],
          "modelName": MODEL,
          "provider": "bedrock",
          "sessionId": str(session_id),
#          "workspaceId": WORKSPACE_ID,
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
  prompt_element_template = """#element."""
  prompt_subsystem_template = """#service."""

  url = SOCKET_URL
  ws = websocket.create_connection(url, header={"x-api-key": API_TOKEN})

  # Session ID
  session_id = uuid4()

  with gr.Blocks(theme=theme) as demo:
    #gr.Label("Generate Tests for")
    with gr.Row() as row1:
       element = gr.Textbox(label="Generate tests for ", value=prompt_element_template, scale=2)
       subsystem = gr.Textbox(label="Service ", value=prompt_subsystem_template, scale=1)

    with gr.Row() as row2:
      format = gr.Dropdown(choices=["HTML", "CSV", "Excel", "JSON", "Text"],
                           label="Format",
                           value="HTML")
      temperature = gr.Number(value=0.4, label="Temperature")
      topp = gr.Number(value=0.9, label="TopP")
      max_tokens = gr.Number(value=4096, label="Max Tokens")
    with gr.Row() as row3:
      num_tests = gr.Number(value=10, label="Number")

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
    html_block = gr.HTML("""
        <div style='height: 800px; width: 100px; background-color: white;'></div>
        """)

    gen_btn.click(fn=generate_tests,
                  inputs=[
                      element, subsystem, format, temperature, topp, max_tokens, num_tests,
                      role, type
                  ],
                  outputs=html_block,
                  api_name="TCGen")

#    iface = gr.Interface(
#      fn=send_query,
#      inputs=["text"],
#      outputs="text",
#      title="Test Generator",
#      description="Describe the test cases"
#    )

  demo.launch(share=True)
  ws.close()
