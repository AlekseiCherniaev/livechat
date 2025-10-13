CREATE TABLE IF NOT EXISTS chat_messages.messages_by_id (
    id UUID PRIMARY KEY,
    room_id UUID,
    user_id UUID,
    content TEXT,
    created_at TIMESTAMP,
    edited BOOLEAN,
    updated_at TIMESTAMP
);
