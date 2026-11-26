from __future__ import annotations

from typing import Any

SUPPORTED = {"contributing", "code_of_conduct", "security", "architecture"}


def generate(kind: str, repo: dict[str, Any], context: dict[str, Any] | None = None) -> str:
    if kind not in SUPPORTED:
        raise ValueError("Unsupported document type.")
    name = str(repo.get("name") or "this project")
    owner = str((repo.get("owner") or {}).get("login") or "the maintainer")
    contact = f"Open a private message to @{owner} on GitHub or use the repository's security advisory form." if kind == "security" else f"Open an issue in {name}."
    context = context or {}

    if kind == "contributing":
        return f"""# Contributing to {name}

Thank you for considering a contribution.

## Before you start

- Read the README and understand the project's goals.
- Search existing issues and pull requests to avoid duplicate work.
- For larger changes, open an issue first and agree on the approach.

## Development setup

1. Fork and clone the repository.
2. Install the dependencies described in the README.
3. Create a branch with a descriptive name.

## Making changes

- Keep changes focused and include tests where behaviour changes.
- Follow the existing style and file organisation.
- Update documentation when behaviour or setup changes.
- Never commit credentials, tokens or personal data.

## Pull requests

- Reference the related issue with `#number`.
- Describe what changed and how you verified it.
- Be responsive to review feedback.

## Code of conduct

By participating you agree to follow the project's Code of Conduct.
""".strip() + "\n"

    if kind == "code_of_conduct":
        return f"""# Code of Conduct — {name}

## Our standard

We want participation in {name} to be welcoming, respectful and productive for everyone.

## Expected behaviour

- Be respectful of different backgrounds, experience levels and viewpoints.
- Give constructive feedback focused on the work, not the person.
- Accept feedback gracefully and help newcomers learn.
- Respect maintainers' decisions about scope and releases.

## Unacceptable behaviour

- Harassment, personal attacks or discriminatory language.
- Publishing someone else's private information.
- Trolling, spam or deliberate disruption.

## Reporting

Report unacceptable behaviour privately to {contact} Reports are handled confidentially and may result in a warning, temporary block or permanent removal.

This document is a starter template. Adapt it to your community and, where appropriate, reference the Contributor Covenant at https://www.contributor-covenant.org/.
""".strip() + "\n"

    if kind == "security":
        return f"""# Security Policy — {name}

## Supported versions

List the versions that currently receive security fixes. Example: the latest released version.

## Reporting a vulnerability

Do not open a public issue for an unpatched vulnerability. Contact {contact} Include:

- affected version or commit,
- steps to reproduce,
- potential impact,
- any suggested mitigation.

You should receive an acknowledgement within the timeframe the maintainers commit to publicly. Keep reports confidential until a fix is released.

## Disclosure process

1. Maintainers confirm the report and assess severity.
2. A fix and regression test are prepared privately.
3. A release and advisory are published together.
4. Reporters are credited unless they prefer anonymity.

## Scope

This policy covers the source code and published packages of {name}. Third-party dependencies should be reported to their own maintainers.
""".strip() + "\n"

    entrypoints = context.get("entrypoints") or []
    api_flow = context.get("apiFlow") or []
    lines = [f"# Architecture — {name}", "", "## Purpose", "", str(repo.get("description") or "Describe the purpose of this project."), "", "## Components", ""]
    if entrypoints:
        lines.append("Entry points identified by static analysis:")
        lines.extend(f"- `{path}`" for path in entrypoints[:10])
    else:
        lines.append("No common entry-point filename was detected. Document the actual entry point here.")
    lines.extend(["", "## Request flow", ""])
    if api_flow:
        for route in api_flow[:20]:
            lines.append(f"- `{route['method']} {route['path']}` — `{route['file']}`")
    else:
        lines.append("No route declarations were detected in the analysed files.")
    lines.extend(["", "## Data and configuration", "", "Describe data stores, configuration files and environment variables used by the project.", "", "## Verification", "", "This document was generated from static analysis of a bounded set of files. Review and correct it before publishing."])
    return "\n".join(lines) + "\n"
