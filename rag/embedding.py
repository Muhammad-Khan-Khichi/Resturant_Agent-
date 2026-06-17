import os
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("MISTRALAI_API_KEY") or os.getenv("MISTRAL_API_KEY")
os.environ["MISTRALAI_API_KEY"] = api_key

from langchain_mistralai import MistralAIEmbeddings
from splitter import texts

embeddings = MistralAIEmbeddings(model="mistral-embed")


chunks_content = [doc.page_content for doc in texts]
embeddings_result = embeddings.embed_documents(chunks_content)
