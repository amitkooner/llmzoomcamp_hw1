import requests 
import json
from elasticsearch import Elasticsearch
import urllib3
import tiktoken

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fetch the documents data from the URL
docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
docs_response = requests.get(docs_url)
documents_raw = docs_response.json()

documents = []

for course in documents_raw:
    course_name = course['course']
    for doc in course['documents']:
        doc['course'] = course_name
        documents.append(doc)

# Initialize Elasticsearch client
es = Elasticsearch(
    ['https://localhost:9200'],
    basic_auth=('elastic', 'XqqHEf4B_3-7EGAhnO0L'),
    verify_certs=False  # Only for testing purposes
)

index_name = "faq_index"

# Define the search query with a filter for the course field
search_query = {
    "query": {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": "How do I execute a command in a running docker container?",
                        "fields": ["question^4", "text"],
                        "type": "best_fields"
                    }
                }
            ],
            "filter": [
                {
                    "term": {
                        "course": "machine-learning-zoomcamp"
                    }
                }
            ]
        }
    },
    "size": 3
}

# Execute the search query
response = es.search(index=index_name, body=search_query)

# Build the context from the search results
context_template = """
Q: {question}
A: {text}
""".strip()

context_entries = []
hits = response['hits']['hits']
for hit in hits:
    context_entry = context_template.format(
        question=hit['_source']['question'],
        text=hit['_source']['text']
    )
    context_entries.append(context_entry)

context = "\n\n".join(context_entries)

# Define the prompt template
prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

# Construct the final prompt
question = "How do I execute a command in a running docker container?"
prompt = prompt_template.format(question=question, context=context)

# Calculate the length of the resulting prompt
prompt_length = len(prompt)
print("Length of the resulting prompt:", prompt_length)

# Tokenize the prompt using tiktoken
encoding = tiktoken.encoding_for_model("gpt-4")
tokens = encoding.encode(prompt)
print("Number of tokens in the prompt:", len(tokens))

# Optional: Print the tokens for inspection
# print("Tokens:", tokens)