import traceback

from sqlmodel import Session, select

from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from database.db_conn import get_engine
from database.db_schema import Chat

def add_chat(title: str = None):
    new_chat = Chat(title=title)

    with Session(get_engine()) as session:
        session.add(new_chat)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description=f"Failed to save chat {title if title else ''}",
                source="add_chat",
                traceback=traceback.format_exception(e)
            )

        session.refresh(new_chat)

    return new_chat.model_dump()

def update_chat(chat_id: int, title):
    with Session(get_engine()) as session:
        result = session.exec(select(Chat).where(Chat.id == chat_id))
        chat = result.one_or_none()

        if chat is None:
            return None

        chat.title = title

        session.add(chat)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description=f"Failed to update chat {chat_id}",
                source="update_chat",
                traceback=traceback.format_exception(e)
            )

        session.refresh(chat)

        return chat.model_dump()

def delete_chat(chat_id: int) -> bool:
    with Session(get_engine()) as session:
        statement = select(Chat).where(Chat.id == chat_id)
        result = session.exec(statement)
        session.delete(result.one())

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                code="DATABASE_COMMIT_ERROR",
                detail=str(e),
                description=f'Failed to delete chat {chat_id}',
                source="delete_chat",
                traceback=traceback.format_exception(e)
            )

        return bool(session.get(Chat, chat_id) is None)

def get_chats() -> list:
    with Session(get_engine()) as session:
        chat_list = session.exec(select(Chat)).all()

        return [chat.model_dump() for chat in chat_list]

def get_chat(chat_id: int):
    with Session(get_engine()) as session:
        statement = select(Chat).where(Chat.id == chat_id)
        result = session.exec(statement)

        chat = result.first()

        return chat.model_dump() if chat is not None else None
