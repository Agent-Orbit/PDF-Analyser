from rag import llm
import json
userPrompt = "Who was frankenstein?"
print(type(llm.getKeySentences("llama-3.3-70b-versatile",userPrompt)))
s = "[3,5,6]"
print(type(json.loads(s)))
