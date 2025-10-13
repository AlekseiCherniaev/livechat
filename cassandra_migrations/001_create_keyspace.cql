CREATE KEYSPACE IF NOT EXISTS chat_messages
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};