"""Check repository documentation without model calls or network requests."""

from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt


PARSER = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".txt"}
TEXT_NAMES = {"LICENSE", ".editorconfig", ".gitignore", ".gitattributes", "CODEOWNERS"}


def text_errors(data: bytes) -> list[str]:
    errors = []
    if data.startswith(b"\xef\xbb\xbf"):
        errors.append("UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["file is not UTF-8"]
    if b"\r" in data:
        errors.append("use LF line endings")
    if not data.endswith(b"\n"):
        errors.append("add a final newline")
    for number, line in enumerate(text.splitlines(), 1):
        if line != line.rstrip():
            errors.append(f"line {number}: trailing whitespace")
    return errors


def heading_anchors(tokens) -> set[str]:
    anchors = set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        inline = tokens[index + 1]
        text = "".join(
            child.content
            for child in inline.children or []
            if child.type in {"text", "code_inline"}
        )
        base = re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
        anchor = base
        suffix = 0
        while anchor in anchors:
            suffix += 1
            anchor = f"{base}-{suffix}"
        anchors.add(anchor)
    return anchors


def check_documents(root: Path, files: list[Path]) -> list[str]:
    root = root.resolve()
    sources = {path.resolve(): path.read_text(encoding="utf-8") for path in files}
    parsed = {path: PARSER.parse(text) for path, text in sources.items()}
    anchors = {path: heading_anchors(tokens) for path, tokens in parsed.items()}
    errors = []

    for path, tokens in parsed.items():
        name = path.relative_to(root).as_posix()
        headings = [token for token in tokens if token.type == "heading_open"]
        if name != ".github/pull_request_template.md":
            if sum(token.tag == "h1" for token in headings) != 1:
                errors.append(f"{name}: use exactly one level-one heading")
        previous = 0
        for heading in headings:
            level = int(heading.tag[1:])
            if level > previous + 1:
                errors.append(f"{name}: heading levels skip from {previous} to {level}")
            previous = level

        lines = sources[path].splitlines()
        for token in tokens:
            if token.type == "fence":
                start, end = token.map
                close = lines[end - 1].strip()
                pattern = re.escape(token.markup[0]) + "{" + str(len(token.markup)) + ",}"
                if end - start < 2 or not re.fullmatch(pattern, close):
                    errors.append(f"{name}:{start + 1}: close the fenced code block")
            for child in token.children or []:
                if child.type not in {"link_open", "image"}:
                    continue
                href = child.attrGet("href" if child.type == "link_open" else "src")
                if not href:
                    continue
                parts = urlsplit(href)
                if parts.scheme in {"http", "https", "mailto"} or (
                    not parts.scheme and parts.netloc
                ):
                    continue
                if parts.scheme:
                    errors.append(f"{name}: unsupported link scheme in {href}")
                    continue
                target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
                if not target.is_relative_to(root):
                    errors.append(f"{name}: link escapes repository: {href}")
                elif not target.is_file():
                    errors.append(f"{name}: missing link target: {href}")
                elif parts.fragment:
                    anchor = unquote(parts.fragment)
                    if target not in anchors or anchor not in anchors[target]:
                        errors.append(f"{name}: missing heading anchor: {href}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, check=True,
    )
    names = sorted(set(result.stdout.decode("utf-8").split("\0")) - {""})
    paths = [root / name for name in names]
    errors = []
    documents = []
    for path in paths:
        name = path.relative_to(root).as_posix()
        if not path.is_file():
            errors.append(f"{name}: indexed file is missing; stage its deletion")
            continue
        if path.name == ".env" or (
            path.name.startswith(".env.") and path.name != ".env.example"
        ):
            errors.append(f"{name}: environment credentials must not be tracked")
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            problems = text_errors(path.read_bytes())
            errors.extend(f"{name}: {problem}" for problem in problems)
            if path.suffix == ".md" and not problems:
                documents.append(path)
    errors.extend(check_documents(root, documents))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Documentation checks passed: {len(documents)} Markdown files; {len(paths)} repository files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
