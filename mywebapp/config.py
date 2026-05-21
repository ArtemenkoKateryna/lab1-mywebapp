from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    host: str
    port: int
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_connect_timeout: int = 5
    listen_fd: int | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mywebapp",
        description="Simple Inventory service for Lab 1.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("serve", "migrate"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--host", default="127.0.0.1")
        subparser.add_argument("--port", type=int, default=3000)
        subparser.add_argument("--db-host", required=True)
        subparser.add_argument("--db-port", type=int, default=3306)
        subparser.add_argument("--db-name", required=True)
        subparser.add_argument("--db-user", required=True)
        subparser.add_argument("--db-password", required=True)
        subparser.add_argument("--db-connect-timeout", type=int, default=5)
        if command == "serve":
            subparser.add_argument("--listen-fd", type=int, default=None)

    return parser


def settings_from_namespace(namespace: argparse.Namespace) -> Settings:
    return Settings(
        host=namespace.host,
        port=namespace.port,
        db_host=namespace.db_host,
        db_port=namespace.db_port,
        db_name=namespace.db_name,
        db_user=namespace.db_user,
        db_password=namespace.db_password,
        db_connect_timeout=namespace.db_connect_timeout,
        listen_fd=getattr(namespace, "listen_fd", None),
    )
