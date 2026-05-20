import requests
import json

def ask_AI(chunks,q):

    prompt = f""" You are a PDF analyser specialist. You will be provided with chunks of PDF and a question.
                You have to provide the user with a respectfull answer and of correct info
                
                Data: {chunks}
                    
                Question: {q}"""



    model = "qwen2.5:7b"

    response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
         
    ans = response.json()["response"]
    return ans
