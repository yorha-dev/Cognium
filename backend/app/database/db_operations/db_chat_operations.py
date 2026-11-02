import traceback

from sqlmodel import Session, select

from error_handler import ErrorHandler
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
                event_type="add_chat",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
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
                event_type="update_chat",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
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
                event_type="delete_chat",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
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
