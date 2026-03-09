import contractions
import string
import coref_handler
import spacy
import claucy
import re
import numerizer

# Sentence canonicalzation
def canonize_sentence(input_sentence: str, word2num=True, solve_coref=None,  nlp=None, language="en", model="lg"):
    # Trim whitespaces
    output_sentence = input_sentence.strip()

    # Eliminate period (e.g. Mr. Whiskers -> Mr Whiskers)
    output_sentence = output_sentence.replace(".", "")
    if output_sentence[-1] not in string.punctuation: # add period back
        output_sentence = output_sentence + "."

    # Expand contractions and fix slang
    output_sentence = contractions.fix(output_sentence)

    # Transform numbers written in words in numerals
    if word2num:
        temp_sentence = re.sub(r"\ba\b", "_A_", output_sentence, flags=re.IGNORECASE)
        temp_sentence = numerizer.numerize(temp_sentence)
        output_sentence = temp_sentence.replace("_A_", "a")

    # Coreference resolution (external library)
    if solve_coref == "stanford":
        coref_obj = coref_handler.CorefHandler()
        output_sentence = coref_obj.solve(output_sentence)[0]
    elif solve_coref == "manual":
        #nlp = spacy.load(f'{language}_core_web_{model}')
        doc = nlp(output_sentence)
        singular_nouns = [token for token in doc if token.tag_ in ["NN", "NNP"]]
        plural_nouns = [token for token in doc if token.tag_ in ["NNS", "NNPS"]]
        personal_pronouns = [token for token in doc if token.tag_ in ["PRP"] and token.i > 0]
        replacement_dict = dict()
        for pp in personal_pronouns:
            if pp.text.lower() in ["they", "them", "themselves"] and len(plural_nouns) > 0:
                replacement_dict[pp.text] = plural_nouns[0].text
            elif pp.text.lower() in ["he", "she", "it", "him", "her", "himself", "herself", "itself"] and len(singular_nouns) > 0:
                if not (singular_nouns[0].ent_type_ in ["PERSON"] and pp.text.lower() == "it"):
                    replacement_dict[pp.text] = singular_nouns[0].text
        for key, value in replacement_dict.items():
            output_sentence = re.sub(fr"\b{key}\b", value, output_sentence)
    return output_sentence

# Sentence capitalization and punctuation (returns also if it is a query or not)
def to_sentence_form(input_sentence: str):
    # Trim whitespaces
    output_sentence = input_sentence.strip()

    # Adds a period/question punctuation mark at the end
    last_char = output_sentence[-1]
    query = False
    if last_char == "?": # if it is a question, leave the question mark, and mark it as a query
        query = True
    elif last_char in string.punctuation: # user added a punctuation, but not necessarily a period or a question mark 
        output_sentence = output_sentence.replace(last_char, ".")
    else: # user did not add any punctuation
        output_sentence = output_sentence + "."
    
    # Capitalized first letter
    output_sentence = output_sentence[0].upper() + output_sentence[1:]  #re.sub(r'[^a-zA-Z0-9\s\-]', '', expanded_text) # Remove special characters and punction (except for the hyphen)
    
    return (output_sentence, query)

