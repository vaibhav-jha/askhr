from langchain_ibm import WatsonxLLM
from os import getenv

parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 2000,
    "min_new_tokens": 10,
    "temperature": 0.01,
}

llama = WatsonxLLM(
    model_id="meta-llama/llama-3-70b-instruct",
    url="https://us-south.ml.cloud.ibm.com",
    project_id=getenv("WATSONX_PROJECT_ID"),
    params=parameters,
)
