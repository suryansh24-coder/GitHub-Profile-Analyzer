from __future__ import annotations

import re
from typing import Any

SECTION_RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("overview", ("overview", "about", "introduction", "what is"), "Add a short overview explaining what the project does and why it exists."),
    ("installation", ("install", "setup", "getting started", "quick start"), "Add installation steps with exact commands and prerequisites."),
    ("usage", ("usage", "how to use", "example", "getting started"), "Add a minimal usage example that a new user can copy."),
    ("contributing", ("contribut",), "Add contribution instructions or link to CONTRIBUTING.md."),
    ("license", ("license", "licensing"), "State the license or link to the LICENSE file."),
    ("testing", ("test", "unit test", "running tests"), "Explain how to run the test suite."),
    ("architecture", ("architecture", "design", "structure"), "Document the high-level structure for new contributors."),
    ("configuration", ("environment", "configuration", "env variable", ".env"), "Document required environment variables and configuration files."),
]

SEVERITY_PENALTY = {"critical": 18, "high": 10, "medium": 5, "low": 2}


def _line_of(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle.lower() in line.lower():
            return index
    return None


def _headings(text: str) -> list[tuple[int, str, int]]:
    result = []
    for index, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append((len(match.group(1)), match.group(2).strip(), index))
    return result


def _finding(
    finding_id: str,
    severity: str,
    section: str | None,
    line: int | None,
    message: str,
    recommendation: str,
    evidence: str | None = None,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "section": section,
        "line": line,
        "message": message,
        "recommendation": recommendation,
        "evidence": evidence,
    }


def analyze(readme: str | None, files: list[str] | None = None, repo: dict[str, Any] | None = None) -> dict[str, Any]:
    file_names = [str(path).lower() for path in (files or [])]
    findings: list[dict[str, Any]] = []
    if not readme or not readme.strip():
        findings.append(
            _finding("missing_readme", "critical", None, None, "README.md is missing or empty.", "Create a README with an overview, setup, usage and license section.")
        )
        return {
            "score": 0,
            "grade": "F",
            "findings": findings,
            "summary": {"critical": 1, "high": 0, "medium": 0, "low": 0},
            "sections": [],
            "links": {"internal": 0, "external": 0, "images": 0, "brokenInternal": []},
            "statistics": {"lines": 0, "words": 0, "headings": 0, "codeBlocks": 0},
        }

    lines = readme.splitlines()
    headings = _headings(readme)
    lower = readme.lower()

    if not any(level == 1 for level, _, _ in headings):
        findings.append(_finding("missing_h1", "medium", None, None, "No level-one heading found.", "Start the README with `# Project Name`."))
    h1_count = sum(1 for level, _, _ in headings if level == 1)
    if h1_count > 1:
        findings.append(_finding("multiple_h1", "low", None, headings[1][2] if len(headings) > 1 else None, f"Found {h1_count} level-one headings.", "Use a single H1 for the project title and H2 for sections."))

    previous_level = 0
    for level, title, line in headings:
        if previous_level and level > previous_level + 1:
            findings.append(
                _finding("heading_hierarchy", "medium", title, line, f"Heading jumps from H{previous_level} to H{level}.", "Do not skip heading levels; use H2 or H3 in sequence.", f"Line {line}: {'#' * level} {title}")
            )
        previous_level = level

    section_names = [title.lower() for _, title, _ in headings]
    detected_sections: list[str] = []
    for name, keywords, recommendation in SECTION_RULES:
        present = any(any(keyword in title for keyword in keywords) for title in section_names) or any(
            keyword in lower for keyword in keywords
        )
        if present:
            detected_sections.append(name)
        else:
            severity = "high" if name in {"overview", "installation", "usage"} else "medium"
            findings.append(_finding(f"missing_{name}", severity, name, None, f"Missing {name} section.", recommendation))

    for index, (level, title, line) in enumerate(headings):
        end = headings[index + 1][2] - 1 if index + 1 < len(headings) else len(lines)
        body = "\n".join(lines[line:end]).strip()
        if not body and level > 1:
            findings.append(_finding("empty_section", "medium", title, line, f"Section '{title}' has no content.", "Add content or remove the empty heading."))

    fence_count = sum(1 for line in lines if line.lstrip().startswith("```"))
    if fence_count % 2 != 0:
        findings.append(_finding("unclosed_code_fence", "high", None, None, "Unclosed Markdown code fence detected.", "Close every ``` block with a matching fence."))
    unlabeled = 0
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            if not in_fence and stripped.strip() == "```":
                unlabeled += 1
            in_fence = not in_fence
    if unlabeled:
        findings.append(_finding("unlabeled_code_block", "low", None, None, f"{unlabeled} code block(s) have no language hint.", "Add a language after the opening fence, e.g. ```bash.", None))

    links = re.findall(r"!?\[([^\]]*)\]\(([^)]+)\)", readme)
    internal = 0
    external = 0
    images = 0
    broken_internal: list[str] = []
    empty_alt = 0
    for label, target in links:
        clean = target.strip().split(" ")[0]
        if clean.startswith("http://") or clean.startswith("https://") or clean.startswith("mailto:"):
            external += 1
        elif clean.startswith("#"):
            anchor = clean[1:].lower().replace(" ", "-")
            if not any(re.sub(r"[^a-z0-9-]", "", title.lower().replace(" ", "-")) == anchor for _, title, _ in headings):
                broken_internal.append(clean)
        else:
            internal += 1
            base = clean.split("#")[0].lstrip("./")
            if file_names and base and base not in file_names and not any(name.endswith(base) for name in file_names):
                broken_internal.append(clean)
    for match in re.finditer(r"!\[([^\]]*)\]\(", readme):
        images += 1
        if not match.group(1).strip():
            empty_alt += 1
    if broken_internal:
        findings.append(
            _finding("broken_internal_link", "medium", None, _line_of(readme, broken_internal[0]), f"{len(broken_internal)} internal link target(s) could not be verified.", "Update relative links and anchors so they point to files or headings that exist.", ", ".join(broken_internal[:5]))
        )
    if images == 0:
        findings.append(_finding("no_screenshots", "low", None, None, "No screenshot or diagram images found.", "Add a screenshot or architecture diagram when it helps users understand the project."))
    if empty_alt:
        findings.append(_finding("image_alt_text", "low", None, None, f"{empty_alt} image(s) have empty alt text.", "Describe each image in its alt attribute for accessibility."))

    duplicated = []
    paragraphs = [re.sub(r"\s+", " ", block).strip().lower() for block in re.split(r"\n\s*\n", readme) if len(block.strip()) > 80]
    seen: set[str] = set()
    for paragraph in paragraphs:
        if paragraph in seen:
            duplicated.append(paragraph[:80])
        seen.add(paragraph)
    if duplicated:
        findings.append(_finding("duplicate_content", "low", None, None, f"{len(duplicated)} duplicated paragraph(s) detected.", "Remove duplicated content and keep one authoritative section."))

    table_lines = [line for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if table_lines:
        has_separator = any(re.match(r"^\s*\|?[\s:\-|]+\|", line) for line in table_lines)
        if not has_separator:
            findings.append(_finding("malformed_table", "medium", None, None, "Table-like content has no separator row.", "Add a separator row such as `| --- | --- |` below the header."))

    outdated_terms = [term for term in ("deprecated", "outdated", "no longer works", "doesn't work", "todo") if term in lower]
    if outdated_terms:
        findings.append(
            _finding("outdated_signal", "medium", None, _line_of(readme, outdated_terms[0]), "Documentation contains possible outdated signals.", "Verify and update commands, versions and notes marked as deprecated or TODO.", ", ".join(outdated_terms))
        )

    if repo is not None:
        if repo.get("description") and "overview" in detected_sections:
            description = str(repo["description"]).strip()
            if description.lower()[:40] not in lower:
                findings.append(
                    _finding("description_mismatch", "low", "overview", None, "README overview does not repeat the repository description from GitHub.", "Consider aligning the first paragraph with the GitHub repository description.", description)
                )

    badge_count = lower.count("shields.io") + lower.count("badge")
    if badge_count == 0:
        findings.append(_finding("no_badges", "low", None, None, "No status badges detected.", "Add build, license or version badges only when they reflect real status."))

    penalty = sum(SEVERITY_PENALTY[f["severity"]] for f in findings)
    score = max(0, 100 - penalty)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    summary = {key: sum(1 for f in findings if f["severity"] == key) for key in SEVERITY_PENALTY}
    return {
        "score": score,
        "grade": grade,
        "findings": findings,
        "summary": summary,
        "sections": detected_sections,
        "links": {"internal": internal, "external": external, "images": images, "brokenInternal": broken_internal[:10]},
        "statistics": {
            "lines": len(lines),
            "words": len(readme.split()),
            "headings": len(headings),
            "codeBlocks": fence_count // 2,
        },
    }


def suggest_readme(readme: str | None, repo: dict[str, Any], files: list[str] | None = None, analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    name = str(repo.get("name") or "project")
    owner = str((repo.get("owner") or {}).get("login") or "owner")
    description = str(repo.get("description") or "").strip() or "Describe what this project does and who it is for."
    language = repo.get("language") or ""
    license_name = (repo.get("license") or {}).get("name") or "See LICENSE"
    homepage = str(repo.get("homepage") or "").strip()
    clone_url = str(repo.get("clone_url") or f"https://github.com/{owner}/{name}.git")
    topics = list(repo.get("topics") or [])
    files_lower = [str(path).lower() for path in (files or [])]
    changes: list[str] = []

    if language.lower() in {"python", "jupyter notebook"}:
        install = "```bash\ngit clone " + clone_url + "\ncd " + name + "\npython -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\n```"
        test = "```bash\npytest -q\n```"
    elif language.lower() in {"javascript", "typescript"}:
        install = "```bash\ngit clone " + clone_url + "\ncd " + name + "\nnpm install\n```"
        test = "```bash\nnpm test\n```"
    elif language.lower() in {"go"}:
        install = "```bash\ngit clone " + clone_url + "\ncd " + name + "\ngo mod download\n```"
        test = "```bash\ngo test ./...\n```"
    elif language.lower() in {"rust"}:
        install = "```bash\ngit clone " + clone_url + "\ncd " + name + "\ncargo build\n```"
        test = "```bash\ncargo test\n```"
    else:
        install = "```bash\ngit clone " + clone_url + "\ncd " + name + "\n# Follow the setup steps for this technology stack\n```"
        test = "```bash\n# Add the command used to run tests\n```"

    existing = analysis.get("sections") if analysis else []
    intro = f"# {name}\n\n{description}\n"
    if homepage:
        intro += f"\nOfficial site: {homepage}\n"
    if topics:
        intro += "\n" + " ".join(f"`{topic}`" for topic in topics[:8]) + "\n"

    parts = [intro, "## Overview\n\n" + description + "\n", "## Installation\n\n### Prerequisites\n\n- Git\n- A supported runtime for " + (language or "this project") + "\n\n### Steps\n\n" + install + "\n", "## Usage\n\nDescribe the most common command or workflow here.\n\n```bash\n# Add a working example\n```\n"]
    changes.extend(["Created a single H1 title", "Added overview, installation and usage sections"])

    if "architecture" not in (existing or []):
        parts.append("## Architecture\n\nDescribe the main components and how data flows between them. Link to `docs/architecture/SYSTEM_OVERVIEW.md` when available.\n")
        changes.append("Added an architecture section placeholder")

    if "configuration" not in (existing or []):
        parts.append("## Configuration\n\nList required environment variables and configuration files. Do not commit secrets.\n\n```bash\n# EXAMPLE_VAR=description_of_value\n```\n")
        changes.append("Added environment configuration guidance")

    parts.append("## Testing\n\n" + test + "\n")
    if "contributing" not in (existing or []):
        parts.append("## Contributing\n\nContributions are welcome. Read `CONTRIBUTING.md` if present, open an issue to discuss larger changes, and include tests with your pull request.\n")
        changes.append("Added contribution guidance")
    if "license" not in (existing or []):
        parts.append(f"## License\n\n{license_name}. See the LICENSE file for details.\n")
        changes.append("Added license information")

    if "docs/" in files_lower:
        parts.append("## Documentation\n\nAdditional documentation is available in the `docs/` directory.\n")

    suggested = "\n".join(parts).rstrip() + "\n"
    return {
        "suggested": suggested,
        "changes": changes,
        "mode": "deterministic-template",
        "warning": "This is a generated draft. Review it before committing; it is not written to GitHub automatically.",
    }
