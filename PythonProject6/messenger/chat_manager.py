from .database import Chat, Message, User
from django.db.models import Q

def create_chat(participant_ids, chat_type='private', name=None):
    if chat_type == 'private' and len(participant_ids) != 2:
        raise ValueError("Private chat must have exactly 2 participants")
    chat = Chat.objects.create(chat_type=chat_type, name=name)
    chat.participants.set(participant_ids)
    chat.save()
    return chat

def send_message(chat_id, sender_id, text):
    chat = Chat.objects.get(id=chat_id)
    sender = User.objects.get(id=sender_id)
    if sender not in chat.participants.all():
        raise PermissionError("User not in chat")
    message = Message.objects.create(chat=chat, sender=sender, text=text)
    return message

def get_messages(chat_id, limit=50):
    chat = Chat.objects.get(id=chat_id)
    return chat.messages.order_by('-timestamp')[:limit]

def get_user_chats(user_id):
    user = User.objects.get(id=user_id)
    return user.chats.all()