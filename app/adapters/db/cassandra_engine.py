import structlog
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine import connection

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

        logger.info("Cassandra connection initialized")

    @staticmethod
    def shutdown() -> None:
        connection.unregister_connection("default")
        logger.info("Cassandra connection closed.")
