
from abc import ABC, abstractmethod

class Backend(ABC):
   def __init__(self):
      """Backend"""

############################################################
#
# Sends the query to the playground
#
############################################################
   def send_query(self, model, provider, prompt, session_id, workspace_id, document_id, temperature, topp, max_tokens):

      #provider = model_dict[model][0]

      print("Provider      :" + str(provider))
      print("Model         :" + str(model))
      print("Max Tokens    :" + str(max_tokens))
      print("Session ID IN :" + str(session_id))
      print("Workspace ID  :" + str(workspace_id))
      print("Document ID   :" + str(document_id))
      print("Temperature   :" + str(temperature))
      print("TopP          :" + str(topp))
      print("Prompt Size   :" + str(len(prompt)))
      print("Prompt        :" + str(prompt))

      return self.send_query_impl(model, provider, prompt, session_id, workspace_id, document_id, temperature, topp, max_tokens)

   @abstractmethod
   def send_query_impl(self, model, provider, prompt, session_id, workspace_id, document_id, temperature, topp, max_tokens):
      pass

#   @abstractmethod
   def upload_file(self, filename):
      pass

   def get_existing_workspaces(self):
      pass


