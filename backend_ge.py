

import websocket
import json
from backend import Backend


class BackendGenerativeEngine(Backend):

#   SOCKET_URL = "wss://datw9crxl8.execute-api.us-east-1.amazonaws.com/socket/"

   def __init__(self, url, api_token):
      """Generative Engine"""
      print("Backend is Generative Engine")
      self.ws = websocket.create_connection(url, header={"x-api-key": api_token})

   def __del__(self):
      # body of destructor
      self.ws.close()


   ############################################################
   #
   # Sends the query to the playground
   #
   ############################################################
   def send_query_impl(self, model, provider, prompt, session_id, workspace_id, document_id, temperature, topp, max_tokens):

      data = {
          "action": "run",
          "modelInterface": "langchain",
          "data": {
              "mode": "chain",
              "text": prompt,
              "files": [],
              "modelName": model,
              "provider": provider,
#              "provider": "bedrock",
              "sessionId": str(session_id),
#              "workspaceId": WORKSPACE_ID,
              "workspaceId": workspace_id,
              "modelKwargs": {
                  "streaming": False,
                  "maxTokens": max_tokens,
                  "temperature": temperature,
                  "topP": topp
              }
          }
      }
      self.ws.send(json.dumps(data))

      r1 = None
      s1 = None
      while r1 is None:
         m1 = self.ws.recv()
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


