from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Any
from urllib.parse import parse_qs, urlparse


ITEM_DETAIL_RE = re.compile(r"^/items/(?P<item_id>\d+)$")


@dataclass(slots=True)
class Response:
    status_code: int
    headers: dict[str, str]
    body: bytes


class InventoryApplication:
    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def handle_request(
        self,
        method: str,
        target: str,
        headers: dict[str, str] | Any,
        body: bytes,
    ) -> Response:
        parsed_url = urlparse(target)
        path = parsed_url.path or "/"
        accept = str(headers.get("Accept", "*/*"))

        if path == "/health/alive":
            return self._text_response(200, "OK")

        if path == "/health/ready":
            ready, message = self.repository.check_ready()
            return self._text_response(200 if ready else 500, "OK" if ready else message)

        if path == "/":
            if not self._prefers_html(accept):
                return self._text_response(406, "Only text/html is supported for /")
            return self._html_response(200, self._render_index())

        if path == "/items":
            if method == "GET":
                return self._handle_items_list(accept)
            if method == "POST":
                return self._handle_create_item(headers, body, accept)
            return self._text_response(405, "Method Not Allowed")

        match = ITEM_DETAIL_RE.fullmatch(path)
        if match:
            item_id = int(match.group("item_id"))
            if method == "GET":
                return self._handle_item_detail(item_id, accept)
            return self._text_response(405, "Method Not Allowed")

        return self._text_response(404, "Not Found")

    def _handle_items_list(self, accept: str) -> Response:
        items = self.repository.list_items()
        if self._prefers_html(accept):
            rows = "".join(
                f"<tr><td>{item['id']}</td><td>{escape(item['name'])}</td></tr>"
                for item in items
            )
            table_body = rows or "<tr><td colspan='2'>No items yet</td></tr>"
            html = (
                "<html><body>"
                "<h1>Inventory Items</h1>"
                "<table border='1'>"
                "<thead><tr><th>ID</th><th>Name</th></tr></thead>"
                f"<tbody>{table_body}</tbody>"
                "</table>"
                "</body></html>"
            )
            return self._html_response(200, html)
        if self._prefers_json(accept):
            return self._json_response(200, items)
        return self._text_response(406, "Only text/html and application/json are supported")

    def _handle_item_detail(self, item_id: int, accept: str) -> Response:
        item = self.repository.get_item(item_id)
        if item is None:
            return self._text_response(404, "Item not found")
        normalized = self._normalize_item(item)
        if self._prefers_html(accept):
            html = (
                "<html><body>"
                f"<h1>Item #{normalized['id']}</h1>"
                "<ul>"
                f"<li>ID: {normalized['id']}</li>"
                f"<li>Name: {escape(normalized['name'])}</li>"
                f"<li>Quantity: {normalized['quantity']}</li>"
                f"<li>Created at: {escape(normalized['created_at'])}</li>"
                "</ul>"
                "</body></html>"
            )
            return self._html_response(200, html)
        if self._prefers_json(accept):
            return self._json_response(200, normalized)
        return self._text_response(406, "Only text/html and application/json are supported")

    def _handle_create_item(self, headers: Any, body: bytes, accept: str) -> Response:
        try:
            payload = self._parse_payload(headers, body)
            name = str(payload["name"]).strip()
            quantity = int(payload["quantity"])
        except KeyError as exc:
            return self._text_response(400, f"Missing required field: {exc.args[0]}")
        except ValueError:
            return self._text_response(400, "quantity must be an integer")
        except json.JSONDecodeError:
            return self._text_response(400, "Request body is not valid JSON")

        if not name:
            return self._text_response(400, "name must not be empty")
        if quantity < 0:
            return self._text_response(400, "quantity must be zero or positive")

        item = self._normalize_item(self.repository.create_item(name, quantity))
        location = f"/items/{item['id']}"
        if self._prefers_html(accept):
            html = (
                "<html><body>"
                "<h1>Item created</h1>"
                f"<p>Created inventory item <strong>{escape(item['name'])}</strong>.</p>"
                f"<p><a href='{location}'>Open item details</a></p>"
                "</body></html>"
            )
            return self._html_response(201, html, extra_headers={"Location": location})
        if self._prefers_json(accept):
            return self._json_response(201, item, extra_headers={"Location": location})
        return self._text_response(406, "Only text/html and application/json are supported")

    def _parse_payload(self, headers: Any, body: bytes) -> dict[str, Any]:
        content_type = str(headers.get("Content-Type", "application/x-www-form-urlencoded"))
        if "application/json" in content_type:
            return json.loads(body.decode("utf-8") or "{}")
        form = parse_qs(body.decode("utf-8"))
        return {key: values[-1] for key, values in form.items()}

    def _render_index(self) -> str:
        return (
            "<html><body>"
            "<h1>mywebapp</h1>"
            "<p>Simple Inventory service endpoints:</p>"
            "<ul>"
            "<li>GET /items</li>"
            "<li>POST /items</li>"
            "<li>GET /items/&lt;id&gt;</li>"
            "</ul>"
            "</body></html>"
        )

    def _normalize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(item)
        created_at = normalized.get("created_at")
        if isinstance(created_at, datetime):
            normalized["created_at"] = created_at.isoformat(sep=" ")
        return normalized

    def _json_response(self, status_code: int, payload: Any, extra_headers: dict[str, str] | None = None) -> Response:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if extra_headers:
            headers.update(extra_headers)
        return Response(
            status_code=status_code,
            headers=headers,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    def _html_response(self, status_code: int, html: str, extra_headers: dict[str, str] | None = None) -> Response:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if extra_headers:
            headers.update(extra_headers)
        return Response(status_code=status_code, headers=headers, body=html.encode("utf-8"))

    def _text_response(self, status_code: int, text: str) -> Response:
        return Response(
            status_code=status_code,
            headers={"Content-Type": "text/plain; charset=utf-8"},
            body=text.encode("utf-8"),
        )

    @staticmethod
    def _prefers_html(accept: str) -> bool:
        accept_lower = accept.lower()
        return "text/html" in accept_lower or "*/*" in accept_lower or not accept_lower.strip()

    @staticmethod
    def _prefers_json(accept: str) -> bool:
        accept_lower = accept.lower()
        return "application/json" in accept_lower or "*/*" in accept_lower or not accept_lower.strip()
