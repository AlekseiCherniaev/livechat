CREATE KEYSPACE IF NOT EXISTS livechat
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};