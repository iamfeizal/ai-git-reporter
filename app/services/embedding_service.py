"""
Embedding Service — Semantic vector embeddings for commit clustering.

Uses Gemini text-embedding-004 to generate embeddings for commit messages,
then clusters semantically similar commits using cosine similarity.
"""
import os
import numpy as np
from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering

import google.generativeai as genai
from dotenv import load_dotenv

from app.core.state import NormalizedCommit

load_dotenv()

# Default embedding model
EMBEDDING_MODEL = "models/text-embedding-004"
# Cosine similarity threshold for clustering (0.6 = reasonably related)
DEFAULT_SIMILARITY_THRESHOLD = 0.55


def get_embeddings(texts: List[str], api_key: str = None) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Gemini text-embedding-004.
    
    Args:
        texts: List of strings to embed
        api_key: Optional API key (falls back to GEMINI_API_KEY env var)
    
    Returns:
        List of embedding vectors (list of floats)
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not found. Set it in .env or pass api_key.")
    
    genai.configure(api_key=key)
    
    # Gemini embed_content supports batching
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=texts,
        task_type="CLUSTERING",
    )
    
    return result["embedding"]


def cluster_commits_by_similarity(
    commits: List[NormalizedCommit],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    api_key: str = None,
) -> List[List[NormalizedCommit]]:
    """
    Cluster commits by semantic similarity using embeddings + agglomerative clustering.
    
    Process:
    1. Generate embedding for each commit's title + message
    2. Compute pairwise cosine similarity matrix
    3. Apply agglomerative clustering with distance threshold
    4. Return groups of related commits
    
    Args:
        commits: List of NormalizedCommit objects to cluster
        similarity_threshold: Minimum cosine similarity to consider commits related (0.0-1.0)
        api_key: Optional Gemini API key
    
    Returns:
        List of commit groups (each group is a list of NormalizedCommit)
    """
    if len(commits) <= 1:
        return [commits] if commits else []
    
    # Build text representations for embedding
    texts = []
    for c in commits:
        # Combine title and message body for richer semantic signal
        text = c.title
        if c.message and c.message != c.title:
            # Avoid duplicating title in the text
            body = c.message.replace(c.title, "").strip()
            if body:
                text = f"{text} — {body[:200]}"  # Limit body length
        texts.append(text)
    
    # Generate embeddings
    embeddings = get_embeddings(texts, api_key=api_key)
    embedding_matrix = np.array(embeddings)
    
    # Compute cosine similarity → convert to distance
    sim_matrix = cosine_similarity(embedding_matrix)
    distance_matrix = 1 - sim_matrix
    # Clip negative distances (floating point artifacts)
    distance_matrix = np.clip(distance_matrix, 0, 2)
    
    # Agglomerative clustering with distance threshold
    # distance_threshold = 1 - similarity_threshold
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - similarity_threshold,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(distance_matrix)
    
    # Group commits by cluster label
    clusters_dict: dict[int, List[NormalizedCommit]] = {}
    for idx, label in enumerate(labels):
        clusters_dict.setdefault(label, []).append(commits[idx])
    
    return list(clusters_dict.values())
