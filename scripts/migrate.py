import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mywebapp.config import build_parser, settings_from_namespace
from mywebapp.database import DatabaseConfig, MariaDBInventoryRepository


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args(["migrate", *sys.argv[1:]])
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
    repository.migrate()
    raise SystemExit(0)
