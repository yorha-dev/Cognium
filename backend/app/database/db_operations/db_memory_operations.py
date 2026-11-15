import traceback

from sqlmodel import Session, select
import numpy as np

from config import DbConfig, CONSTRAINT
from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from database.db_conn import get_engine
from database.db_schema import Memory

def create_memory(**data):
    mem = Memory(
        created_at=None, # implement
        modified_at=None, # implement
        used_model=data['used_model'],
        content=data['content'],
        embedding=data['embedding']
    )

    with Session(get_engine()) as session:
        session.add(mem)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description="Failed to save memory.",
                source="create_memory",
                traceback=traceback.format_exception(e)
            )

        session.refresh(mem)

        return mem.model_dump()

def update_memory(mem_id: int, **data):
    with Session(get_engine()) as session:
        mem = session.exec(select(Memory).where(
            Memory.id == mem_id
        )).one_or_none()

        mem.content = data['content']
        mem.embedding = data['embedding']
        mem.used_model = data['used_model']

        session.add(mem)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description="Failed to update memory.",
                source="update_memory",
                traceback=traceback.format_exception(e)
            )

        session.refresh(mem)

        return mem.model_dump()

def delete_memory(mem_id: int) -> bool:
    with Session(get_engine()) as session:
        mem = session.exec(select(Memory).where(
            Memory.id == mem_id
        )).one_or_none()

        if mem is None:
            return False

        session.delete(mem)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description="Failed to delete memory",
                source="delete_memory",
                traceback=traceback.format_exception(e)
            )

        return bool(session.get(Memory, mem.id))

def search_memory(query, top_k: int) -> list:
    with Session(get_engine()) as session:
        if DbConfig.DB_PERSISTENT in CONSTRAINT:
            memories = session.exec(select(Memory).order_by(
                # Common use is Memory.embedding.cosine_distance(...)
                # Used an alternative to avoid error lint on IDE
                Memory.__table__.columns.embedding.cosine_distance(query)).limit(top_k)
            ).all()

            return [memory.model_dump() for memory in memories]

        all_memories = session.exec(select(Memory)).all()

        scores = []

        for memory in all_memories:
            a = np.asarray(memory.embedding)
            b = np.asarray(query)

            similarity = np.dot(a, b) / (
                np.linalg.norm(a) * np.linalg.norm(b)
            )

            scores.append((similarity, memory))

        scores.sort(
            key=lambda x: x[0],
            reverse=True
        )

        memories = scores[:top_k]

        return [memory.model_dump() for _, memory in memories]
