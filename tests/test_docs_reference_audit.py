"""Safety checks for the read-only documentation dependency audit."""
import tempfile
import unittest
from pathlib import Path
from scripts.audit_docs_references_readonly import audit


class DocsReferenceAuditTests(unittest.TestCase):
    def test_references_outside_index_and_unique_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "src").mkdir()
            (root / "docs" / "README.md").write_text(
                "[Old](old.md)\n[Active](active.md)", encoding="utf-8")
            (root / "docs" / "old.md").write_text("Historical CI #1834\n",
                                                   encoding="utf-8")
            (root / "docs" / "active.md").write_text(
                "[Old report](old.md)", encoding="utf-8")
            (root / "src" / "main.py").write_text(
                "# docs/active.md\n", encoding="utf-8")
            result = audit(root)
            self.assertEqual(result["document_count"], 2)
            self.assertEqual(result["documents"]["old.md"]["inbound_count"], 1)
            self.assertTrue(result["documents"]["old.md"]["potential_unique_evidence"])
            self.assertEqual(result["documents"]["active.md"]["inbound_count"], 1)
            self.assertFalse(result["documents"]["old.md"]["deletion_safe"])
            self.assertEqual(result["broken_relative_link_count"], 0)

    def test_orphan_is_not_automatically_deletable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "orphan.md").write_text(
                "One-off audit observations", encoding="utf-8")
            result = audit(root)
            info = result["documents"]["orphan.md"]
            self.assertEqual(info["inbound_count"], 0)
            self.assertFalse(info["deletion_safe"])

    def test_actual_repository_inventory_summary(self):
        # Emit bounded evidence in standard GitHub CI logs, with no file writes.
        import json
        root = Path(__file__).resolve().parents[1]
        result = audit(root)
        self.assertGreaterEqual(result["document_count"], 40)  # Pruned archived reports reduce the fixed count
        self.assertEqual(result["files_deleted"], 0)
        self.assertEqual(result["broken_relative_link_count"], 0)
        self.assertNotIn("A3_DASHBOARD_NATIVE_15_SLOTS_DHAN_AUDIT_20261115.md", result["documents"])
        self.assertNotIn("A2_CHART_FILTER_OPTIONS_REPORT_20261115.md", result["documents"])
        orphan = [
            {"name": name, "unique_marker": data["potential_unique_evidence"]}
            for name, data in result["documents"].items()
            if data["inbound_count"] == 0
        ]
        summary = {
            "document_count": result["document_count"],
            "texts_scanned": result["texts_scanned"],
            "linked_docs": result["documents_with_inbound_references"],
            "evidence_docs": result["documents_with_evidence_markers"],
            "broken_relative_link_count": result["broken_relative_link_count"],
            "broken_link_samples": result["broken_relative_links"][:10],
            "no_external_inbound_candidates": orphan[:50],
        }
        print("BOT_KING_DOCS_AUDIT_SUMMARY=" + json.dumps(summary, sort_keys=True))

    def test_broken_link_identification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "README.md").write_text(
                "[Missing](gone.md)", encoding="utf-8")
            result = audit(root)
            self.assertEqual(result["broken_relative_link_count"], 1)


if __name__ == "__main__":
    unittest.main()