def sentence_to_clauses(input_text: str, nlp=None, language="en", model="lg"):
    def aux(doc):
        output_txt = []
        singular = True
        for token in doc:
            txt = token.text
            if token.dep_ == "nsubj":
                if token.tag_ in ["NNS", "NNPS"]:
                    singular = False # third person singular
            elif token.tag_ in ["VBD", "VBP", "VBZ"]:
                if token.tag_ in ["VBP", "VBZ"]: # present
                    if singular:
                        inflect = "VBZ"
                    else:
                        inflect = "VBP"
                else:
                    inflect = "VBD"
                txt = token._.inflect(inflect)
            elif token.dep_ != "nsubj" and token.tag_ in ["NN", "NNS"]:
                if singular:
                    inflect = "NN"
                else:
                    inflect = "NNS"
                txt = token._.inflect(inflect)
            output_txt.append(txt)
        return output_txt

    #nlp = spacy.load(f'{language}_core_web_{model}')
    doc = nlp(input_text)
    cc = None
    sconj = None
    independent = []
    after_then = False
    left = [] # relative to the subordinate
    right = [] # relative to the subordinate
    first_sub_txt = ""
    second_sub_txt = ""
    for token in doc:
        # we don't want to save "if", "then", "and" or "or" (then is completely ignored)
        if token.pos_ == "SCONJ":
            sconj = token
        elif token.text.lower() == "then":
            after_then = True
        elif not sconj or after_then: # independent clause
            if token.dep_ != "punct": # ignore punctuations as well
                independent.append(token)
        else: # dependent clause
            if token.dep_ == "cc":
                cc = token
            elif token.dep_ != "punct": # ignore punctuations
                if not cc:
                    left.append(token)
                else:
                    right.append(token)
                
    ind_clause = " ".join([i.text for i in independent])
    right_verbs = [token for token in right if token.tag_.startswith("VB")]
    left_verbs = [token for token in left if token.tag_.startswith("VB")]
    right_subjs = [token for token in right if token.dep_ in ["expl", "nsubj"] or (token.dep_ == "conj" and (token.tag_.startswith("N") or token.tag_ == "PRP"))]
    left_subjs = [token for token in left if token.dep_ in ["expl", "nsubj"] or (token.dep_ == "conj" and (token.tag_.startswith("N") or token.tag_ == "PRP"))]
    dependent_clauses = None

    if (len(left) > 0 and len(right) > 0):
        left_right_verbs = (len(left_verbs) > 0 and len(right_verbs) > 0)
        left_right_subjs = (len(left_subjs) > 0 and len(right_subjs) > 0)
        dependent_clauses = not (left_right_verbs and left_right_subjs)

    if dependent_clauses:
        if len(right_subjs) > 0:
            if len(right_verbs) == 0: # Bob likes videogames and magazines
                verb = left_verbs[0]
                start_index = left.index(verb)
                first_sub = left
                second_sub = left[0:start_index+1] + right
                first_sub_txt = [token.text for token in first_sub]
                second_sub_txt = [token.text for token in second_sub]
                first_sub_txt = " ".join(first_sub_txt)
                second_sub_txt = " ".join(second_sub_txt)
            else: # Harry and Sam are students (both are nsubj)
                verb = right_verbs[0] # needs verb on the right
                start_index = right.index(verb)
                first_sub = left + right[start_index:]
                second_sub = right
                first_sub_txt = aux(first_sub)
                second_sub_txt = aux(second_sub)
                first_sub_txt = " ".join(first_sub_txt)
                second_sub_txt = " ".join(second_sub_txt)
        else:
            left_txt = [token.text for token in left]
            right_txt = [token.text for token in right]
            verb = left_verbs[0]
            start_index = left.index(verb)
            offset = 1 # It is sunny and warm (shared verb and subject)
            if right[0].tag_.startswith("VB"):
                offset = 0 # Mary likes Peter and lives in NYC (shared subject)
            first_sub_txt = " ".join(left_txt)
            second_sub_txt = " ".join(left_txt[0:start_index+offset] + right_txt)
    else: # only indepent clauses on the right side (e.g. if Peter is smart; if Mary likes Peter and Mary likes John) (None or false)
        left_txt = [token.text for token in left]
        first_sub_txt = " ".join(left_txt)
        right_txt = [token.text for token in right]
        second_sub_txt = " ".join(right_txt)

    clauses = [ind_clause]
    if sconj:
        clauses.append(sconj.text.lower())
    if first_sub_txt:
        clauses.append(first_sub_txt)
    if cc:
        clauses.append(cc.text.lower())
    if second_sub_txt:
        clauses.append(second_sub_txt)
    return clauses