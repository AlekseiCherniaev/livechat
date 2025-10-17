CREATE TABLE IF NOT EXISTS livechat.messages (
    room_id UUID,
    created_at timestamp,
    id UUID,
    user_id UUID,
    content text,
    edited boolean,
    updated_at timestamp,
    PRIMARY KEY (room_id, created_at)
) WITH CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS livechat.messages_by_user (
    user_id UUID,
    created_at timestamp,
    message_id UUID,
    room_id UUID,
    content text,
    edited boolean,
    updated_at timestamp,
    PRIMARY KEY (user_id, created_at)
) WITH CLUSTERING ORDER BY (created_at DESC);

CREATE TABLE IF NOT EXISTS livechat.messages_by_id (
    id UUID PRIMARY KEY,
    room_id UUID,
    user_id UUID,
    content text,
    created_at timestamp,
    edited boolean,
    updated_at timestamp
);

CREATE TABLE IF NOT EXISTS livechat.messages_global (
    partition text,
    created_at timestamp,
    id UUID,
    room_id UUID,
    user_id UUID,
    content text,
    edited boolean,
    updated_at timestamp,
    PRIMARY KEY (partition, created_at, id)
) WITH CLUSTERING ORDER BY (created_at DESC, id DESC);