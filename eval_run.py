import os
import math
import sys
from unittest.mock import MagicMock

os.environ["OPENAI_API_KEY"] = "sk-fake-not-used"
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()

from datasets import Dataset
from ragas import evaluate
import ragas
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from utils import API_calls
from rag import pdf_parser, embedder, retriever, llm

PDF_PATH = "uploads\LifeInvader Ad's Internal Policy (EN3).pdf"
MODEL    = "llama-3.3-70b-versatile"

# setup
groq_llm        = ChatGroq(model=MODEL, api_key=API_calls.get_groqAPI())
wrapped_llm     = LangchainLLMWrapper(groq_llm)
hf_embeddings   = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
wrapped_emb     = LangchainEmbeddingsWrapper(hf_embeddings)

# global
ragas.llm        = wrapped_llm
ragas.embeddings = wrapped_emb

# per metric
faithfulness.llm            = wrapped_llm
answer_relevancy.llm        = wrapped_llm
answer_relevancy.embeddings = wrapped_emb
context_recall.llm          = wrapped_llm
context_precision.llm       = wrapped_llm

test_cases = [
    (
        "How much houses we can advertise is a single AD",
        "We can advertise upto 3 houses if the number is not mentioned."
    ),
    (
        "Can we sell a gun store?",
        "Yes it can be advertised but as Ammunition store"
    ),
    (
        "Edit this AD: Selling a house with 2 g.s. and a garden",
        "Edited AD: Selling a house with a garden and 2 g.s. Price: Negotiable."
    ),
    (
        "This AD comes under what category? AD: looking for friends",
        "It comes under Dating category."
    ),
    (
        "Can we buy weapons?",
        "No"
    ),
]


def run_eval():

    print("Loading PDF...")
    with open(PDF_PATH, "rb") as f:
        chunks = pdf_parser.get_chunks(f)

    print(f"Chunks loaded: {len(chunks)}")

    print("Building index...")
    embs  = embedder.embed_chunks(chunks)
    index = retriever.build_index(embs)

    questions     = []
    answers       = []
    contexts      = []
    ground_truths = []

    print("\nRunning questions through pipeline...\n")

    for i, (question, ground_truth) in enumerate(test_cases):

        print(f"Q{i+1}: {question}")

        q_emb      = embedder.embed_query(question)
        ret_chunks = retriever.get_topK_chunks(chunks, index, question, q_emb)

        full_answer = ""
        response, _ = llm.getResponse(
            MODEL, chunks, ret_chunks, index,
            question, history=None, isBetter=False
        )
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_answer += content

        print(f"A{i+1}: {full_answer[:120]}...")
        print(f"     chunks retrieved: {len(ret_chunks)}\n")

        questions.append(question)
        answers.append(full_answer)
        contexts.append([c["text"] for c in ret_chunks])
        ground_truths.append(ground_truth)

    dataset = Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths
    })

    print("Running RAGAS evaluation...\n")

    result = evaluate(dataset, metrics=[
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision
    ])

    metrics = {
        "Faithfulness":      "faithfulness",
        "Answer Relevancy":  "answer_relevancy",
        "Context Recall":    "context_recall",
        "Context Precision": "context_precision",
    }

    print("=" * 45)
    print("OVERALL RESULTS")
    print("=" * 45)

    for label, key in metrics.items():
        score = result[key]
        if math.isnan(score[0]):
            print(f"{label:<22} unavailable")
        else:
            bar = "█" * int(score * 20)
            print(f"{label:<22} {round(score[0] * 100, 1):>5}%  {bar}")

    print("=" * 45)

    print("\nPER QUESTION BREAKDOWN:")

    for i, (q, s) in enumerate(zip(questions, result.scores)):

        print(f"\nQ{i+1}: {q}")

        for label, key in metrics.items():
            score = s.get(key, float("nan"))
            if math.isnan(score[0]):
                print(f"  {label:<22} N/A")
            else:
                print(f"  {label:<22} {round(score[0] * 100, 1)}%")


if __name__ == "__main__":
    run_eval()