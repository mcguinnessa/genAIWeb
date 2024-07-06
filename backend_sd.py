
import requests
import json
from backend import Backend

class BackendSingleDoc(Backend):
   

   def __init__(self):
      """Single Document"""
      print("Backend is Single Doc")

############################################################
#
# Send the query to the internal backend
#
############################################################
   def send_query_impl(self, model, provider, prompt, session_id, workspace_id, temperature, topp, max_tokens):

      headers = {
         'Content-Type': 'application/json',
      }

      payload = {
         #"model": "amazon.titan-text-express-v1",
         "model": "mistral.mixtral-8x7b-instruct-v0:1",
         "temperature": temperature,
         "maxTokenCount": 600,
         "topP": topp,
         "prompt": prompt,
         "workspace": workspace_id
      }

      json_payload = json.dumps(payload)

      resp = requests.post("http://192.168.0.121:5000/generate", headers=headers, data=json_payload)

      resp_json = resp.json()
      if resp.status_code == 200:
         print('Request was successful.')
         print('Response:',resp_json)
         return resp_json["answer"]
      else:
         print(f'Request failed with status code: {resp.status_code}')
         print('Response:', resp.text)


############################################################
#
# Upload File
#
############################################################
   def upload_file(self, filename):

      with open(filename, "rb") as file:

         files = {'file': file}
         resp = requests.post("http://192.168.0.121:5000/upload", files=files)

         if resp.status_code == 200:
            print('File uploaded successfully.')
            #print('Response:', resp.json())

            resp_json = resp.json()
            id = resp_json["id"]
            print("WS ID:" + str(id))

            #return "Success"
            return id
         else:
            print(f'File upload failed with status code: {resp.status_code}')
            print('Response:', resp.text)
            raise Exception(resp.text)
            #return resp.text



