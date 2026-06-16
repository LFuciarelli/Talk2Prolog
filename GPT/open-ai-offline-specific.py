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
    with open("exec_time_offline_specific.txt", "a") as time_file:
        time_file.write(f"{total_time}\n")

# === GPT TESTING ===
import prolog_gpt_handler

file_name = input("File name: ")
with open(file_name, "r", encoding="utf-8") as f:
    input_sentences = f.read()
#input_sentences = input("Enter the sentences in natural language:")

start_time = time.perf_counter()

instructions = """
    You are a coding assistant that converts natural-language sentences into Prolog expressions.
    For each sentence (which are separated by a new line), output exactly one Prolog fact, rule, or query (no explanations).
    Nested compound terms are allowed.
    Do not insert dummy subjects ("it" or "there" in expletive constructions)
    Every term must have arity 0, 1 or 2.
    Consider subject-verb agreement.
    """


response = client.responses.create(
    model="gpt-5.2",
    instructions=instructions,
    input=input_sentences,
    temperature=0,
    top_p=0
    #seed=123
)

end_timing()

terms = response.output_text.split("\n")
for term in terms:
    term = term.strip()
    if len(term) > 0:
        try:
            kb_type = "specific"
            prolog_handler = prolog_gpt_handler.PrologHandler(kb_path=f"KB-GPT-offline-{kb_type}.pl")
            query = term.find("?") != -1
            term = term.replace("?- ", "").replace(".", "")
            if query:
                prolog_handler.query(term)
            else:
                prolog_handler.insert(term, input_sentences)
            prolog_handler.close()
        except:
            continue