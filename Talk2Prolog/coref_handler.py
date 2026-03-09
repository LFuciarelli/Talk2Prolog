from stanfordnlp.server import CoreNLPClient

class CorefHandler():
    def __init__(self, coref_sys='dcoref'):
        self.str = str
        self.coref_sys = coref_sys
    
    def solve(self, str):
        results = []
        with CoreNLPClient(
            annotators=['tokenize','ssplit','pos','lemma','ner','parse',self.coref_sys],
            timeout=30000,
            memory='8G'
        ) as client:
            ann = client.annotate(str)

            # Get all sentences of input string
            sentences = [[token.word for token in sent.token] for sent in ann.sentence]

            for chain in ann.corefChain:
                # Best mention of an entity
                rep_mention = chain.mention[chain.representative]
                rep_idx = rep_mention.mentionID

                # Index of the representative inside the sentence
                sentence_idx = rep_mention.sentenceIndex
                rep_mention_txt = sentences[sentence_idx][rep_mention.beginIndex:rep_mention.endIndex]
                rep_mention_txt = " ".join(rep_mention_txt)

                for mention in chain.mention:
                    if mention.mentionID == rep_idx:
                        continue
                    sentences[sentence_idx][mention.beginIndex:mention.endIndex] = [rep_mention_txt]
                
                #results = []
                for sentence in sentences:
                    res = " ".join(sentence)
                    results.append(res)
        return results