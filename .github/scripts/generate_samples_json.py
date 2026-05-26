#!/usr/bin/env python3
"""
Parse README.md to generate Sample.json for the Evergine launcher.

Extracts sample metadata (Title, Description, Image, Uri, DownloadBranchName)
from the markdown structure and outputs a JSON array matching the launcher format.
"""

import json
import re
import sys
from pathlib import Path

REPO_RAW_BASE = "https://github.com/EvergineTeam/Samples/raw/main"


def parse_readme(readme_path: Path) -> list[dict]:
    """Parse README.md and extract sample entries."""
    content = readme_path.read_text(encoding="utf-8")

    # Split by H2 headers, keeping the header text
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    samples = []
    for section in sections[1:]:  # Skip content before first H2
        lines = section.strip().split("\n")
        if not lines:
            continue

        title = lines[0].strip()

        # Extract description: lines between title and image/comment/source-code
        desc_lines = []
        image_url = None
        source_url = None
        opens_in_studio = None

        i = 1
        # Skip empty lines after title
        while i < len(lines) and not lines[i].strip():
            i += 1

        # Collect description lines (before image, comment, or Source Code)
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("![") or line.startswith("<!--") or line.startswith("Source Code:"):
                break
            if line:
                desc_lines.append(line)
            i += 1

        # Process remaining lines for image, comments, and source URL
        while i < len(lines):
            line = lines[i].strip()

            # Image: ![alt](url)
            img_match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
            if img_match:
                image_url = img_match.group(1)
                i += 1
                continue

            # HTML comment: <!-- OpensInEvergineStudio: false -->
            comment_match = re.match(r"<!--\s*OpensInEvergineStudio:\s*(\w+)\s*-->", line)
            if comment_match:
                value = comment_match.group(1).lower()
                opens_in_studio = value == "true"
                i += 1
                continue

            # Source Code URL
            src_match = re.match(r"Source Code:\s*(.+)", line)
            if src_match:
                source_url = src_match.group(1).strip()
                i += 1
                continue

            i += 1

        # Skip sections without a source URL (not a sample entry)
        if not source_url:
            continue

        # Resolve relative image paths to full raw GitHub URLs
        if image_url and not image_url.startswith("http"):
            image_url = f"{REPO_RAW_BASE}/{image_url}"

        # Clean description: remove markdown formatting like __bold__
        description = " ".join(desc_lines)
        description = re.sub(r"__([^_]+)__", r"\1", description)
        description = re.sub(r"\*\*([^*]+)\*\*", r"\1", description)

        entry = {
            "Title": title,
            "Description": description,
            "Uri": source_url,
            "Image": image_url,
            "DownloadBranchName": "main",
        }

        if opens_in_studio is not None:
            entry["OpensInEvergineStudio"] = opens_in_studio

        samples.append(entry)

    return samples


def main():
    # Determine paths
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    readme_path = repo_root / "README.md"

    output_path = Path("Sample.json")
    if len(sys.argv) > 1 and sys.argv[1] == "--output" and len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    if not readme_path.exists():
        print(f"ERROR: README.md not found at {readme_path}", file=sys.stderr)
        sys.exit(1)

    samples = parse_readme(readme_path)

    json_output = json.dumps(samples, indent=2, ensure_ascii=False)

    output_path.write_text(json_output + "\n", encoding="utf-8")
    print(f"Generated {output_path} with {len(samples)} samples.")


if __name__ == "__main__":
    main()
