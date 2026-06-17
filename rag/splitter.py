from langchain_text_splitters import RecursiveCharacterTextSplitter
from docs_loader import docs

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=10
)

texts = text_splitter.split_documents(docs)