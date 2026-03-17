import chromadb
from chromadb.config import Settings
client = chromadb.PersistentClient(path="./test_chroma")
col = client.get_or_create_collection("test")
print("Adding document...")
col.add(ids=["1"], documents=["test document"])
print("Done!")
