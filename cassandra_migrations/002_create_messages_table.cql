CREATE TABLE IF NOT EXISTS chat_messages.messages (
    room_id UUID,
    created_at TIMESTAMP,
    id UUID,
    user_id UUID,
    content TEXT,
    edited BOOLEAN,
    updated_at TIMESTAMP,
    PRIMARY KEY (room_id, created_at)
) WITH CLUSTERING ORDER BY (created_at DESC);