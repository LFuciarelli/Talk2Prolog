import spacy
import numerizer
import pyinflect

# Transforms a clause into a Prolog term
class SemanticParser():

    ## === SPACY MODEL INITIALIZATION ===
    def __init__(self,
                nlp=None, 
                language="en",
                model="lg", 
                verb_as_relation=True, 
                conjugate_present=True,
                conjugate_third_person=True,
                char_as_var=True,
                adj_as_term=True,
                chunk_arg=False,
                include_adv=True,
                include_preposition=True,
                prefix="my"):
        
        # Model (default English, large)
        #self.nlp = spacy.load(f'{language}_core_web_{model}')
        self.nlp = nlp

        # Flags
        self.verb_as_relation=verb_as_relation
        self.conjugate_present=conjugate_present
        self.conjugate_third_person=conjugate_third_person
        self.char_as_var=char_as_var
        self.adj_as_term=adj_as_term
        self.chunk_arg=chunk_arg
        self.include_adv=include_adv
        self.include_preposition=include_preposition
        self.prefix=prefix

    ## === NEW DOC INITIALIZATION ===
    def new_doc(self, clause: str):

        # Loading of spacy
        self.doc = self.nlp(clause)
        self.clause = clause

        # Grammar parsing
        self.aux = None
        self.attribute = None

        self.subject = None
        self.subject_chunk = None

        self.verb = None
        self.conjugated_relation = None
        self.verb_preposition = None
        self.adverb = None

        self.object = None
        self.object_chunk = None
        self.predicate_adjective = None
        self.predicate_nominative = None
        self.open_clausal_complement = None

        self.is_query = (self.doc[0].pos_ == "AUX" or self.doc[0].tag_ in ["WP", "WRB", "WDT"])
        self.is_passive = False
        self.is_negation = False
        self.is_past = (clause.lower().find("did") != -1)

        # Semantic meaning (spacy objects)
        self.relation = None
        self.arg1 = None
        self.arg1_chunk = None
        self.arg2 = None
        self.arg2_chunk = None

        # Output term information (strings)
        self.term_name = None
        self.term_arity = None
        self.term = None


    # === ENGLISH CLAUSE ELEMENTS ===
    def complement_identifier(self):
        for token in self.doc:
            # Check part of speech tagging (coarse)
            if token.pos_ == "ADJ": # e.g. "Olivia is smart.", "John felt angry"
                self.predicate_adjective = token
            elif token.pos_ == "NOUN" and token.dep_ != "nsubj": # e.g. 'John is a man."
                self.predicate_nominative = token
            elif token.pos_ == "ADV" and self.include_adv: # e.g. "She spoke angrily."
                self.adverb = token
            elif token.pos_ == "AUX":
                self.aux = token

            # Check part of speech tagging (fine)
            if token.tag_ == "IN" and self.include_preposition and token.head.text == self.verb.text:
                self.verb_preposition = token

            # Check dependencies
            if token.dep_ in ["nsubj", "expl", "nsubjpass"]:
                self.subject = token
                if token.dep_ == "nsubjpass":
                    self.is_passive = True
            elif token.dep_ == "ROOT":
                self.verb = token
            elif token.dep_ in ["xcomp"]: #and token.head.text == verb.text: (e.g. She likes reading.)
                self.open_clausal_complement = token
            elif token.dep_ in ["attr"]: # e.g. John is 5
                self.attribute = token

            # Check negation
            if token.text.lower() in ["not"]:
                self.is_negation = True

    def svo_identifier(self):
        for chunk in self.doc.noun_chunks:
            if chunk.root.dep_ in ["nsubj", "expl", "nsubjpass"]:
                self.subject = chunk.root
                self.subject_chunk = chunk
                self.verb = chunk.root.head
                if chunk.root.dep_ == "nsubjpass":
                    self.is_passive = True
                for verb_child in self.verb.children:
                    if verb_child.text in ["not"]:
                        self.is_negation = True
            elif chunk.root.dep_ in ["attr"]: # John is the son of Mark
                self.attribute = chunk.root
            elif chunk.root.dep_ in ["dobj", "pobj"]: #or chunk.root.head == verb:
                self.object = chunk.root
                self.object_chunk = chunk
                if chunk.root.head.tag_ == "IN" and self.include_preposition:
                    self.verb_preposition = chunk.root.head
                if chunk.root.head.dep_ in ["xcomp"]: # (e.g. She likes reading books.)
                    self.open_clausal_complement = chunk.root.head

    # === TERM CONSTRUCTION AUX FUNCTIONS ===
    def add_prefix(self, predicate):
        if not isinstance(predicate, str): # we are passing a token
            predicate = predicate.text

        with open("prolog-built-in-predicates.txt", "r") as context_file:
            context_content = [context_line.strip() for context_line in context_file]

        p = predicate.split("(")[0]
        if p in context_content:
            predicate = predicate.replace(p, f"{self.prefix}_{p}", 1)
        return predicate

    def normalize(self, in_token, in_chunk, is_arg2=False):
         # Noun phrases
        if self.chunk_arg and in_chunk:
            out_string = in_chunk.text.replace(" ", "_").replace("-", "_").replace(".", "")
        else:
            out_string = in_token.text.replace(" ", "_").replace("-", "_").replace(".", "")
            compounds = [child.text for child in in_token.children if child.dep_ in ["compound"]]
            if len(compounds) > 0:
                compounds_txt = "_".join(compounds)
                out_string = compounds_txt + "_" + out_string

        # Variables
        if in_token.tag_ not in ["WP", "WRB", "WDT"] and not (len(out_string) == 1 and self.char_as_var and out_string != "I"):
            out_string = out_string.lower()
        
        if in_token.tag_ in ["WP", "WRB", "WDT"]:
            out_string = out_string.capitalize()
        
        indefinite_pronouns = ["someone", "somebody", "anyone", "anybody", "something", "anything", "somewhere", "anywhere",
                               "everyone", "everybody", "everything", "everywhere"]
        if in_token.text.lower() in indefinite_pronouns:
            out_string = out_string.capitalize()

        # Adjective nesting
        adjs = [child for child in in_token.children if child.pos_ in ["ADJ"]]
        adjs.reverse()
        for adj in adjs:
            adj_txt = self.add_prefix(adj.text.lower())
            out_string = f"{adj_txt}({out_string})" if self.adj_as_term else f"{adj_txt}_{out_string}"

        # Gerund nesting
        if is_arg2 and self.open_clausal_complement:
            if in_token.head.text == self.open_clausal_complement.text:
                occ_txt = self.add_prefix(self.open_clausal_complement.text.lower())
                out_string = f"{occ_txt}({out_string})"

        # Amount
        amounts = [child for child in in_token.children if child.dep_ in ["nummod"]]
        if len(amounts) > 0:
            quantity_value = amounts[0].text.replace(",", "")
            out_string = f"quantity({out_string}, {quantity_value})"

        return out_string

    def relation_as_predicate(self):
        def is_third_person_sing():
            return (self.arg1.text.lower() not in ["i", "you", "we", "they"]) and self.arg1.tag_ not in ["NNS", "NNPS"]

        # Conjugate relation verb according to finite present indicate
        if self.conjugate_present: #and self.relation.tag_ in ["VBP", "VBZ", "VB", "VBN"]:
            # Conjugate relation verb according to 3rd person singular subject
            if self.conjugate_third_person and is_third_person_sing():
                self.conjugated_relation = self.relation._.inflect("VBZ")
            else:
                self.conjugated_relation = self.relation._.inflect("VBP")
        else:
            if self.is_past: # queries and negative sentences in the past
                self.conjugated_relation = self.relation._.inflect("VBD")

        out_string = self.relation.text.lower() if not self.conjugated_relation else self.conjugated_relation.lower()

        if self.verb_preposition and not self.is_passive:
            out_string = out_string + f"_{self.verb_preposition}"
        return out_string

    # === TERM CONSTRUCITON ===
    def term_construction_aux(self, quantity=None):
        self.term = ""
        if quantity: # always binary unit(object, total)
            self.term_name = self.add_prefix(quantity)
            term_arg1 = self.normalize(self.arg1, self.arg1_chunk)
            term_arg2 = self.normalize(self.arg2, self.arg2_chunk, is_arg2=True)
            self.term = f"{self.term_name}({term_arg1}, {term_arg2})"
            self.term_arity = 2
        else:
            if self.term_arity == None:
                self.term = self.normalize(self.arg2, self.arg2_chunk, is_arg2=True)
                if self.term.find("(") == -1:
                    self.term = self.add_prefix(self.term)
                    self.term_name = self.term
                    self.term_arity = 0
                else:
                    self.term_name = self.add_prefix(self.term.split("(")[0])
                    self.term_arity = 1 if self.term_name != "quantity" else 2
            elif self.term_arity == 1:
                if self.arg2: # Priority given to transform arg2 as predicate
                    self.term_name = self.normalize(self.arg2, self.arg2_chunk, is_arg2=True)
                    self.term_name = self.add_prefix(self.term_name)
                    term_arg = self.normalize(self.arg1, self.arg1_chunk)
                    par_idx = self.term_name.find(")")
                    if par_idx == -1:
                        self.term = f"{self.term_name.lower()}({term_arg})"
                    else:
                        self.term = f"{self.term_name[:par_idx]}({term_arg}){self.term_name[par_idx:]}"
                        self.term_name = self.term_name[:self.term_name.find("(")]
                else: # If it is not present, use arg1
                    self.term_name = self.add_prefix(self.relation_as_predicate())
                    term_arg = self.normalize(self.arg1, self.arg1_chunk)
                    self.term = f"{self.term_name}({term_arg})"
            elif self.term_arity == 2:
                self.term_name = self.attribute if self.attribute else self.relation_as_predicate() # e.g. attribute could be son
                self.term_name = self.add_prefix(self.term_name)
                term_arg1 = self.normalize(self.arg1, self.arg1_chunk)
                term_arg2 = self.normalize(self.arg2, self.arg2_chunk, is_arg2=True)
                self.term = f"{self.term_name}({term_arg1}, {term_arg2})"
        
        # Negation nesting
        if self.is_negation:
            self.term_name = f"{self.prefix}_not"
            self.term_arity = 1
            self.term = f"{self.term_name}({self.term})"
        
        # Check to ensure all predicates are lowercase
        first_par = self.term.find("(")
        predicate = self.term[:first_par] if first_par > 0 else self.term
        if not predicate.islower():
            self.term = predicate.lower() + self.term[first_par:]
            self.term_name = predicate.lower()

    def term_construction(self):
        # === ARGUMENT 2 ASSIGNMENT ===
        self.svo_identifier()
        if (self.subject is None) or (self.verb is None) or (self.object is None):
            self.complement_identifier()

            # Complement and adverb become the second argument
            if self.predicate_adjective:
                self.arg2 = self.predicate_adjective
            if self.predicate_nominative:
                self.arg2 = self.predicate_nominative
            if not self.arg2 and self.adverb: # attention that it would be a complement in "Dan is here" but not "Dan spoke loudly"
                self.arg2 = self.adverb # only adverbs of manner basically in SV phrases

            # Gerund becomes the second argument is there are not any object, complement or adverb
            if not self.arg2:
                self.arg2 = self.open_clausal_complement
            if not self.arg2 and self.aux:
                self.arg2 = self.verb
                self.relation = self.aux
        else:
            # Usually the second argument is the object
            self.arg2 = self.object
            self.arg2_chunk = self.object_chunk

        # === ARGUMENT 1 ASSIGNMENT ===
        if self.is_passive:
            # the object becomes the first argument
            self.arg1 = self.arg2
            self.arg2 = self.subject

            # same thing for the noun phrase
            self.arg1_chunk = self.arg2_chunk
            self.arg2_chunk = self.subject_chunk
        else:
            self.arg1 = self.subject
            self.arg1_chunk = self.subject_chunk

        # === RELATION ASSIGNMENT ===
        if not self.relation:
            self.relation = self.verb

        # === ATTRIBUTE HANDLING ===
        quantity = None
        if self.attribute:
            if self.attribute.pos_ == "NUM" and self.arg1.ent_type_ == "PERSON": # age
                self.arg2 = self.attribute
                quantity = "age"
            if self.arg2.text == self.attribute.text: # no "real" attribute
                self.attribute = None
            elif self.relation.lemma_ == "be" and self.attribute.tag_.startswith("W"): # e.g. What is a food?
                self.arg2 = self.arg1 # "subject" becomes 2nd arg
                self.arg1 = self.attribute
                self.attribute = None

        # === ARITY ASSIGNMENT ===
        if self.arg1.text.lower() in ["it", "there"]:
            self.term_arity = None
        else:
            if self.verb_as_relation and (self.relation.lemma_ != "be" or self.attribute) and self.arg2:
                self.term_arity = 2
            else:
                self.term_arity = 1

        # === CONSTRUCTION OF THE TERM STRING ===
        self.term_construction_aux(quantity)