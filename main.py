import argparse
import requests
from datetime import datetime, timedelta


def positive_int(str_value):
    try:
        int_value = int(str_value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{str_value} must be a positive integer.")

    if int_value <= 0:
        raise argparse.ArgumentTypeError(f"{str_value} must be a positive integer.")

    return int_value

def parse_arguments(args=None):
    parser = argparse.ArgumentParser(description="CLI tool for fetching trending repos.")

    parser.add_argument(
        "-d",
        "--duration",
        type=str.lower,
        choices=["day", "week", "month", "year"],
        default="week",
        help="Duration of receiving trending repos.(Default: week)"
    )
    
    parser.add_argument(
        "-l",
        "--limit",
        type=positive_int,
        default=10,
        help="Number of receiving trending repos.(Default: 10)"
    )

    return parser.parse_args(args)


def calculate_since_date(duration):
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


def fetch_repos(duration, limit):
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
        print(f"Error: Request timed out. Please check your network and try again.")
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



def github_trending_repos():
    args = parse_arguments()

    try:
        repos = fetch_repos(duration=args.duration, limit=args.limit)
        print("fetched")
        print(len(repos))
    except Exception as e:
        print(f"Error occured: {e}")


if __name__ == "__main__":
    github_trending_repos()