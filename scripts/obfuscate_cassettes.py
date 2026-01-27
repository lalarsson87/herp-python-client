#!/usr/bin/env python3
"""
Obfuscate sensitive personal data in VCR cassettes

This script replaces PII (Personally Identifiable Information) in recorded
VCR cassettes with fake/anonymized data to protect candidate privacy.
"""

import json
import re
import yaml
from pathlib import Path
from typing import Any, Dict
import hashlib


class CassetteObfuscator:
    """Obfuscate sensitive data in VCR cassettes"""

    def __init__(self):
        # Cache for consistent replacements
        self.name_cache: Dict[str, str] = {}
        self.email_cache: Dict[str, str] = {}
        self.phone_cache: Dict[str, str] = {}
        self.company_cache: Dict[str, str] = {}
        self.counter = 1000

    def _hash_to_id(self, value: str) -> int:
        """Generate consistent numeric ID from hash"""
        return int(hashlib.md5(value.encode()).hexdigest()[:8], 16) % 10000

    def obfuscate_name(self, name: str) -> str:
        """Replace name with anonymized version"""
        if not name or name in self.name_cache:
            return self.name_cache.get(name, name)

        # Generate consistent candidate ID
        candidate_id = self._hash_to_id(name)
        fake_name = f"Candidate_{candidate_id}"
        self.name_cache[name] = fake_name
        return fake_name

    def obfuscate_email(self, email: str) -> str:
        """Replace email with fake email"""
        if not email or email in self.email_cache:
            return self.email_cache.get(email, email)

        email_id = self._hash_to_id(email)
        fake_email = f"candidate{email_id}@example.com"
        self.email_cache[email] = fake_email
        return fake_email

    def obfuscate_phone(self, phone: str) -> str:
        """Replace phone number with fake number"""
        if not phone or phone in self.phone_cache:
            return self.phone_cache.get(phone, phone)

        # Keep format, replace digits
        phone_id = self._hash_to_id(phone)

        # Japanese format: 080-XXXX-XXXX or 070-XXXX-XXXX
        if re.match(r"0[7-9]0-\d{4}-\d{4}", phone):
            fake_phone = f"080-{phone_id:04d}-{(phone_id * 7) % 10000:04d}"
        # International format
        elif phone.startswith("+"):
            fake_phone = f"+81-0{phone_id % 10000000000:010d}"
        else:
            fake_phone = f"000-0000-{phone_id % 10000:04d}"

        self.phone_cache[phone] = fake_phone
        return fake_phone

    def obfuscate_company(self, company: str) -> str:
        """Replace company name with generic name"""
        if not company or company in self.company_cache:
            return self.company_cache.get(company, company)

        company_id = self._hash_to_id(company)
        fake_company = f"Company_{company_id}"
        self.company_cache[company] = fake_company
        return fake_company

    def obfuscate_text(self, text: str) -> str:
        """Obfuscate text content (career histories, notes, etc.)"""
        if not text:
            return text

        # Replace email addresses
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            lambda m: self.obfuscate_email(m.group(0)),
            text,
        )

        # Replace phone numbers (Japanese format)
        text = re.sub(
            r"0[7-9]0-\d{4}-\d{4}", lambda m: self.obfuscate_phone(m.group(0)), text
        )

        # Replace international phone format
        text = re.sub(
            r"\+\d{1,3}-\d{10,11}", lambda m: self.obfuscate_phone(m.group(0)), text
        )

        # Replace URLs with personal identifiers (Google Drive links)
        text = re.sub(
            r"https://drive\.google\.com/drive/folders/[A-Za-z0-9_-]+",
            "https://drive.google.com/drive/folders/REDACTED",
            text,
        )

        return text

    def obfuscate_candidacy(self, candidacy: Dict[str, Any]) -> Dict[str, Any]:
        """Obfuscate a single candidacy object"""
        if "name" in candidacy:
            candidacy["name"] = self.obfuscate_name(candidacy["name"])

        if "email" in candidacy:
            candidacy["email"] = self.obfuscate_email(candidacy["email"])

        if "telephoneNumber" in candidacy:
            candidacy["telephoneNumber"] = self.obfuscate_phone(
                candidacy["telephoneNumber"]
            )

        if "company" in candidacy:
            candidacy["company"] = self.obfuscate_company(candidacy["company"])

        # Obfuscate text fields
        for field in ["note", "career", "education"]:
            if field in candidacy:
                candidacy[field] = self.obfuscate_text(candidacy[field])

        # Obfuscate channel agent info
        if "channel" in candidacy and isinstance(candidacy["channel"], dict):
            channel = candidacy["channel"]
            if "agent" in channel and isinstance(channel["agent"], dict):
                agent = channel["agent"]
                if "name" in agent:
                    agent["name"] = self.obfuscate_name(agent["name"])
                if "company" in agent:
                    agent["company"] = self.obfuscate_company(agent["company"])

        return candidacy

    def obfuscate_response_body(self, body: str) -> str:
        """Obfuscate JSON response body"""
        try:
            data = json.loads(body)

            # Handle candidacies list
            if "candidacies" in data and isinstance(data["candidacies"], list):
                data["candidacies"] = [
                    self.obfuscate_candidacy(c) for c in data["candidacies"]
                ]

            # Handle single candidacy
            elif "id" in data and "name" in data:
                data = self.obfuscate_candidacy(data)

            # Handle contacts
            if "contacts" in data and isinstance(data["contacts"], list):
                for contact in data["contacts"]:
                    if "title" in contact:
                        contact["title"] = self.obfuscate_text(contact["title"])
                    if "notes" in contact:
                        contact["notes"] = self.obfuscate_text(contact["notes"])

            return json.dumps(data, ensure_ascii=False)

        except json.JSONDecodeError:
            # If not JSON, just obfuscate as text
            return self.obfuscate_text(body)

    def obfuscate_cassette(self, cassette_path: Path) -> None:
        """Obfuscate a VCR cassette file"""
        print(f"Obfuscating {cassette_path.name}...")

        with open(cassette_path, "r", encoding="utf-8") as f:
            cassette = yaml.safe_load(f)

        if "interactions" not in cassette:
            print(f"  ⚠️  No interactions found, skipping")
            return

        # Obfuscate each interaction
        for interaction in cassette["interactions"]:
            if "response" in interaction and "body" in interaction["response"]:
                body = interaction["response"]["body"]
                if isinstance(body, dict) and "string" in body:
                    body["string"] = self.obfuscate_response_body(body["string"])

        # Write back
        with open(cassette_path, "w", encoding="utf-8") as f:
            yaml.dump(cassette, f, allow_unicode=True, default_flow_style=False)

        print(f"  ✅ Obfuscated successfully")

    def obfuscate_all_cassettes(self, cassettes_dir: Path) -> None:
        """Obfuscate all cassettes in directory"""
        cassette_files = list(cassettes_dir.glob("*.yaml"))

        if not cassette_files:
            print(f"No cassette files found in {cassettes_dir}")
            return

        print(f"Found {len(cassette_files)} cassette files")
        print()

        for cassette_path in cassette_files:
            self.obfuscate_cassette(cassette_path)

        print()
        print(f"✅ Obfuscated {len(cassette_files)} cassettes")
        print(f"   - {len(self.name_cache)} names")
        print(f"   - {len(self.email_cache)} emails")
        print(f"   - {len(self.phone_cache)} phone numbers")
        print(f"   - {len(self.company_cache)} companies")


def main():
    """Main entry point"""
    cassettes_dir = (
        Path(__file__).parent.parent
        / "tests"
        / "integration"
        / "fixtures"
        / "cassettes"
    )

    if not cassettes_dir.exists():
        print(f"❌ Cassettes directory not found: {cassettes_dir}")
        return 1

    obfuscator = CassetteObfuscator()
    obfuscator.obfuscate_all_cassettes(cassettes_dir)

    return 0


if __name__ == "__main__":
    exit(main())
