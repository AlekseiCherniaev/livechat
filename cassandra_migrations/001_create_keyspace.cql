CREATE KEYSPACE IF NOT EXISTS messages
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};