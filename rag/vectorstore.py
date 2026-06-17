import chromadb
import os
from dotenv import load_dotenv

load_dotenv()


def get_client():
    api_key = os.environ.get("CHROMA_API_KEY")
    tenant = os.environ.get("CHROMA_TENANT")
    database = os.environ.get("CHROMA_DATABASE")

    if not api_key:
        raise ValueError("CHROMA_API_KEY is missing")

    return chromadb.CloudClient(
        api_key=api_key,
        tenant=tenant,
        database=database,
    )


client = get_client()

collection = client.get_or_create_collection(
    name="restaurant_knowledge"
)