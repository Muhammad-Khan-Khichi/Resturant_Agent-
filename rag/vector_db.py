import os
from dotenv import load_dotenv
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from splitter import texts


load_dotenv()


api_key = os.getenv("MISTRALAI_API_KEY") or os.getenv("MISTRAL_API_KEY")
if not api_key:
    print("❌ No API key found! Check your .env file")
    exit()
os.environ["MISTRALAI_API_KEY"] = api_key




embeddings = MistralAIEmbeddings(model="mistral-embed")


vector_store = FAISS.from_documents(texts, embeddings)


vector_store.save_local("faiss_index")

