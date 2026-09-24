from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from triage import StudentTODO

MAX_READ_LINES = 200
MAX_SEARCH_RESULTS = 50


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    content: str = ""
    error: str | None = None


def search_repo(root: Path, pattern: str, path_glob: str | None = None, max_results: int = MAX_SEARCH_RESULTS) -> ToolResult:
    """Search text files under root for a Python regular expression (ASSIGNMENT.md, Part 1)."""
    # TODO(student): implement repository search.
    raise StudentTODO("triage.application.tools.search_repo")


def read_file(root: Path, path: str, start_line: int, end_line: int) -> ToolResult:
    """Return numbered lines start_line..end_line of a file inside root (ASSIGNMENT.md, Part 1)."""
    # TODO(student): implement bounded, confined file reads.
    raise StudentTODO("triage.application.tools.read_file")


TOOL_SPECS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_repo",
            "description": "Search the pinned repository with a Python regular expression. Returns path:line: text matches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Python regular expression."},
                    "path_glob": {"type": "string", "description": "Optional glob over repository-relative paths."},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": MAX_SEARCH_RESULTS},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": f"Read up to {MAX_READ_LINES} numbered lines of a repository file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Repository-relative path."},
                    "start_line": {"type": "integer", "minimum": 1},
                    "end_line": {"type": "integer", "minimum": 1},
                },
                "required": ["path", "start_line", "end_line"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_finding",
            "description": "Submit the triage verdict. Ends the investigation if the runtime accepts it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "verdict": {"type": "string", "enum": ["TP", "FP", "Other"]},
                    "rationale": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "start_line": {"type": "integer", "minimum": 1},
                                "end_line": {"type": "integer", "minimum": 1},
                                "note": {"type": "string"},
                            },
                            "required": ["path", "start_line", "end_line", "note"],
                        },
                    },
                    "uncertainty": {"type": "string", "description": "What static inspection did not establish."},
                },
                "required": ["verdict", "rationale", "evidence", "uncertainty"],
            },
        },
    },
]
