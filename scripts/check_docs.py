#!/usr/bin/env python3
"""
Documentation validation script

Checks:
- Spelling errors
- Broken internal links
- Consistent formatting
- Code block syntax
- Heading hierarchy
"""

import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

# Common technical terms that spell checkers flag
ALLOWED_TERMS = {
    "herp",
    "api",
    "async",
    "await",
    "httpx",
    "sync",
    "candidacy",
    "candidacies",
    "requisition",
    "timeline",
    "webhook",
    "webhooks",
    "hmac",
    "sha",
    "typedef",
    "typeddict",
    "dataclass",
    "dataclasses",
    "enum",
    "enums",
    "mixin",
    "mixins",
    "paginator",
    "aggregator",
    "uuid",
    "json",
    "jwt",
    "oauth",
    "fastapi",
    "flask",
    "django",
    "pytest",
    "mypy",
    "pylint",
    "flake",
    "isort",
    "codecov",
    "pyproject",
    "toml",
    "venv",
    "env",
    "dotenv",
    "gitignore",
    "repr",
    "str",
    "int",
    "bool",
    "dict",
    "tuple",
    "cls",
    "init",
    "repr",
    "len",
    "datetime",
    "timedelta",
    "timestamp",
    "iso",
    "utc",
    "timezone",
    "py",
    "md",
    "yml",
    "yaml",
    "txt",
    "cfg",
    "ini",
    "src",
    "docs",
    "tests",
    "dist",
    "build",
    "lib",
    "bin",
    "github",
    "ci",
    "cd",
    "devops",
    "dockerfile",
    "kubernetes",
    "postgres",
    "postgresql",
    "sqlite",
    "redis",
    "mongodb",
    "aws",
    "gcp",
    "azure",
    "cloudrun",
    "lambda",
    "ok",
    "dlq",
    "ttl",
    "roi",
    "mvp",
    "poc",
    "kpi",
    "lars",
    "larsson",
    "dreamly",
    "belong",
    "itochu",
    "notion",
    "req",
    "cand",
    "evt",
    "usr",
    "msg",
    "idx",
    "tmp",
    "max",
    "min",
    "id",
    "ids",
    "url",
    "urls",
    "uri",
    "uris",
    "http",
    "https",
    "ftp",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "retryable",
    "exponential",
    "backoff",
    "idempotent",
    "deduplicate",
}


class DocumentationChecker:
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_all(self) -> bool:
        """Check all documentation files"""
        print("Checking documentation...")
        print(f"Directory: {self.docs_dir}")
        print()

        md_files = list(self.docs_dir.glob("*.md"))
        if not md_files:
            self.errors.append("No markdown files found")
            return False

        for md_file in md_files:
            print(f"Checking {md_file.name}...")
            self.check_file(md_file)

        # Check README in root
        readme = self.docs_dir.parent / "README.md"
        if readme.exists():
            print(f"Checking {readme.name}...")
            self.check_file(readme)

        print()
        return self.report()

    def check_file(self, file_path: Path):
        """Check a single markdown file"""
        content = file_path.read_text()
        lines = content.split("\n")

        # Check heading hierarchy
        self.check_headings(file_path, lines)

        # Check code blocks
        self.check_code_blocks(file_path, lines)

        # Check links
        self.check_links(file_path, content)

        # Check for common typos
        self.check_typos(file_path, content)

        # Check line length
        self.check_line_length(file_path, lines)

    def check_headings(self, file_path: Path, lines: List[str]):
        """Check heading hierarchy"""
        heading_levels = []

        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                level = len(re.match(r"^#+", line).group())
                heading_levels.append((i, level, line))

        # Check for skipped levels
        for i in range(len(heading_levels) - 1):
            current_level = heading_levels[i][1]
            next_level = heading_levels[i + 1][1]

            if next_level > current_level + 1:
                self.warnings.append(
                    f"{file_path.name}:{heading_levels[i+1][0]} - "
                    f"Skipped heading level (h{current_level} -> h{next_level})"
                )

    def check_code_blocks(self, file_path: Path, lines: List[str]):
        """Check code block syntax"""
        in_code_block = False
        code_block_start = 0

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                if in_code_block:
                    in_code_block = False
                else:
                    in_code_block = True
                    code_block_start = i

                    # Check language specification
                    lang = line.strip()[3:].strip()
                    if not lang:
                        self.warnings.append(
                            f"{file_path.name}:{i} - Code block without language specification"
                        )

        if in_code_block:
            self.errors.append(
                f"{file_path.name}:{code_block_start} - Unclosed code block"
            )

    def check_links(self, file_path: Path, content: str):
        """Check for broken internal links"""
        # Find all markdown links
        link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        links = re.findall(link_pattern, content)

        for link_text, link_url in links:
            # Skip external links
            if link_url.startswith(("http://", "https://", "mailto:")):
                continue

            # Skip anchors
            if link_url.startswith("#"):
                continue

            # Check if file exists
            if "/" in link_url:
                linked_file = self.docs_dir.parent / link_url
            else:
                linked_file = file_path.parent / link_url

            # Remove anchor from path
            if "#" in link_url:
                linked_file = Path(str(linked_file).split("#")[0])

            if not linked_file.exists():
                self.errors.append(f"{file_path.name} - Broken link: {link_url}")

    def check_typos(self, file_path: Path, content: str):
        """Check for common typos"""
        common_typos = {
            "teh": "the",
            "recieve": "receive",
            "occured": "occurred",
            "seperate": "separate",
            "defintely": "definitely",
            "sucessful": "successful",
            "sucessfully": "successfully",
            "necesary": "necessary",
            "occassion": "occasion",
            "reponse": "response",
        }

        # Remove code blocks before checking
        content_no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

        for typo, correction in common_typos.items():
            pattern = r"\b" + typo + r"\b"
            if re.search(pattern, content_no_code, re.IGNORECASE):
                self.errors.append(
                    f"{file_path.name} - Typo found: '{typo}' (should be '{correction}')"
                )

    def check_line_length(self, file_path: Path, lines: List[str]):
        """Check for extremely long lines (excluding code blocks and links)"""
        in_code_block = False
        max_length = 120

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Skip lines with links
            if "[" in line and "](" in line:
                continue

            # Skip table lines
            if "|" in line:
                continue

            if len(line) > max_length:
                self.warnings.append(
                    f"{file_path.name}:{i} - Line too long ({len(line)} > {max_length})"
                )

    def report(self) -> bool:
        """Print report and return success status"""
        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.errors:
            print("❌ Errors:")
            for error in self.errors:
                print(f"  {error}")
            print()
            print(f"Found {len(self.errors)} error(s)")
            return False
        else:
            print("✅ All documentation checks passed!")
            if self.warnings:
                print(f"   ({len(self.warnings)} warning(s))")
            return True


def main():
    docs_dir = Path(__file__).parent.parent / "docs"

    if not docs_dir.exists():
        print(f"Error: Documentation directory not found: {docs_dir}")
        sys.exit(1)

    checker = DocumentationChecker(docs_dir)
    success = checker.check_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
