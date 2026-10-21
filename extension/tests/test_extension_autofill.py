"""
Unit and Evaluation Tests for HireIQ Chrome Extension Autofill Engine.

Evaluates field detection accuracy against realistic ATS forms:
- Lever Application Form
- Greenhouse Application Form
- Workday Multi-step Application Form
"""

import os
import re
from html.parser import HTMLParser
from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class MiniDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = {"tag": "root", "attrs": {}, "parent": None, "children": [], "text": []}
        self.stack = [self.root]
        self.inputs = []
        self.labels = {}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        node = {
            "tag": tag,
            "attrs": attr_dict,
            "parent": self.stack[-1],
            "children": [],
            "text": [],
        }
        self.stack[-1]["children"].append(node)
        if tag in ("input", "textarea", "select"):
            self.inputs.append(node)

        # Do not push self-closing tags onto stack
        if tag not in ("input", "img", "br", "hr", "meta", "link"):
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag not in ("input", "img", "br", "hr", "meta", "link"):
            if self.stack and self.stack[-1]["tag"] == tag:
                popped = self.stack.pop()
                if popped["tag"] == "label":
                    for_attr = popped["attrs"].get("for")
                    if for_attr:
                        self.labels[for_attr.lower()] = " ".join(popped["text"])

    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned:
            self.stack[-1]["text"].append(cleaned)


def get_node_text(node):
    parts = list(node.get("text", []))
    for child in node.get("children", []):
        parts.append(get_node_text(child))
    return " ".join(parts).strip()


def detect_field_type(input_node, labels_dict=None):
    """
    Python mirror of detection logic in extension/content_script.js
    """
    labels_dict = labels_dict or {}
    attrs = input_node["attrs"]
    tag = input_node["tag"]
    field_type = attrs.get("type", "text").lower() if tag == "input" else tag
    name = attrs.get("name", "").lower()
    fid = attrs.get("id", "").lower()
    autocomplete = attrs.get("autocomplete", "").lower()
    automation_id = attrs.get("data-automation-id", "").lower()
    placeholder = attrs.get("placeholder", "").lower()
    aria_label = attrs.get("aria-label", "").lower()

    # Guardrails: Never fill passwords, submit buttons, checkboxes, radio, hidden
    if field_type in ["password", "submit", "button", "checkbox", "radio", "hidden"]:
        return None

    # Retrieve container text
    parent = input_node.get("parent")
    container_text = get_node_text(parent).lower() if parent else ""

    # Label text
    label_text = labels_dict.get(fid, "").lower()

    # Resume file upload detection
    if field_type == "file":
        desc = f"{name} {fid} {automation_id} {label_text} {container_text}".lower()
        if any(k in desc for k in ["resume", "cv", "attachment", "file-upload"]):
            return {"fieldKey": "resume_file", "confidence": "high"}
        return None

    # LAYER 1: Standard Autocomplete, Name, ID
    if autocomplete == "email" or name == "email" or fid == "email":
        return {"fieldKey": "email", "confidence": "high"}
    if autocomplete == "tel" or name == "phone" or fid == "phone":
        return {"fieldKey": "phone", "confidence": "high"}
    if autocomplete == "given-name" or name == "first_name" or fid == "first_name":
        return {"fieldKey": "first_name", "confidence": "high"}
    if autocomplete == "family-name" or name == "last_name" or fid == "last_name":
        return {"fieldKey": "last_name", "confidence": "high"}
    if autocomplete == "name" or name == "name" or fid == "name":
        return {"fieldKey": "full_name", "confidence": "high"}

    # LAYER 2 & 3: Combined Descriptors
    combined = f"{automation_id} {autocomplete} {name} {fid} {aria_label} {placeholder} {label_text} {container_text[:200]}".lower()

    # Safety: Skip password or verification
    if any(k in combined for k in ["password", "confirm email", "verify email"]):
        return None

    # Workday Automation IDs
    if "legalnamesection_firstname" in automation_id or "firstname" in automation_id:
        return {"fieldKey": "first_name", "confidence": "high"}
    if "legalnamesection_lastname" in automation_id or "lastname" in automation_id:
        return {"fieldKey": "last_name", "confidence": "high"}
    if "phone-number" in automation_id or "phone" in automation_id:
        return {"fieldKey": "phone", "confidence": "high"}
    if "addresssection_city" in automation_id or "city" in automation_id:
        return {"fieldKey": "city", "confidence": "high"}
    if "linkedin" in automation_id:
        return {"fieldKey": "linkedin", "confidence": "high"}
    if "portfolio" in automation_id or "website" in automation_id:
        return {"fieldKey": "portfolio", "confidence": "high"}

    # General Regex Synonyms
    if re.search(r"\b(first[\s_-]?name|given[\s_-]?name|forename)\b", combined):
        return {"fieldKey": "first_name", "confidence": "medium"}
    if re.search(r"\b(last[\s_-]?name|family[\s_-]?name|surname)\b", combined):
        return {"fieldKey": "last_name", "confidence": "medium"}
    if re.search(r"\b(full[\s_-]?name|your name|candidate name)\b", combined):
        return {"fieldKey": "full_name", "confidence": "medium"}
    if re.search(r"\b(e[\s_-]?mail|email address)\b", combined):
        return {"fieldKey": "email", "confidence": "high"}
    if re.search(r"\b(phone|mobile|cell|contact number|telephone)\b", combined):
        return {"fieldKey": "phone", "confidence": "medium"}
    if re.search(r"\b(linkedin|linked in)\b", combined):
        return {"fieldKey": "linkedin", "confidence": "high"}
    if re.search(r"\b(github|git hub)\b", combined):
        return {"fieldKey": "github", "confidence": "high"}
    if re.search(r"\b(portfolio|website|personal site)\b", combined):
        return {"fieldKey": "portfolio", "confidence": "medium"}
    if re.search(r"\b(city|current location|address|location)\b", combined):
        return {"fieldKey": "city", "confidence": "medium"}
    if re.search(r"\b(current company|current employer|organization|org)\b", combined):
        return {"fieldKey": "company", "confidence": "medium"}

    return None


