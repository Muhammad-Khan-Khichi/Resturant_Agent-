from langchain_docling.loader import DoclingLoader

FILE_PATH = "../menu.txt"

loader = DoclingLoader(file_path=FILE_PATH)

docs = loader.load()

