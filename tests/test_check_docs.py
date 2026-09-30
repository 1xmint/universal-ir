"""Failure-oriented tests for the documentation quality gate."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_docs import check_documents, text_errors


class DocumentationTests(unittest.TestCase):
    def check(self, content: dict[str, str]) -> list[str]:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            files = []
            for name, text in content.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
                files.append(path)
            return check_documents(root, files)

    def test_relative_reference_and_encoded_links(self):
        errors = self.check({
            "README.md": "# Start\n\n[Guide][g]\n\n[g]: docs/a%20guide.md#first-step\n",
            "docs/a guide.md": "# Guide\n\n## First step\n",
        })
        self.assertEqual(errors, [])

    def test_missing_file_fails(self):
        errors = self.check({"README.md": "# Start\n\n[Missing](gone.md)\n"})
        self.assertTrue(any("missing link target" in error for error in errors))

    def test_missing_anchor_fails(self):
        errors = self.check({"README.md": "# Start\n\n[Missing](#gone)\n"})
        self.assertTrue(any("missing heading anchor" in error for error in errors))

    def test_duplicate_heading_anchor(self):
        errors = self.check({
            "README.md": "# Start\n\n## Step\n\n## Step\n\n[Again](#step-1)\n"
        })
        self.assertEqual(errors, [])

    def test_links_inside_code_are_not_checked(self):
        errors = self.check({
            "README.md": "# Start\n\n~~~text\n[Example](gone.md)\n~~~\n"
            "\nInline: \x60[Example](gone.md)\x60\n"
        })
        self.assertEqual(errors, [])

    def test_external_links_do_not_require_network(self):
        errors = self.check({
            "README.md": "# Start\n\n[Remote](https://example.invalid/path#heading)\n"
        })
        self.assertEqual(errors, [])

    def test_repository_escape_fails(self):
        errors = self.check({"README.md": "# Start\n\n[Outside](../outside.md)\n"})
        self.assertTrue(any("escapes repository" in error for error in errors))

    def test_unsupported_url_scheme_fails(self):
        errors = self.check({"README.md": "# Start\n\n[Share](ftp://host/share)\n"})
        self.assertTrue(any("unsupported link scheme" in error for error in errors))

    def test_unclosed_fence_fails(self):
        errors = self.check({"README.md": "# Start\n\n~~~text\nunfinished\n"})
        self.assertTrue(any("close the fenced code block" in error for error in errors))

    def test_heading_level_skip_fails(self):
        errors = self.check({"README.md": "# Start\n\n### Skipped\n"})
        self.assertTrue(any("heading levels skip" in error for error in errors))

    def test_multiple_top_headings_fail(self):
        errors = self.check({"README.md": "# Start\n\n# Other\n"})
        self.assertTrue(any("exactly one" in error for error in errors))

    def test_clean_text(self):
        self.assertEqual(text_errors(b"# Start\n"), [])

    def test_bom_crlf_missing_newline_and_whitespace_fail(self):
        errors = text_errors(b"\xef\xbb\xbf# Start \r\nend")
        self.assertTrue(any("BOM" in error for error in errors))
        self.assertTrue(any("LF" in error for error in errors))
        self.assertTrue(any("final newline" in error for error in errors))
        self.assertTrue(any("trailing whitespace" in error for error in errors))

    def test_invalid_utf8_fails(self):
        self.assertIn("file is not UTF-8", text_errors(b"\xff\n"))


if __name__ == "__main__":
    unittest.main()