def parse_fixture(filename: str):
    path = FIXTURES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    parser = MiniDOMParser()
    parser.feed(html)
    return parser.inputs, parser.labels


def test_lever_form_autofill():
    inputs, labels = parse_fixture("lever_form.html")
    assert len(inputs) > 0

    detected = {}
    for inp in inputs:
        match = detect_field_type(inp, labels)
        if match:
            detected[match["fieldKey"]] = match

    required = ["full_name", "email", "phone", "company", "linkedin", "github", "portfolio", "resume_file"]
    for req in required:
        assert req in detected, f"Lever form missed field: {req}"

    success_rate = (len(detected) / len(required)) * 100
    print(f"\n[EVALUATION] Lever ATS Autofill Accuracy: {success_rate:.1f}% ({len(detected)}/{len(required)})")
    assert success_rate >= 100.0


def test_greenhouse_form_autofill():
    inputs, labels = parse_fixture("greenhouse_form.html")
    assert len(inputs) > 0

    detected = {}
    for inp in inputs:
        match = detect_field_type(inp, labels)
        if match:
            detected[match["fieldKey"]] = match

    required = ["first_name", "last_name", "email", "phone", "city", "linkedin", "github", "resume_file"]
    for req in required:
        assert req in detected, f"Greenhouse form missed field: {req}"

    success_rate = (len(detected) / len(required)) * 100
    print(f"\n[EVALUATION] Greenhouse ATS Autofill Accuracy: {success_rate:.1f}% ({len(detected)}/{len(required)})")
    assert success_rate >= 100.0


def test_workday_form_autofill():
    inputs, labels = parse_fixture("workday_form.html")
    assert len(inputs) > 0

    detected = {}
    for inp in inputs:
        match = detect_field_type(inp, labels)
        if match:
            detected[match["fieldKey"]] = match

    required = ["first_name", "last_name", "email", "phone", "city", "linkedin", "portfolio", "resume_file"]
    for req in required:
        assert req in detected, f"Workday form missed field: {req}"

    success_rate = (len(detected) / len(required)) * 100
    print(f"\n[EVALUATION] Workday ATS Autofill Accuracy: {success_rate:.1f}% ({len(detected)}/{len(required)})")
    assert success_rate >= 100.0


def test_safety_guardrails_prevent_accidental_fills():
    # Passwords and submit buttons must NEVER be matched
    password_node = {"tag": "input", "attrs": {"type": "password", "name": "user_password"}, "parent": None}
    assert detect_field_type(password_node) is None

    submit_node = {"tag": "input", "attrs": {"type": "submit", "value": "Submit Application"}, "parent": None}
    assert detect_field_type(submit_node) is None

    checkbox_node = {"tag": "input", "attrs": {"type": "checkbox", "name": "agree_terms"}, "parent": None}
    assert detect_field_type(checkbox_node) is None
