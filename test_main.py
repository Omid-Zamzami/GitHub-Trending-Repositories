import argparse
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
import requests

# Importing functions from main.py
from main import (
    calculate_since_date,
    display_repos,
    fetch_repos,
    github_trending_repos,
    parse_arguments,
    positive_int,
)


# 1. Tests for positive_int validator
class TestPositiveInt:
    @pytest.mark.parametrize("valid_input, expected", [
        ("1", 1),
        ("10", 10),
        ("100", 100),
    ])
    def test_positive_int_valid(self, valid_input: str, expected: int) -> None:
        """Test valid positive integer strings return parsed integers."""
        assert positive_int(valid_input) == expected

    @pytest.mark.parametrize("invalid_input", ["0", "-1", "-50"])
    def test_positive_int_zero_or_negative(self, invalid_input: str) -> None:
        """Test zero or negative integers raise ArgumentTypeError with expected message."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            positive_int(invalid_input)
        assert f"{invalid_input} must be a positive integer." in str(exc_info.value)

    @pytest.mark.parametrize("non_int_input", ["abc", "12.5", "", "None"])
    def test_positive_int_invalid_strings(self, non_int_input: str) -> None:
        """Test non-integer strings raise ArgumentTypeError."""
        with pytest.raises(argparse.ArgumentTypeError):
            positive_int(non_int_input)


# 2. Tests for CLI Argument Parsing (parse_arguments)
class TestParseArguments:
    def test_parse_arguments_default_values(self) -> None:
        """Test default CLI values when no arguments are provided."""
        args = parse_arguments([])
        assert args.duration == "week"
        assert args.limit == 10

    @pytest.mark.parametrize("flag, duration_val", [
        ("-d", "day"),
        ("--duration", "week"),
        ("-d", "month"),
        ("--duration", "year"),
    ])
    def test_parse_arguments_valid_durations(self, flag: str, duration_val: str) -> None:
        """Test all valid duration options using short (-d) and long (--duration) flags."""
        args = parse_arguments([flag, duration_val])
        assert args.duration == duration_val

    @pytest.mark.parametrize("flag, limit_val, expected", [
        ("-l", "5", 5),
        ("--limit", "20", 20),
    ])
    def test_parse_arguments_valid_limits(self, flag: str, limit_val: str, expected: int) -> None:
        """Test custom limit values using short (-l) and long (--limit) flags."""
        args = parse_arguments([flag, limit_val])
        assert args.limit == expected

    def test_parse_arguments_case_insensitivity(self) -> None:
        """Test that duration argument accepts uppercase strings and converts to lowercase."""
        args = parse_arguments(["--duration", "DAY"])
        assert args.duration == "day"

    def test_parse_arguments_invalid_duration(self) -> None:
        """Test invalid duration choice triggers CLI exit (SystemExit)."""
        with pytest.raises(SystemExit):
            parse_arguments(["--duration", "century"])

    @pytest.mark.parametrize("invalid_limit", ["0", "-5", "abc", "10.5"])
    def test_parse_arguments_invalid_limit(self, invalid_limit: str) -> None:
        """Test invalid limit values (zero, negative, non-int) trigger CLI exit."""
        with pytest.raises(SystemExit):
            parse_arguments(["--limit", invalid_limit])


# 3. Tests for Date Calculation (calculate_since_date)
class TestCalculateSinceDate:
    @patch("main.datetime")
    @pytest.mark.parametrize("duration, expected_date_str", [
        ("day", "2026-09-05"),
        ("week", "2026-08-30"),
        ("month", "2026-08-07"),
        ("year", "2025-09-06"),
        ("unknown_fallback", "2026-08-30"),  # Tests wildcard default fallback logic
    ])
    def test_calculate_since_date(
        self, mock_datetime: MagicMock, duration: str, expected_date_str: str
    ) -> None:
        """Test date calculation logic relative to a fixed current date (deterministic)."""
        mock_datetime.now.return_value = datetime(2026, 9, 6)
        
        result = calculate_since_date(duration)
        assert result == expected_date_str


# 4. Tests for API Requests & Exception Handling (fetch_repos)
class TestFetchRepos:
    @patch("main.calculate_since_date")
    @patch("main.requests.get")
    def test_fetch_repos_success(
        self, mock_get: MagicMock, mock_calc_date: MagicMock
    ) -> None:
        """Test successful API request verifies exact parameters and response structure."""
        mock_calc_date.return_value = "2026-08-30"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"name": "repo1"}, {"name": "repo2"}]
        }
        mock_get.return_value = mock_response

        repos = fetch_repos("week", 10)

        assert len(repos) == 2
        assert repos[0]["name"] == "repo1"
        
        # Verify exact request parameters, headers, and timeout
        mock_get.assert_called_once_with(
            "https://api.github.com/search/repositories",
            params={
                "q": "created:>2026-08-30",
                "sort": "stars",
                "order": "desc",
                "per_page": 10
            },
            headers={"User-Agent": "GitHub-Trending-Repos"},
            timeout=10
        )

    @patch("main.requests.get")
    @pytest.mark.parametrize("status_code", [400, 403, 404, 500, 502, 503])
    def test_fetch_repos_http_error_handling(
        self, mock_get: MagicMock, status_code: int
    ) -> None:
        """Test non-200 HTTP status codes trigger raise_for_status and return [] safely."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} Error"
        )
        mock_get.return_value = mock_response

        repos = fetch_repos("week", 10)

        assert repos == []
        mock_response.raise_for_status.assert_called_once()

    @patch("main.requests.get")
    def test_fetch_repos_json_decode_error(self, mock_get: MagicMock) -> None:
        """Test invalid JSON response triggers ValueError and returns [] safely."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON format")
        mock_get.return_value = mock_response

        repos = fetch_repos("week", 10)

        assert repos == []

    @patch("main.requests.get")
    @pytest.mark.parametrize("exception_class", [
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ])
    def test_fetch_repos_network_exceptions(
        self, mock_get: MagicMock, exception_class: type
    ) -> None:
        """Test network connectivity exceptions are caught and return []."""
        mock_get.side_effect = exception_class("Network level exception")

        repos = fetch_repos("week", 10)
        assert repos == []


# 5. Tests for Output Display (display_repos)
class TestDisplayRepos:
    def test_display_repos_empty_list(self, capsys: pytest.CaptureFixture) -> None:
        """Test display message when repository list is empty and ensures no items are printed."""
        display_repos([], "week", 10)
        captured = capsys.readouterr()
        
        assert "No repositories to display." in captured.out
        assert "GitHub Trending Repositories" not in captured.out

    def test_display_repos_valid_data(self, capsys: pytest.CaptureFixture) -> None:
        """Test formatted output rendering for valid repository data."""
        sample_repos = [
            {
                "owner": {"login": "octocat"},
                "name": "hello-world",
                "stargazers_count": 1500,
                "language": "Python",
                "description": "A sample repository",
                "html_url": "https://github.com/octocat/hello-world",
            }
        ]

        display_repos(sample_repos, "week", 1)
        captured = capsys.readouterr()

        assert "1. octocat/hello-world" in captured.out
        assert "Description: A sample repository" in captured.out
        assert "Stars: 1500" in captured.out
        assert "Language: Python" in captured.out
        assert "Link: https://github.com/octocat/hello-world" in captured.out

    @pytest.mark.parametrize("sample_repo, expected_owner, expected_name, expected_stars, expected_lang, expected_desc, expected_link", [
        # Case 1: Owner dict is None
        (
            {"owner": None, "name": "repo1", "stargazers_count": 10, "language": "Go", "description": "desc", "html_url": "http://test.com"},
            "No owner", "repo1", "10", "Go", "desc", "http://test.com"
        ),
        # Case 2: Owner dict is empty {}
        (
            {"owner": {}, "name": "repo1", "stargazers_count": 10, "language": "Go", "description": "desc", "html_url": "http://test.com"},
            "No owner", "repo1", "10", "Go", "desc", "http://test.com"
        ),
        # Case 3: Owner login is None
        (
            {"owner": {"login": None}, "name": "repo1", "stargazers_count": 10, "language": "Go", "description": "desc", "html_url": "http://test.com"},
            "No owner", "repo1", "10", "Go", "desc", "http://test.com"
        ),
        # Case 4: All fields missing or None
        (
            {"owner": None, "name": None, "stargazers_count": None, "language": None, "description": None, "html_url": None},
            "No owner", "No name", "0", "Unknown", "No description", "N/A"
        ),
        # Case 5: Empty dictionary {}
        (
            {},
            "No owner", "No name", "0", "Unknown", "No description", "N/A"
        ),
    ])
    def test_display_repos_fallbacks(
        self,
        capsys: pytest.CaptureFixture,
        sample_repo: dict,
        expected_owner: str,
        expected_name: str,
        expected_stars: str,
        expected_lang: str,
        expected_desc: str,
        expected_link: str,
    ) -> None:
        """Test fallback default values for missing, None, or empty dictionary fields."""
        display_repos([sample_repo], "month", 1)
        captured = capsys.readouterr()

        assert f"1. {expected_owner}/{expected_name}" in captured.out
        assert f"Description: {expected_desc}" in captured.out
        assert f"Stars: {expected_stars}" in captured.out
        assert f"Language: {expected_lang}" in captured.out
        assert f"Link: {expected_link}" in captured.out


# 6. Tests for Main Orchestration Function (github_trending_repos)
class TestMainOrchestration:
    @patch("main.display_repos")
    @patch("main.fetch_repos")
    @patch("main.parse_arguments")
    def test_github_trending_repos_orchestration(
        self,
        mock_parse: MagicMock,
        mock_fetch: MagicMock,
        mock_display: MagicMock,
    ) -> None:
        """Unit test verifying pipeline orchestration and parameter passing across components."""
        mock_parse.return_value = argparse.Namespace(duration="week", limit=5)
        mock_fetch.return_value = [{"name": "repo1"}]

        github_trending_repos()

        mock_parse.assert_called_once_with()
        mock_fetch.assert_called_once_with(duration="week", limit=5)
        mock_display.assert_called_once_with([{"name": "repo1"}], "week", 5)

    @patch("main.fetch_repos")
    @patch("main.parse_arguments")
    def test_github_trending_repos_exception_handling(
        self,
        mock_parse: MagicMock,
        mock_fetch: MagicMock,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """Test top-level error handling in github_trending_repos catches unexpected errors."""
        mock_parse.return_value = argparse.Namespace(duration="week", limit=5)
        mock_fetch.side_effect = Exception("Unexpected application error")

        github_trending_repos()

        captured = capsys.readouterr()
        assert "Error occured: Unexpected application error" in captured.out