import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.models import PointStruct, UpdateStatus
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from typing import List
import openai
from openai.embeddings_utils import get_embedding
from dotenv import load_dotenv, dotenv_values
import tiktoken


load_dotenv()  # take environment variables from .env.

config = dotenv_values(".env")
openai.api_key = config.get("OPENAI_API_KEY")


class QdrantVectorStore:

    def __init__(self,
                 host: str = config.get("QD_HOST"),
                 port: int = config.get("QD_PORT"),
                 #db_path: str = "/Users/het/qdrant/qdrant_storage",
                 collection_name: str = config.get("COLLECTION"),
                 vector_size: int = config.get("VECTOR_SIZE"),
                 vector_distance=Distance.COSINE
                 ):

        self.client = QdrantClient(
            url=host,
            port=port,
#            path=db_path
        )
        self.collection_name = collection_name

        try:
            collection_info = self.client.get_collection(collection_name=collection_name)
        except Exception as e:
            print("Collection does not exist, creating collection now")
            self.set_up_collection(collection_name,  vector_size, vector_distance)

    def set_up_collection(self, collection_name: str, vector_size: int, vector_distance: str):

        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=vector_distance)
        )

        collection_info = self.client.get_collection(collection_name=collection_name)

    def upsert_data(self, data: List[dict]):
        points = []
        for item in data:
            text = item.get("text")

            text_vector = get_embedding(text, engine=config.get("EMBEDDING"))
            text_id = str(uuid.uuid4())
            point = PointStruct(id=text_id, vector=text_vector, payload=item)
            points.append(point)

        operation_info = self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points)

        if operation_info.status == UpdateStatus.COMPLETED:
            print("Data inserted successfully!")
        else:
            print("Failed to insert data")

    def search(self, input_query: str, limit: int = config.get("QD_RESULTS")):
        input_vector = get_embedding(input_query, engine=config.get("EMBEDDING"))
        #text-embedding-ada-002
#curl --header 'Content-Type: application/json' -X POST -d '{"query": query goes here("Who is the author of.... ?)"}' http://127.0.0.1:5000/query
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=input_vector,
            limit=limit
        )

        result = []
        for item in search_result:
            similarity_score = item.score
            payload = item.payload
            data = {"id": item.id, "similarity_score": similarity_score, "text": payload.get("text")}
            result.append(data)

        return result


    def search_with_filter(self, input_query: str, filter: dict, limit: int = 3):
        input_vector = get_embedding(input_query, engine=config.get("EMBEDDING"))
        filter_list = []
        for key, value in filter.items():
            filter_list.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )

        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=input_vector,
            query_filter=Filter(
                must=filter_list
            ),
            limit=limit
        )

        result = []
        for item in search_result:
            similarity_score = item.score
            payload = item.payload
            data = {"id": item.id, "similarity_score": similarity_score, "quote": payload.get("quote"),
                    "person": payload.get("person")}
            result.append(data)

        return result

    def delete(self, text_ids: list):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(
                points=text_ids,
            )
        )

    def delete_collection(self, collection_name: str):
        self.client.delete_collection(collection_name=collection_name)
        print("collection deleted")

    def get_collection(self, collection_name: str):
        return self.client.get_collection(collection_name=collection_name)
    
    def docs_to_chunks(self, documents):
        chunks = []
        for doc in documents:
            document_chunks = self.chunk_tokens(doc)
            chunks.extend(document_chunks)

        return chunks
    
    def chunk_tokens(self, document: str, token_limit: int = 200):
        tokenizer = tiktoken.get_encoding(
            "cl100k_base"
        )

        chunks = []
        tokens = tokenizer.encode(document, disallowed_special=())

        while tokens:
            chunk = tokens[:token_limit]
            chunk_text = tokenizer.decode(chunk)
            last_punctuation = max(
                chunk_text.rfind("."),
                chunk_text.rfind("?"),
                chunk_text.rfind("!"),
                chunk_text.rfind("\n"),
            )
            if last_punctuation != -1:
                chunk_text = chunk_text[: last_punctuation + 1]
            cleaned_text = chunk_text.replace("\n", " ").strip()

            if cleaned_text and (not cleaned_text.isspace()):
                chunks.append(
                    {"text": cleaned_text}
                )

            tokens = tokens[len(tokenizer.encode(chunk_text, disallowed_special=())):]

        return chunks


