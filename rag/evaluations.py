import sys
from unittest.mock import MagicMock

sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()


from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from langchain_groq import ChatGroq
from utils import API_calls


groq_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=API_calls.get_groqAPI())
wrapped = LangchainLLMWrapper(groq_llm)

faithfulness.llm = wrapped
answer_relevancy.llm = wrapped

def get_faithfulnessScore(user_q,llm_ans,ret_chunks):

    dataset = Dataset.from_dict({

        "question": [user_q],
        "answer": [llm_ans],
        "contexts": [[chunk["text"] for chunk in ret_chunks]]
    })
    
    result = evaluate(dataset, metrics=[faithfulness])
    return result