import traceback

from sqlmodel import Session, select
import numpy as np

from config import DbConfig, CONSTRAINT
from error_handler import ErrorHandler
from database.db_conn import get_engine
from database.db_schema import Chunk, Document

def save_chunk(document_id: int, data):
    chunk = Chunk(
        id=None,
        document_id=document_id,
        page=data['page'],
        section=data['section'],
        model=data['model'],
        index=data['index'],
        text=data['text'],
        embedding=data['embedding']
    )

    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(Document.id == document_id))

        chunk.document = result.one()

        session.add(chunk)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                event_type="save_chunk",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
            )

        return chunk.model_dump()

def delete_chunks(document_id: int) -> None:
    with Session(get_engine()) as session:
        chunks = session.exec(select(Chunk).where(
            Chunk.document_id == document_id
        )).all()

        session.delete(chunks)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                event_type="delete_chunk",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
            )

def get_chunk(document_id: int, index: int):
    with Session(get_engine()) as session:
        result = session.exec(select(Chunk).where(
            Chunk.document_id == document_id, Chunk.index == index
        )).one_or_none()

        return result.model_dump() if result else None

def get_chunks(document_id: int) -> list:
    with Session(get_engine()) as session:
        chunks = session.exec(select(Chunk).where(Chunk.document_id  == document_id)).all()

        if chunks is None:
            return None

        return [chunk.model_dump() for chunk in chunks]

def chunk_similarity_search(document_id: int, query, top_k: int) -> list:
    with Session(get_engine()) as session:
        if DbConfig.DB_PERSISTANT in CONSTRAINT:
            chunks = session.exec(select(Chunk).where(
                Chunk.document_id == document_id
            ).order_by(
                # Common use is Chunk.embedding.cosine_distance(...)
                # Used an alternative to avoid error lint on IDE
                Chunk.__table__.columns.embedding.cosine_distance(query)).limit(top_k)
            ).all()

            return [chunk.model_dump() for chunk in chunks]
        else:
            all_chunks = session.exec(select(Chunk).where(
                Chunk.document_id == document_id
            )).all()

            scores = []

            for chunk in all_chunks:
                a = np.asarray(chunk.embedding)
                b = np.asarray(query)

                similarity = np.dot(a, b) / (
                    np.linalg.norm(a) * np.linalg.norm(b)
                )

                scores.append((similarity, chunk))

            scores.sort(
                key=lambda x: x[0],
                reverse=True
            )

            chunks = scores[:top_k]

            return [chunk.model_dump() for _, chunk in chunks]
