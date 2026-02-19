import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_explanation(prediction, shap_values, retrieved_docs):

    prompt = f"""
    You are a regulated AI valuation system for Calgary Alberta.

    Prediction: {prediction}
    Top Drivers: {shap_values}
    Governance Rules: {retrieved_docs}

    Provide:
    1. Clear valuation reasoning
    2. Regulatory alignment reference
    3. Risk flags (if any)
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]