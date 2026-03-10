import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from backend.tools.rag import search_knowledge_base

print("Testing RAG Tool...")
try:
    result = search_knowledge_base("OpenClaw")
    print("\nResult:")
    print(result)
except Exception as e:
    print(f"\nError: {e}")
