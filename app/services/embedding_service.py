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
from app.core.logger import logger

load_dotenv()

# Default embedding model
EMBEDDING_MODEL = "models/text-embedding-004"
# Cosine similarity threshold for clustering (0.6 = reasonably related)
DEFAULT_SIMILARITY_THRESHOLD = 0.55


from sqlalchemy.orm import Session
from app.models.embedding_models import CommitEmbedding

def get_embeddings(texts: List[str], api_key: str = None) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Gemini text-embedding-004.
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


def save_embeddings_to_db(commits: List[NormalizedCommit], embeddings: List[List[float]], db: Session):
    """Saves generated embeddings to pgvector database."""
    if not db:
        return
        
    try:
        # Note: in a real app, we should check if they already exist, but for now we just insert
        objects = []
        for c, emb in zip(commits, embeddings):
            objects.append(CommitEmbedding(
                commit_short_id=c.short_id,
                project_id=c.project_id if hasattr(c, 'project_id') else "unknown",
                title=c.title,
                message=c.message,
                embedding=emb
            ))
        db.bulk_save_objects(objects)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to save embeddings to db: {e}")


def cluster_commits_by_similarity(
    commits: List[NormalizedCommit],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    api_key: str = None,
    db: Session = None,
) -> List[List[NormalizedCommit]]:
    """
    Cluster commits by semantic similarity using embeddings + agglomerative clustering.
    """
    if len(commits) <= 1:
        return [commits] if commits else []
    
    # Build text representations for embedding
    texts = []
    for c in commits:
        text = c.title
        if c.message and c.message != c.title:
            body = c.message.replace(c.title, "").strip()
            if body:
                text = f"{text} — {body[:200]}"
        texts.append(text)
    
    # Generate embeddings
    embeddings = get_embeddings(texts, api_key=api_key)
    
    # Optionally save to pgvector database
    if db:
        save_embeddings_to_db(commits, embeddings, db)
        
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
