# === SPACY LOADING ===
import spacy

language = "en"
model = "lg"
nlp = spacy.load(f'{language}_core_web_{model}')

# === TIMING ===
import time

def end_timing():
    end_time = time.perf_counter()
    total_time = f"{round(end_time - start_time, 5)}".replace(".", ",")
    with open("exec_time.txt", "a") as time_file:
        time_file.write(f"{total_time}\n")

# === LIBRARY IMPORTS ===
import sys
import prolog_handler
import preprocessor
import semantic_parser

# === CONFIGURATION FLAGS ===

# default, insert an if to change the values through the command prompt
chunk_arg = False # default False
conjugate_third_person = True # default True
conjugate_present = True # default True
include_adv = True # default True
include_preposition = True # default True
verb_as_relation = True # default True It is not used if the verb is "to be" in the 3rd person singular ("is" is a built-in predicate)
char_as_var = True # default True
adj_as_term = True # default True

# Pre-processing flags
word2num = True # default True (if False, numerical words will not be treated as numeric values)
solve_coref = "stanford" # default "manual" (can also be "stanford", but sometimes coreference resolution breaks the original sentence)

# === INPUT SENTENCE PRE-PROCESSING === 

try:
    text = input("Enter a sentence: ")
    start_time = time.perf_counter()
    (text, query) = preprocessor.to_sentence_form(text)
    text = preprocessor.canonize_sentence(text, word2num=word2num, solve_coref=solve_coref, nlp=nlp)
    substrings = preprocessor.sentence_to_clauses(text, nlp=nlp) # sentence clauses and conjunctions
except:
    print("An error occurred during sentence pre-processing.")
    end_timing()
    exit(0)

# === SEMANTIC PARSING ===
try:
    terms = dict() # key: natural language, value: Prolog
    semantic_parser = semantic_parser.SemanticParser(
            nlp=nlp,
            verb_as_relation=verb_as_relation,
            conjugate_present=conjugate_present,
            conjugate_third_person=conjugate_third_person,
            char_as_var=char_as_var,
            adj_as_term=adj_as_term,
            chunk_arg=chunk_arg,
            include_adv=include_adv,
            include_preposition=include_preposition
        )

    body_terms = dict() # key: name, value: arity
    for i in range(len(substrings)):
        substring = substrings[i]
        if substring.strip().lower() in ["if", "and", "or"]:
            continue

        # Clause (treated as a sentence)
        (normalized_clause, _) = preprocessor.to_sentence_form(substring)

        # Term from clause (flags in new doc)
        semantic_parser.new_doc(normalized_clause)
        semantic_parser.term_construction()

        clause_term = semantic_parser.term
        if i == 0:
            head_term_name = semantic_parser.term_name
            head_term_arity = semantic_parser.term_arity
        else:
            body_terms[semantic_parser.term_name] = semantic_parser.term_arity

        if not query:
            query = semantic_parser.is_query

        terms[substring] = clause_term

    subterms = []
    for substring in substrings:
        subterm = terms.get(substring, None)
        if subterm is None: # if subterm is none, then it is a connector/conjunction
            connector = substring.strip().lower()
            if connector == "if":
                subterms.append(":-")
            elif connector == "and":
                subterms.append(",")
            elif connector == "or":
                subterms.append(";")
        else:
            subterms.append(subterm)
    term = " ".join(subterms)
except:
    print("An error occurred during post-processing sentence parsing.")
    end_timing()
    exit(0)

end_timing()

try:
    prolog_handler = prolog_handler.PrologHandler()
    if query:
        prolog_handler.query(term)
    else:
        prolog_handler.insert(term, head_term_name, head_term_arity, body_terms, text)
    prolog_handler.close()
except:
    print("An error occurred during Prolog execution.")
    exit(0)

exit(0)