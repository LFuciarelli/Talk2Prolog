# ..\openaienv\Scripts\activate
# https://notes.kodekloud.com/docs/Mastering-Generative-AI-with-OpenAI/Understanding-Tokens-and-API-Parameters/Understanding-OpenAI-API-Parameters

# === OPEN-AI LOADING ===
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# === TIMING AND IMPORTS ===
import time
import sys

def end_timing():
    end_time = time.perf_counter()
    total_time = f"{round(end_time - start_time, 5)}".replace(".", ",")
    with open("exec_time_online_general.txt", "a") as time_file:
        time_file.write(f"{total_time}\n")

# === GPT TESTING ===
import prolog_gpt_handler

input_sentence = input("Enter a sentence: ")

start_time = time.perf_counter()

instructions =  """
    You are a coding assistant that converts a single natural-language sentence into one Prolog expression.
    Output exactly one Prolog fact, rule, or query (no explanations).
    """

response = client.responses.create(
    model="gpt-5.2",
    instructions=instructions,
    input=input_sentence,
    temperature=0,
    top_p=0
    #seed=123
)

end_timing()
#print(response.output_text)

prolog_handler = prolog_gpt_handler.PrologHandler(kb_path="KB-GPT-online-general.pl")
term = response.output_text
query = term.find("?") != -1
term = term.replace("?- ", "").replace(".", "")
if query:
    prolog_handler.query(term)
else:
    prolog_handler.insert(term, input_sentence)
prolog_handler.close()