CREATE TABLE IF NOT EXISTS chat_messages.messages_by_user (
    user_id UUID,
    created_at TIMESTAMP,
    message_id UUID,
    room_id UUID,
    content TEXT,
    edited BOOLEAN,
    updated_at TIMESTAMP,
    PRIMARY KEY (user_id, created_at)
) WITH CLUSTERING ORDER BY (created_at DESC);