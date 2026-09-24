from __future__ import annotations

from pathlib import Path

from triage.application.tools import MAX_READ_LINES, MAX_SEARCH_RESULTS, read_file, search_repo


def test_search_finds_matches_with_locations(mini_repo: Path) -> None:
    result = search_repo(mini_repo, r"shell=True")
    assert result.ok
    assert "app/server.py:9:" in result.content


def test_search_skips_git_and_reports_bad_regex(mini_repo: Path) -> None:
    assert ".git/" not in search_repo(mini_repo, r"fixture").content
    assert "escape.txt" not in search_repo(mini_repo, r"hw1-secret-7f3a1c").content  # symlink leaves the repo
    bad = search_repo(mini_repo, r"(unclosed")
    assert not bad.ok and bad.error


def test_search_truncates_and_says_so(mini_repo: Path) -> None:
    result = search_repo(mini_repo, r".", max_results=2)
    assert result.ok
    assert len([line for line in result.content.splitlines() if ".py:" in line or ".md:" in line]) == 2
    assert "more" in result.content.lower() or "truncat" in result.content.lower()


def test_search_honours_path_glob_and_the_result_cap(mini_repo: Path) -> None:
    globbed = search_repo(mini_repo, r".", path_glob="app/*.py")
    assert "app/server.py:" in globbed.content and "README.md" not in globbed.content
    (mini_repo / "many.txt").write_text("x\n" * (MAX_SEARCH_RESULTS + 10))
    capped = search_repo(mini_repo, r"^x$", max_results=MAX_SEARCH_RESULTS + 10)
    assert len([line for line in capped.content.splitlines() if line.startswith("many.txt:")]) == MAX_SEARCH_RESULTS


def test_read_returns_numbered_lines_and_clips_at_eof(mini_repo: Path) -> None:
    result = read_file(mini_repo, "app/server.py", 8, 20)
    assert result.ok
    assert "9|" in result.content.replace(" ", "") and "shell=True" in result.content
    assert read_file(mini_repo, "app/server.py", 5, MAX_READ_LINES + 4).ok  # 200 lines requested: the limit is on length


def test_read_refuses_paths_outside_the_repo(mini_repo: Path) -> None:
    for path in ("../secret.txt", str(mini_repo.parent / "secret.txt"), "app/escape.txt", "app"):
        result = read_file(mini_repo, path, 1, 5)
        assert not result.ok, path
        assert "hw1-secret-7f3a1c" not in result.content + (result.error or "")


def test_read_refuses_bad_ranges(mini_repo: Path) -> None:
    for start, end in ((0, 3), (5, 4), (1, MAX_READ_LINES + 1)):
        assert not read_file(mini_repo, "app/server.py", start, end).ok
