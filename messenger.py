# messenger.py
from flask_socketio import emit, join_room, leave_room

class Messenger:
    def __init__(self):
        self.messages = []  # In-memory store for messages (you can replace with a database)

    def get_messages(self):
        """
        Fetch all messages.
        """
        return self.messages

    def send_message(self, data):
        """
        Send a new message and store it.
        """
        message = {
            'sender': data['sender'],
            'receiver': data['receiver'],
            'message': data['message'],
            'timestamp': data['timestamp']
        }
        self.messages.append(message)
        return message

    def emit_message(self, socketio, message):
        """
        Emit the message to the receiver in real-time.
        """
        socketio.emit('new_message', message, room=message['receiver'])

    def join_chat(self, username):
        """
        Handle joining a chat room.
        """
        join_room(username)

    def leave_chat(self, username):
        """
        Handle leaving a chat room.
        """
        leave_room(username)



