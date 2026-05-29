import sys
from unittest.mock import MagicMock

sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()


from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from langchain_groq import ChatGroq
from utils import API_calls
import time
import streamlit as st

MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

def get_wrapped_llm(model_name):
    groq_llm = ChatGroq(model=model_name, api_key=API_calls.get_groqAPI())
    return LangchainLLMWrapper(groq_llm)

def evaluate_with_fallback(dataset, metrics):
    for model in MODELS:
        try:
            wrapped = get_wrapped_llm(model)
            for metric in metrics:
                metric.llm = wrapped
            
            return evaluate(dataset, metrics=metrics)
        
        except Exception as e:
            error_str = str(e)
            if "rate_limit_exceeded" in error_str:
                
                if "tokens per day" in error_str:
                    continue  
                
                time.sleep(10)
                try:
                    return evaluate(dataset, metrics=metrics)
                except Exception:
                    continue
            else:
                raise e
    
    raise RuntimeError("All models rate limited. Try again later.")

def get_faithfulnessScore(user_q, llm_ans, ret_chunks):

    if "api_calls" in st.session_state:

        st.session_state.api_calls += 1
    
    dataset = Dataset.from_dict({
        "question": [user_q],
        "answer": [llm_ans],
        "contexts": [[chunk["text"] for chunk in ret_chunks]]
    })
    
    return evaluate_with_fallback(dataset, metrics=[faithfulness])