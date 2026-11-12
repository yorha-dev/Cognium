import traceback

from sqlmodel import Session, select

from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from database.db_conn import get_engine
from database.db_schema import Document, Attachment

def create_document(data):
    doc = Document(
        id=data['id'],
        hash=data['hash'],
        name=data['name'],
        size=data['size'],
        uri=data['uri'],
        timestamp=data['timestamp']
    )

    with Session(get_engine()) as session:
        session.add(doc)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description=f"Failed to save document {data['name']}",
                source="create_document",
                traceback=traceback.format_exception(e)
            )

        session.refresh(doc)

        result = session.exec(select(Document).where(
            Document.id == doc.id
        )).one_or_none()

        return result.model_dump() if result else None

def update_document(file_name: str, new_data: str):
    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(
            Document.name == file_name
        )).one_or_none()

        if result is None:
            return None

        result.uri = new_data

        session.add(result)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description="Failed to update document",
                source="update_document",
                traceback=traceback.format_exception(e)
            )

        session.refresh(result)

        return result.model_dump()

def delete_document(data) -> bool:
    doc = None
    with Session(get_engine()) as session:
        if data.get('id', None):
            doc = session.exec(select(Document).where(
                Document.id == data['id']
            )).one_or_none()
        elif data.get('hash', None):
            doc = session.exec(select(Document).where(
                Document.hash == data['hash']
            )).one_or_none()
        elif data.get('name', None):
            doc = session.exec(select(Document).where(
                Document.name == data['name']
            )).one_or_none()

        if doc is None:
            return False

        session.delete(doc)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description=f"Failed to delete document {data}",
                source="delete_document",
                traceback=traceback.format_exception(e)
            )

        return bool(session.get(Document, doc.id))

def get_documents() -> list:
    with Session(get_engine()) as session:
        documents = session.exec(select(Document)).all()

        return [doc.model_dump() for doc in documents]

def get_document_by_name(name: str):
    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(
            Document.name == name
        )).one_or_none()

        return result.model_dump() if result else None

def get_document_by_hash(doc_hash: str):
    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(
            Document.hash == doc_hash
        )).one_or_none()

        return result.model_dump() if result else None

def get_documents_by_msg_id(msg_id: int) -> list:
    with Session(get_engine()) as session:
        atts = session.exec(select(Attachment).where(
            Attachment.message_id == msg_id
        )).all()

        return [att.document.model_dump() for att in atts]
