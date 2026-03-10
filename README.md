# Talk2Prolog 

Talk2Prolog is a software for translating natural language into Prolog.

## Description

Currently, large language models (LLMs) and generative artificial intelligence (GenAI) are among the principal approaches used for a range of tasks, including translating natural language into a formal representation. 

In this context, we introduce Talk2Prolog, a faster, lighter, and more transparent alternative for translating an English sentence into a Prolog fact, rule, or query. Talk2Prolog can run locally on a standard laptop, guarantees interoperability and consistency due to its coherent translation style, and aligns with trustworthy, sustainable, and explainable artificial intelligence principles. 

Talk2Prolog was built based on a methodology that formalizes common Prolog programming practices, which we derived from a dataset we created using a bottom-up approach. This dataset contains pairs of Prolog expressions and their English meanings obtained from tutorials, university lessons, and GPT. We also included sentences and the corresponding translations obtained with Talk2Prolog in the dataset, some of which were reviewed by Prolog experts and Prolog newcomers. We tested Talk2Prolog against GPT-5.2 using the dataset, evaluating syntax, semantics, and time performance for the translation process. 

Despite its lightweight implementation, Talk2Prolog demonstrates promising results, with an accuracy of 88.3% in experimental semantic translation tasks.
