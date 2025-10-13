from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os
import glob

CONTACT_POINT = os.getenv("CASSANDRA_CONTACT_POINT", "cassandra")
USER = os.getenv("CASSANDRA_USER")
PASSWORD = os.getenv("CASSANDRA_PASSWORD")

auth_provider = None
if USER and PASSWORD:
    auth_provider = PlainTextAuthProvider(username=USER, password=PASSWORD)

cluster = Cluster([CONTACT_POINT], auth_provider=auth_provider)
session = cluster.connect()

for f in sorted(glob.glob("cassandra_migrations/*.cql")):
    print(f"Applying migration: {f}")
    with open(f) as file:
        session.execute(file.read())

print("All migrations applied")
cluster.shutdown()
