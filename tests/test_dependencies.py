"""Offline compatibility checks for the locked dependency graph.

Only external Todoist I/O is replaced; TwiML, JWT, requests serialization,
and the handler's priority mapping execute real library/application code.
"""
import importlib
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

import jwt
import requests
from pytodoist import todoist


class DependencyCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(os.environ, {
            "TODOIST_API_KEY": "offline-test-token",
            "TODOIST_PROJECT": "Inbox & errands",
        }):
            cls.app = importlib.import_module("main")

    def test_sms_priorities_and_real_twiml_response(self):
        for body, text, priority in [
            ("Buy milk", "Buy milk", todoist.Priority.LOW),
            ("!  Buy milk", "Buy milk", todoist.Priority.HIGH),
            ("!!  Buy milk", "Buy milk", todoist.Priority.VERY_HIGH),
            ("Call café <tomorrow>", "Call café <tomorrow>", todoist.Priority.LOW),
        ]:
            with self.subTest(body=body):
                calls = []
                project = SimpleNamespace(
                    name="Inbox & errands",
                    add_task=lambda text, **kwargs: calls.append((text, kwargs)),
                )
                user = SimpleNamespace(get_project=lambda name: project)
                request = SimpleNamespace(values={"From": "+15555550100", "Body": body})
                with patch.object(todoist, "login_with_api_token", return_value=user) as login:
                    xml, status, headers = self.app.add_task(request)
                login.assert_called_once_with("offline-test-token")
                self.assertEqual(calls, [(text, {"priority": priority})])
                self.assertEqual(status, 200)
                self.assertEqual(headers, {"Content-Type": "application/xml"})
                response = ET.fromstring(xml)
                self.assertEqual(response.tag, "Response")
                self.assertEqual(response.findtext("Message"),
                                 "Thanks, your task has been added to Inbox & errands")

    def test_todoist_requests_serializes_task_with_updated_transport(self):
        captured = []

        def send(session, request, **kwargs):
            captured.append(request)
            response = requests.Response()
            response.status_code = 200
            response._content = json.dumps({"id": 123, "content": "Buy café & milk"}).encode()
            response.headers["Content-Type"] = "application/json"
            response.request = request
            return response

        with patch.object(requests.Session, "send", send):
            response = todoist.API.add_item(
                "offline-test-token", "Buy café & milk", project_id=42, priority=4)
        self.assertEqual(response.json()["id"], 123)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].method, "POST")
        form = parse_qs(urlsplit(captured[0].url).query)
        self.assertEqual(form["content"], ["Buy café & milk"])
        self.assertEqual(form["project_id"], ["42"])
        self.assertEqual(form["priority"], ["4"])

    def test_pyjwt_signs_and_verifies_and_rejects_wrong_key(self):
        key = "offline-test-signing-key-32-bytes-long"
        encoded = jwt.encode({"sub": "offline-user"}, key, algorithm="HS256")
        self.assertIsInstance(encoded, str)
        self.assertEqual(jwt.decode(encoded, key, algorithms=["HS256"])["sub"], "offline-user")
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(encoded, "different-test-key-32-bytes-long!!", algorithms=["HS256"])


if __name__ == "__main__":
    unittest.main()
