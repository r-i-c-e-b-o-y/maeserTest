# Extract the text from the The Expanse Wikipedia pages

import wikipediaapi

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='Maeser AI Example',
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI
)


background_info1 = wiki_wiki.page("The Expanse (TV series)")
background_info2 = wiki_wiki.page("The Expanse (novel series)")

#Converted The Expanse fan wiki sites into plain text then imported into Python

bg1 = background_info1.text
bg2 = background_info2.text
millerTV = ""
millerBook = ""
with open("millerTV.txt", "r") as file:
    # Read the entire file content as a string
    millerTV = file.read()
with open("millerBook.txt", "r") as file:
    # Read the entire file content as a string
    millerBook = file.read()

# Split the text into chunks and vectorize them

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
documents = text_splitter.create_documents([bg1, bg2, millerTV, millerBook])

from langchain_community.vectorstores import FAISS

db = FAISS.from_documents(documents, OpenAIEmbeddings())
db.save_local("vectorstores/miller")