import os
from typing import List, Optional
from langchain_core.tools import Tool
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
    Document
)
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from llama_index.core.callbacks import CallbackManager
from llama_index.core.node_parser import SentenceSplitter
import rank_bm25
# import Stemmer  # Check if we can use this, otherwise simple split

try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    # Use a small, efficient model. "local" maps to BAAI/bge-small-en-v1.5 by default in recent versions
    # For Chinese support, BAAI/bge-small-zh-v1.5 is better, but let's stick to a safe default that downloads quickly.
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    print("Using local HuggingFace embeddings.")
except ImportError:
    print("HuggingFace embeddings not found. Falling back to OpenAI (requires OPENAI_API_KEY).")
    # Default is OpenAI

# Ensure we have a BM25 implementation
class CustomBM25Retriever(BaseRetriever):
    """Custom BM25 Retriever using rank_bm25 package."""
    
    def __init__(self, nodes: List[TextNode], similarity_top_k: int = 5):
        self.nodes = nodes
        self.similarity_top_k = similarity_top_k
        self.corpus = [node.get_content() for node in nodes]
        self.bm25 = rank_bm25.BM25Okapi([self._tokenize(text) for text in self.corpus])
        super().__init__()

    def _tokenize(self, text: str) -> List[str]:
        # Simple tokenization
        return text.lower().split()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query = query_bundle.query_str
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Pair scores with nodes
        nodes_with_scores = []
        for i, score in enumerate(scores):
            nodes_with_scores.append(NodeWithScore(node=self.nodes[i], score=float(score)))
            
        # Sort by score descending
        nodes_with_scores.sort(key=lambda x: x.score, reverse=True)
        return nodes_with_scores[:self.similarity_top_k]

class HybridRetriever(BaseRetriever):
    """Hybrid Retriever combining Vector and BM25."""
    
    def __init__(self, vector_retriever: BaseRetriever, bm25_retriever: BaseRetriever):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        vector_nodes = self.vector_retriever.retrieve(query_bundle)
        bm25_nodes = self.bm25_retriever.retrieve(query_bundle)
        
        # Simple RRF (Reciprocal Rank Fusion)
        # Create a map of node_id -> score
        node_scores = {}
        k = 60 # RRF constant
        
        for rank, node in enumerate(vector_nodes):
            node_id = node.node.node_id
            if node_id not in node_scores:
                node_scores[node_id] = {"node": node.node, "score": 0.0}
            node_scores[node_id]["score"] += 1.0 / (k + rank + 1)
            
        for rank, node in enumerate(bm25_nodes):
            node_id = node.node.node_id
            if node_id not in node_scores:
                node_scores[node_id] = {"node": node.node, "score": 0.0}
            node_scores[node_id]["score"] += 1.0 / (k + rank + 1)
            
        # Convert back to list
        final_nodes = []
        for node_id, data in node_scores.items():
            final_nodes.append(NodeWithScore(node=data["node"], score=data["score"]))
            
        # Sort
        final_nodes.sort(key=lambda x: x.score, reverse=True)
        return final_nodes[:10] # Return top 10

# Global Index
_INDEX = None
_BM25_RETRIEVER = None

def get_rag_engine():
    global _INDEX, _BM25_RETRIEVER
    
    knowledge_dir = os.path.join(os.getcwd(), "backend/knowledge")
    storage_dir = os.path.join(os.getcwd(), "backend/storage")
    
    # Check if index exists
    if os.path.exists(storage_dir) and os.listdir(storage_dir):
        try:
            print("Loading index from storage...")
            storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
            _INDEX = load_index_from_storage(storage_context)
            
            # Rebuild BM25 retriever from docs (nodes) in index
            # Note: docstore has nodes.
            nodes = list(_INDEX.docstore.docs.values())
            # Filter for TextNodes
            text_nodes = [n for n in nodes if isinstance(n, TextNode)]
            _BM25_RETRIEVER = CustomBM25Retriever(text_nodes)
            return
        except Exception as e:
            print(f"Error loading index: {e}. Rebuilding...")
    
    # Build index
    if not os.path.exists(knowledge_dir) or not os.listdir(knowledge_dir):
        print("No knowledge files found. RAG tool will be empty.")
        return

    print("Building index from documents...")
    documents = SimpleDirectoryReader(knowledge_dir).load_data()
    
    # Parse nodes
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)
    
    # Build Vector Index
    # This will use Settings.embed_model (Local HF or OpenAI)
    _INDEX = VectorStoreIndex(nodes)
    
    # Persist
    _INDEX.storage_context.persist(persist_dir=storage_dir)
    
    # Build BM25
    _BM25_RETRIEVER = CustomBM25Retriever(nodes)
    print("Index built and persisted.")

def search_knowledge_base(query: str) -> str:
    """
    Search the local knowledge base (PDF/TXT/MD files in backend/knowledge) using Hybrid Search (Vector + BM25).
    """
    global _INDEX, _BM25_RETRIEVER
    
    if _INDEX is None:
        get_rag_engine()
        
    if _INDEX is None:
        return "Knowledge base is empty. Please add documents to 'backend/knowledge' and restart."

    try:
        vector_retriever = _INDEX.as_retriever(similarity_top_k=5)
        hybrid_retriever = HybridRetriever(vector_retriever, _BM25_RETRIEVER)
        
        nodes = hybrid_retriever.retrieve(query)
        
        # Format response
        response = f"Found {len(nodes)} relevant snippets:\n\n"
        for i, node in enumerate(nodes):
            # Try to get metadata for filename
            meta = node.node.metadata or {}
            filename = meta.get("file_name", "Unknown File")
            response += f"--- Snippet {i+1} (Source: {filename}, Score: {node.score:.4f}) ---\n"
            response += f"{node.node.get_content().strip()}\n\n"
            
        return response
    except Exception as e:
        return f"Error searching knowledge base: {e}"

def get_rag_tool():
    return Tool(
        name="search_knowledge_base",
        func=search_knowledge_base,
        description="Search for specific information in the local knowledge base (documents in backend/knowledge). Use this when the user asks about uploaded files or specific domain knowledge."
    )
