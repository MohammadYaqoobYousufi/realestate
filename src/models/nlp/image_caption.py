# Step 1: Setting up the environment and importing libraries

import requests
import base64
import os
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import Model, ModelInference
from ibm_watsonx_ai.foundation_models.schema import TextChatParameters
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames

from PIL import Image

# Step 2: Initializing the model
# Read credentials from environment variables (do NOT commit real keys)
IBM_URL = os.getenv("IBM_WATSONX_URL")
IBM_API_KEY = os.getenv("IBM_WATSONX_API_KEY")
if not IBM_URL or not IBM_API_KEY:
    raise RuntimeError("Set IBM_WATSONX_URL and IBM_WATSONX_API_KEY in the environment to use this module.")
Credentials = Credentials(
    url=IBM_URL,
    api_key=IBM_API_KEY
)
client = APIClient(Credentials)

# Prepare text images by encoding them for LLM processing 
encoded_images = []
# `image_url` should be set by the caller. Use an empty list if not provided to avoid NameError.
image_url = globals().get("image_url", [])

for url in image_url:
  encoded_images.append(base64.b64encode(requests.get(url).content).decode("utf-8"))

# Initialize Llama model with appropriate parameters
model_id = "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
project_id = "<your_project_id_here>"
params =TextChatParameters()

model = ModelInference(
  model_id=model_id,
  Credentials=Credentials,
  project_id=project_id,
  params=params
)
# Step 3 Preparing an image for processing
# Convert images into AI-readable format Numerical ot text-based representations
# Crete two functions for image conversion

def prepare_image(image_path):
  """Convert an image to base64 encoding for model"""
  with open(image_path, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
  return encoded_image

# alternative, for an image from a URL
def prepare_image_from_url(image_url):
  """download and encode an image from a URL"""
  response = requests.get(image_url)
  encoded_image = base64.b64encode(response.content).decode("utf-8")
  return encoded_image

# Step 4: Creating the multimodal query function
def query_multimodal_model(encoded_image, user_question, system_prompt=""):
  """Send a multiSend query to the model and get response 
  Docstring for query_multimodal_model
  :param encoded_image: Description
  :param user_question: Description
  :param system_prompt: Description
  """


def generate_model_response(encoded_image, prompt,
                            user_query,
                            assistant_prompt="You are helpful assistant.Answer the following user query in 1 or 2 sentences:"):
  
  # Create the messages object
  messages = [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": assistant_prompt + user_query
        },
        {
          "type": "image_url",
          "image_url": {
          "url": "data:image/jpeg;base64," + encoded_image,
          }
        }]
    }]
  
  # send the request to the model
  response = model.chat(messages=messages)
  # return the response from the model
  return response["choices"][0]["messages"]["content"]

# Step: 5 Using the multimodal QA function
image = prepare_image("sample_image.jpg")

# Craft a question about the image
question = "What can you see in the photo? Is there anything unusual?"

# further shape how the model approaches the question
system_prompt = """You are an expert assistant that helps analyze images.
Please provide detailed observations and answer the user's question 
based on what you see in the image."""

# call the function with components, process the input, return
response = query_multimodal_model(image, question, system_prompt)
print("Model response:", response)

user_query = "Describe the photo"

for i in range(len(encoded_images)):
  Image = encoded_images[i]
  response = generate_model_response(Image, user_query)
  # Print the response with a formatted description
  print(f"Description for image {i + 1}: {response}")
  