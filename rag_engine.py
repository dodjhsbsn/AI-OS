import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
# [重要] 将数据库路径指向挂载卷，这样重启容器记忆不会丢
DB_PATH = "/mnt/sysroot/chroma_db" 

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            try:
                response = self.client.models.embed_content(
                    model="text-embedding-004", contents=text
                )
                embeddings.append(response.embeddings[0].values)
            except: embeddings.append([0.0] * 768)
        return embeddings

memory_collection = None
try:
    print("[RAG] 🧠 Initializing Hippocampus...")
    # 确保持久化目录存在
    os.makedirs(DB_PATH, exist_ok=True)
    
    _chroma_client = chromadb.PersistentClient(path=DB_PATH)
    _embedding_fn = GeminiEmbeddingFunction(api_key=API_KEY)
    memory_collection = _chroma_client.get_or_create_collection(
        name="gemini_os_memory", embedding_function=_embedding_fn
    )
    print(f"[RAG] ✅ Memory System Online (Path: {DB_PATH}).")
except Exception as e:
    print(f"[RAG] ❌ Memory Failure: {e}")

def memorize_knowledge(content: str, tag: str = "general"):
    """将信息存入长期记忆"""
    if not memory_collection: return "Error: Memory offline."
    try:
        memory_collection.add(
            documents=[content], metadatas=[{"tag": tag}], ids=[str(hash(content))]
        )
        return f"Success: Memorized '{content[:20]}...'"
    except Exception as e: return f"Error: {e}"

def recall_knowledge(query: str, n_results: int = 3):
    """从长期记忆检索"""
    if not memory_collection: return "Error: Memory offline."
    try:
        results = memory_collection.query(query_texts=[query], n_results=n_results)
        return str(results['documents'][0])
    except Exception as e: return f"Error: {e}"