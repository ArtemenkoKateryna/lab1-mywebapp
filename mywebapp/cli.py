from __future__ import annotations

from mywebapp.application import InventoryApplication
from mywebapp.config import build_parser, settings_from_namespace
from mywebapp.database import DatabaseConfig, MariaDBInventoryRepository
from mywebapp.server import run_server


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = settings_from_namespace(args)

    repository = MariaDBInventoryRepository(
        DatabaseConfig(
            host=settings.db_host,
            port=settings.db_port,
            name=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            connect_timeout=settings.db_connect_timeout,
        )
    )

    if args.command == "migrate":
        repository.migrate()
        return 0

    application = InventoryApplication(repository)
    run_server(
        host=settings.host,
        port=settings.port,
        application=application,
        listen_fd=settings.listen_fd,
    )
    return 0
