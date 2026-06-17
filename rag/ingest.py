from vectorstore import collection
from sentence_transformers import SentenceTransformer
import os

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_docs():
    base_path = "knowledge/"
    docs = []

    for file in os.listdir(base_path):
        with open(base_path + file, "r", encoding="utf-8") as f:
            text = f.read()

            chunks = text.split("\n\n")

            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    docs.append((f"{file}_{i}", chunk))

    return docs


def ingest():
    docs = load_docs()

    for doc_id, text in docs:
        embedding = model.encode(text).tolist()

        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text]
        )


if __name__ == "__main__":
    ingest()