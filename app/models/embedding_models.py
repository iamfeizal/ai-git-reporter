from sqlalchemy import Column, String, Integer, Text, Float
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class CommitEmbedding(Base):
    """
    Menyimpan embedding hasil klasifikasi commit untuk tujuan semantic clustering
    dan penelusuran riwayat laporan. Menggunakan pgvector.
    """
    __tablename__ = "commit_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    commit_short_id = Column(String(50), index=True, nullable=False)
    project_id = Column(String(100), index=True, nullable=False)
    
    # Metadata commit
    title = Column(String(500))
    message = Column(Text)
    
    # Kategori Level 1 & Level 2 yang telah diklasifikasikan
    category_level_1 = Column(String(50), index=True)
    category_level_2 = Column(String(50), index=True)
    
    # Vector Embedding (dimensi 768 untuk text-embedding-004 Gemini)
    embedding = Column(Vector(768))
