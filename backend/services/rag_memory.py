import json
import os
import math
from typing import List, Dict, Any, Tuple
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("[RAG] [WARN] Numpy not available. RAG Memory running in degraded mode.")

class RAGMemory:
    """
    Visual Memory Engine.
    Stores trading signals as numerical vectors (embeddings) and retrieves similar historical contexts.
    
    Embedding Signature (Simplified):
    [RSI, Volume_Ratio, Score, Trend_Value]
    """
    
    def __init__(self, storage_path: str = "data/memory_index.json"):
        self.storage_path = storage_path
        self.vectors: List[List[float]] = []
        self.metadata: List[Dict] = [] # Stores signal details and outcomes
        self.dim = 4 # Dimension of embedding
        
        self._load_memory()
        
    def _load_memory(self):
        """Load memory from disk"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.vectors = data.get("vectors", [])
                    self.metadata = data.get("metadata", [])
                print(f"[RAG] [MEM] Memory loaded: {len(self.vectors)} historical patterns.", flush=True)
            except Exception as e:
                print(f"[RAG] [ERROR] Error loading memory: {e}", flush=True)
                
    def save_memory(self):
        """Persist memory to disk"""
        try:
            # Ensure dir exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump({
                    "vectors": self.vectors,
                    "metadata": self.metadata
                }, f)
        except Exception as e:
            print(f"[RAG] [ERROR] Error saving memory: {e}", flush=True)

    def _compute_embedding(self, signal: Dict) -> List[float]:
        """
        Convert a signal into a normalized vector signature.
        """
        # 1. RSI (0-100) -> 0.0-1.0
        rsi = float(signal.get("indicators", {}).get("rsi", 50))
        norm_rsi = rsi / 100.0
        
        # 2. Volume Ratio (0-5+) -> 0.0-1.0 (Capped at 5)
        vol = float(signal.get("volume_ratio", 1.0))
        norm_vol = min(vol, 5.0) / 5.0
        
        # 3. Score (0-100) -> 0.0-1.0
        score = float(signal.get("score", 50))
        norm_score = score / 100.0
        
        # 4. Trend (Categorical -> Scalar)
        # We need market_context for this usually, but signal might have it or we assume logic
        # For MVP, we use signal direction and type
        direction = 1.0 if signal.get("direction") == "LONG" else 0.0
        
        return [norm_rsi, norm_vol, norm_score, direction]

    def add_memory(self, signal: Dict, outcome: Dict):
        """
        Add a completed trade to memory.
        outcome: {"status": "TP_HIT", "roi": 2.5}
        """
        vector = self._compute_embedding(signal)
        
        meta = {
            "symbol": signal.get("symbol"),
            "timestamp": signal.get("timestamp"),
            "signal_type": signal.get("signal_type"),
            "outcome": outcome
        }
        
        self.vectors.append(vector)
        self.metadata.append(meta)
        
        # Auto-save every 10 updates? Or just let caller handle it. 
        # For safety, save now.
        self.save_memory()

    def find_similar(self, signal: Dict, k: int = 5) -> List[Dict]:
        """
        Find k nearest neighbors to the signal.
        Returns: List of metadata items with similarity scores.
        """
        if not self.vectors:
            return []
            
        query_vec = self._compute_embedding(signal)
        
        results = []
        
        # Brute-force Cosine Similarity (Fast enough for <10k items)
        # Sim(A, B) = dot(A, B) / (norm(A) * norm(B))
        
        q_norm = math.sqrt(sum(x*x for x in query_vec))
        if q_norm == 0: q_norm = 1e-9 # Avoid div/0
            
        for i, vec in enumerate(self.vectors):
            dot_product = sum(q*v for q, v in zip(query_vec, vec))
            v_norm = math.sqrt(sum(x*x for x in vec))
            if v_norm == 0: v_norm = 1e-9
            
            similarity = dot_product / (q_norm * v_norm)
            
            results.append({
                "similarity": similarity,
                "metadata": self.metadata[i]
            })
            
        # Sort by similarity desc
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:k]
