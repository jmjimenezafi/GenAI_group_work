import pandas as pd
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

load_dotenv()
QDRANT_PATH = os.getenv("QDRANT_PATH", "../../data/qdrant")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(path=QDRANT_PATH)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.collection_name = "check_news_collection"

    def close(self) -> None:
        self.client.close()
        
    def create_collection(self):
        if self.collection_name not in self.client.get_collections().collections:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    def add_points(self, df: pd.DataFrame):
        points = []
        for _, row in df.iterrows():
            print(f"Processing claim ID {row['id']}")
            embedding = self.embedding_model.encode(row['claim']).tolist()
            print(f"Generated embedding for claim ID {row['id']}")
            point = PointStruct(
                id=str(row['id']),
                vector=embedding,
                payload={
                    "claim": row['claim'],
                    "veracity": row['veracity'],
                    "urls": row['urls'],
                    "reasoning": row['reasoning']

                }
            )
            points.append(point)
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query: str, top_k: int = 5):
        query_embedding = self.embedding_model.encode(query).tolist()
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
        )
