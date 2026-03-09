from pyswip import *

class PrologHandler():
    def __init__(self, kb_path='KB.pl'):
        self.kb_path = kb_path

        # === PROLOG INITIALIZATION ===
        self.prolog = Prolog()

        # === INPUT CONTEXT === 
        self.prolog.consult(kb_path)
        self.context_file = open(kb_path, "r+")
        self.context_content = self.context_file.read() # read file content
        self.context_file.seek(0) # pointer at the beginning of the file

        disable_singleton_warning = ":- style_check(-singleton)."
        if not disable_singleton_warning in self.context_content:
            self.context_file.write(f"{disable_singleton_warning}\n")
    
    # === QUERY ===
    def query(self, goal):
        print(f"?- {goal}.")
        try:
            result = list(self.prolog.query(goal))
            print("Query result: ", bool(result))
            print("Solution:", result)
        except:
            try:
                self.prolog.assertz(goal, catcherrors=True)
                self.prolog.retractall(goal)
                print("Query result: ", False)
            except:
                print("Error: the goal is not well-formed")

    # === INSERTION ===
    def insert(self, clause, term_name, term_arity, body_terms, comment):
        # Saving the new term in the KB and context file

        print(f"{clause}.")

        # Insert dynamic and discontiguous predicate indicators if not already present
        predicate_indicators = ["dynamic", "discontiguous"]
        for predicate_indicator in predicate_indicators:
            predicate = f":- {predicate_indicator} {term_name}/{term_arity}."
            if predicate not in self.context_content:
                self.context_file.write(predicate + "\n")

            for key, value in body_terms.items(): # key name, value arity
                predicate = f":- {predicate_indicator} {key}/{value}."
                if predicate not in self.context_content:
                    self.context_file.write(predicate + "\n")
                
        self.context_file.write(self.context_content)

        try:
            # Dynamic predicate on pyswip prolog as well
            self.prolog.dynamic(f"{term_name}/{term_arity}")
            
            # Insert at the end of the file and query
            self.prolog.assertz(clause)
            self.context_file.write(clause + f". % {comment}\n")
        except:
            print("Error: the clause is not well-formed.")

    def close(self):
        self.context_file.close()