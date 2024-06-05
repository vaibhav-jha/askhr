from langchain_ibm import WatsonxLLM

parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 2000,
    "min_new_tokens": 10,
    "temperature": 0.01,
}

llama = WatsonxLLM(
    model_id="meta-llama/llama-3-70b-instruct",
    url="https://us-south.ml.cloud.ibm.com",
    project_id="8aa3f2a9-238f-49d1-9a4f-5320ca747f2e",
    params=parameters,
)
