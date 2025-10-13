import structlog
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table, create_keyspace_simple

from app.adapters.db.models.cassandra_message import MessageModel
from app.core.settings import get_settings

logger = structlog.getLogger(__name__)


class CassandraEngine:
    def __init__(self) -> None:
        auth_provider = None
        if get_settings().cassandra_user and get_settings().cassandra_password:
            auth_provider = PlainTextAuthProvider(
                username=get_settings().cassandra_user,
                password=get_settings().cassandra_password,
            )
        connection.setup(
            [get_settings().cassandra_contact_point],
            get_settings().cassandra_keyspace,
            protocol_version=4,
            auth_provider=auth_provider,
        )

        create_keyspace_simple(get_settings().cassandra_keyspace, replication_factor=1)
        sync_table(MessageModel)

        logger.info("Cassandra connected and MessageModel synchronized")

    @staticmethod
    def shutdown() -> None:
        connection.unregister_connection("default")
        logger.info("Cassandra connection closed.")
