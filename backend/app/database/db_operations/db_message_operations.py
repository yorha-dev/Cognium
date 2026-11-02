import traceback

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from error_handler import ErrorHandler
from database.db_conn import get_engine
from database.db_schema import Message, Chat, Attachment
from .db_document_operations import get_document_by_name

def add_message(chat_id: int, data):
    msg = Message(
        id=data['id'],
        role=data['role'],
        content=data['content'],
        timestamp=data['timestamp'],
        chat_id=chat_id
    )

    msg.attachments = []

    if data['attachments']:
        for att in data['attachments']:
            doc = get_document_by_name(att['name'])

            msg.attachments.append(
                Attachment(
                    message_id=data['id'],
                    document_id=doc['id']
                )
            )

    with Session(get_engine()) as session:
        result = session.exec(select(Chat).where(Chat.id == chat_id))

        msg.chat = result.one()

        session.add(msg)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                event_type="add_message",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
            )

        session.refresh(msg) # OPITIONAL

        result = session.exec(select(Message).where(
            Message.chat_id == chat_id, Message.id == msg.id
        )).one_or_none()

        return result.model_dump() if result else None

def update_message(chat_id: int, data):
    with Session(get_engine()) as session:
        msg = session.exec(select(Message).where(
            Message.chat_id == chat_id, Message.id == data['id']
        )).one_or_none()

        if msg is None:
            return None

        msg.role = data['role']
        msg.content = data['content']
        msg.timestamp = data['timestamp']

        if isinstance(data.get('attachments'), list):
            for att in data['attachments']:
                doc = get_document_by_name(att['name'])

                msg.attachments.append(
                    Attachment(
                        message_id=msg.id,
                        document_id=doc['id']
                    )
                )

        session.add(msg)

        try:
            session.commit()
        except Exception as e:
            session.rollback()

            ErrorHandler().register(
                event_type="update_message",
                error_type="DATABASE_COMMIT_ERROR",
                description=e,
                traceback=traceback.format_exc()
            )

        session.refresh(msg)

        return msg.model_dump()

def get_messages(chat_id: int) -> list:
    with Session(get_engine()) as session:
        msg_obj_list = session.exec(
            select(Message).where(
                Message.chat_id == chat_id
            ).options(
                selectinload(Message.attachments)
                .selectinload(Attachment.document)
            )
        ).all()

        return [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'timestamp': msg.timestamp,
            'attachments': [
                {
                    'id': att.document.id,
                    'name': att.document.name,
                    'size': att.document.size,
                    'uri': att.document.uri
                } for att in msg.attachments
            ]
        } for msg in msg_obj_list]

def get_message(chat_id: int, msg_id: int):
    with Session(get_engine()) as session:
        msg = session.exec(
            select(Message).where(
                Message.chat_id == chat_id,
                Message.id == msg_id
            )
        ).one_or_none()

        return msg.model_dump() if msg is not None else None
