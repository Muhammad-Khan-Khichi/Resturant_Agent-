import os
from dotenv import load_dotenv
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

api_key = os.getenv("MISTRALAI_API_KEY") or os.getenv("MISTRAL_API_KEY")
os.environ["MISTRALAI_API_KEY"] = api_key


embeddings = MistralAIEmbeddings(model="mistral-embed")
FAISS_DIR = os.path.join(os.path.dirname(__file__), "faiss_index")
vector_store = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)


def search_menu(query: str, k: int = 3) -> str:
    """
    Search the restaurant menu using semantic search.
    
    Args:
        query: The user's question (e.g., "What burgers do you have?")
        k: Number of results to return (default: 3)
    
    Returns:
        Formatted string of matching menu items
    """
    results = vector_store.similarity_search(query, k=k)
    
    if not results:
        return "Sorry, I couldn't find anything on the menu matching that."
    
    formatted = []
    for doc in results:
        formatted.append(doc.page_content.strip())
    
    return "\n---\n".join(formatted)



