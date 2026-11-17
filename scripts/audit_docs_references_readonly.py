#!/usr/bin/env python3
"""Read-only cross-repository documentation dependency and retention audit.

Reports inbound references outside docs/README.md (the navigation index),
unique history markers, and possible dead links. Does not modify files or
mark any file safe to delete on reference count alone.
"""
import argparse
import json
import re
from pathlib import Path

EXTENSIONS = {".md", ".py", ".yml", ".yaml", ".toml", ".json", ".sh", ".txt"}
EVIDENCE = re.compile(
    r"(?i)(?:actions/runs/\d+|\b[0-9a-f]{40}\b|\b(?:SHA256|rollback|backup|versionCode|CI #)\b)"
)
LINK = re.compile(r"\]\(([^)#]+(?:\.[a-z]+))(?:#[^)]*)?\)")


def audit(root: Path):
    docs = root / "docs"
    if not docs.is_dir():
        raise ValueError("Missing docs folder")
    document_paths = sorted(p for p in docs.glob("*.md") if p.is_file())
    candidates = [p for p in document_paths if p.name != "README.md"]
    texts = {}
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTENSIONS:
            continue
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        if p.stat().st_size > 3000000:
            continue
        try:
            texts[p] = p.read_text(encoding="utf-8")
        except UnicodeError:
            continue
    results = {}
    for doc in candidates:
        incoming = []
        for other, value in texts.items():
            if other == doc or other == docs / "README.md":
                continue
            # Plain filename references, not just Markdown links. Capture a
            # root path for each source without leaking any source contents.
            if doc.name in value:
                incoming.append(other.relative_to(root).as_posix())
        data = texts.get(doc, "")
        results[doc.name] = {
            "inbound_outside_index": incoming,
            "inbound_count": len(incoming),
            "potential_unique_evidence": bool(EVIDENCE.search(data)),
            "bytes": doc.stat().st_size,
            "deletion_safe": False,  # requires human provenance assessment
        }
    checked_links = 0
    broken_links = []
    for source, raw in texts.items():
        if source.suffix != ".md":
            continue
        for match in LINK.finditer(raw):
            target = match.group(1)
            if "://" in target or target.startswith(("mailto:", "#")):
                continue
            checked_links += 1
            if not (source.parent / target).resolve().exists():
                broken_links.append({
                    "from": source.relative_to(root).as_posix(),
                    "to": target,
                })
    return {
        "audit": "BOT_KING_DOCS_REFERENCE_RETENTION",
        "documents": len(candidates),
        "texts_scanned": len(texts),
        "link_targets_checked": checked_links,
        "broken_relative_links": broken_links[:100],
        "broken_relative_link_count": len(broken_links),
        "documents_with_inbound_references": sum(
            x["inbound_count"] > 0 for x in results.values()),
        "documents_with_evidence_markers": sum(
            x["potential_unique_evidence"] for x in results.values()),
        "documents": results,
        "production_changed": False,
        "files_deleted": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.repo), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
