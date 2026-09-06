import argparse
import requests
from datetime import datetime, timedelta
from typing import Any


def positive_int(str_value: str) -> int:
    """Validate that an input string represents a positive integer (> 0).

    Raises:
        argparse.ArgumentTypeError: If the value is not an integer or is <= 0.
    """
    try:
        int_value = int(str_value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{str_value} must be a positive integer.")

    if int_value <= 0:
        raise argparse.ArgumentTypeError(f"{str_value} must be a positive integer.")

    return int_value


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """Parse and return command-line arguments for the CLI application."""
    parser = argparse.ArgumentParser(description="CLI tool for fetching trending repos.")

    parser.add_argument(
        "-d",
        "--duration",
        type=str.lower,
        choices=["day", "week", "month", "year"],
        default="week",
        help="Duration of receiving trending repos. (Default: week)"
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=positive_int,
        default=10,
        help="Number of receiving trending repos. (Default: 10)"
    )

    return parser.parse_args(args)


def calculate_since_date(duration: str) -> str:
    """Calculate the starting date string (YYYY-MM-DD) based on the specified duration."""
    today = datetime.now()

    match duration:
        case "day":
            target_date = today - timedelta(days=1)
        case "week":
            target_date = today - timedelta(days=7)
        case "month":
            target_date = today - timedelta(days=30)
        case "year":
            target_date = today - timedelta(days=365)
        case _:
            target_date = today - timedelta(days=7)

    return target_date.strftime("%Y-%m-%d")


def fetch_repos(duration: str, limit: int) -> list[dict[str, Any]]:
    """Fetch trending GitHub repositories using the GitHub Search API.

    Returns:
        list[dict[str, Any]]: A list of repository dictionaries, or an empty list on failure.
    """
    since_date = calculate_since_date(duration)

    try:
        url = "https://api.github.com/search/repositories"

        params = {
            "q": f"created:>{since_date}",
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }

        headers = {
            "User-Agent": "GitHub-Trending-Repos"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])

        response.raise_for_status()

    except requests.exceptions.Timeout:
        print("Error: Request timed out. Please check your network and try again.")
        return []
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to GitHub. Please check your internet connection.")
        return []
    except requests.exceptions.HTTPError as error:
        print(f"HTTP Error occurred: {error}")
        return []
    except requests.exceptions.RequestException as error:
        print(f"An unexpected network error occurred: {error}")
        return []
    except ValueError:
        print("Error: Failed to parse JSON response from server.")
        return []


def display_repos(repos: list[dict[str, Any]], duration: str, limit: int) -> None:
    """Format and display repository details to stdout with fallbacks for missing values."""
    if not repos:
        print("\nNo repositories to display.")
        return

    print("\nGitHub Trending Repositories")
    print(f"Duration: {duration}")
    print(f"Showing: {limit} repositories")

    for index, item in enumerate(repos, start=1):
        profile = item.get('owner') or {}
        owner = profile.get('login') or 'No owner'
        repository = item.get('name') or 'No name'
        stargazers_count = item.get('stargazers_count') if item.get('stargazers_count') is not None else 0
        language = item.get('language') or 'Unknown'
        description = item.get('description') or 'No description'
        html_url = item.get('html_url') or 'N/A'

        print(f"\n{index}. {owner}/{repository}")
        print(f"   Description: {description}")
        print(f"   Stars: {stargazers_count}")
        print(f"   Language: {language}")
        print(f"   Link: {html_url}")


def github_trending_repos() -> None:
    """Main application entry point to orchestrate CLI argument parsing, API fetching, and display."""
    args = parse_arguments()

    try:
        data = fetch_repos(duration=args.duration, limit=args.limit)
        display_repos(data, args.duration, args.limit)
    except Exception as e:
        print(f"Error occured: {e}")


if __name__ == "__main__":
    github_trending_repos()