import traceback

from sqlmodel import Session, select

from error_handler import ErrorHandler
from database.db_conn import get_engine
from database.db_schema import Summary, Document

def save_summary(document_id: int, **data):
    summary = Summary(
        document_id=document_id,
        text=data['text']
    )

    with Session(get_engine()) as session:
        session.add(summary)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                event_type="save_summary",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
            )

        session.refresh(summary)

        return summary.model_dump()

def get_summary(tag):
    summary = None
    with Session(get_engine()) as session:
        if tag.get('document_id', None):
            summary = session.exec(select(Summary).where(
                Summary.document_id == tag['document_id']
            )).one_or_none()
        elif tag.get('document_hash', None):
            result = session.exec(select(Document).where(
                Document.hash == tag['document_hash']
            )).one_or_none()

            summary = result.summary if result else None
        elif tag.get('document_name', None):
            result = session.exec(select(Document).where(
                Document.name == tag['document_name']
            )).one_or_none()

            summary = result.summary if result else None

        return summary.model_dump() if summary else None
