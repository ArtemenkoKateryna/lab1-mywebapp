from __future__ import annotations

import json
import unittest
from datetime import datetime

from mywebapp.application import InventoryApplication


class InMemoryInventoryRepository:
    def __init__(self) -> None:
        self.items = []
        self.next_id = 1

    def check_ready(self):
        return True, "OK"

    def list_items(self):
        return [{"id": item["id"], "name": item["name"]} for item in self.items]

    def get_item(self, item_id: int):
        for item in self.items:
            if item["id"] == item_id:
                return dict(item)
        return None

    def create_item(self, name: str, quantity: int):
        item = {
            "id": self.next_id,
            "name": name,
            "quantity": quantity,
            "created_at": datetime(2026, 1, 1, 12, 0, 0),
        }
        self.next_id += 1
        self.items.append(item)
        return dict(item)


class InventoryApplicationTests(unittest.TestCase):
    def setUp(self):
        self.app = InventoryApplication(InMemoryInventoryRepository())

    def test_root_returns_html(self):
        response = self.app.handle_request("GET", "/", {"Accept": "text/html"}, b"")
        self.assertEqual(response.status_code, 200)

    def test_items_json(self):
        self.app.repository.create_item("Laptop", 3)
        response = self.app.handle_request("GET", "/items", {"Accept": "application/json"}, b"")
        payload = json.loads(response.body.decode("utf-8"))
        self.assertEqual(payload, [{"id": 1, "name": "Laptop"}])


if __name__ == "__main__":
    unittest.main()
