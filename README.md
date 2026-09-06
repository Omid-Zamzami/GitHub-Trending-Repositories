# GitHub Trending Repositories

A lightweight Python command-line tool for discovering recently created GitHub repositories and ranking them by star count.

The application uses the GitHub Search API to find repositories created within a selected time window, sorts the results by stars in descending order, and prints repository details directly to the terminal.

> **Repository:** [Omid-Zamzami/GitHub-Trending-Repositories](https://github.com/Omid-Zamzami/GitHub-Trending-Repositories)

## Features

- Command-line interface with short and long options.
- Supports four time windows:
  - `day` — repositories created within the last 1 day.
  - `week` — repositories created within the last 7 days.
  - `month` — repositories created within the last 30 days.
  - `year` — repositories created within the last 365 days.
- Configurable number of repositories to display.
- Results are requested from the GitHub Search API and sorted by star count in descending order.
- No GitHub token or local configuration file is required by the current implementation.
- Ten-second request timeout.
- Graceful handling of common network, HTTP, and JSON parsing failures.
- Safe fallback values when repository fields are missing or `None`.
- Unit tests covering argument parsing, validation, date calculation, API requests, error handling, output formatting, and application orchestration.

## How It Works

The CLI follows a simple pipeline:

1. Parse command-line arguments.
2. Calculate the date boundary from the selected duration.
3. Query GitHub's repository Search API with a query equivalent to `created:>YYYY-MM-DD`.
4. Sort results by stars in descending order.
5. Display each repository with its owner, name, description, star count, primary language, and GitHub URL.
6. Return an empty result set and print an error message when supported API/network failures occur.

The current implementation searches for **recently created repositories** and ranks them by total stars. It does not scrape or reproduce GitHub's website-level Trending page.

## Requirements

- Python **3.10 or newer**
- Internet access to reach `api.github.com`

The project dependencies are:

| Package | Purpose |
| --- | --- |
| `requests>=2.31.0` | HTTP requests to the GitHub API |
| `pytest>=8.0.0` | Development and test framework |

Python 3.10+ is required because the source code uses modern type hints such as `list[str]` and the `match/case` statement.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Omid-Zamzami/GitHub-Trending-Repositories.git
cd GitHub-Trending-Repositories
```

### 2. Create a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Usage

Run the application without arguments to use the defaults:

```bash
python main.py
```

Default behavior:

- Duration: `week`
- Limit: `10`

### Specify the duration

```bash
python main.py --duration day
```

Short option:

```bash
python main.py -d day
```

Supported duration values are:

```text
day
week
month
year
```

The duration input is case-insensitive, so this is also valid:

```bash
python main.py --duration DAY
```

### Specify the number of repositories

```bash
python main.py --limit 20
```

Short option:

```bash
python main.py -l 20
```

The limit must be a positive integer greater than zero.

### Combine options

```bash
python main.py --duration month --limit 25
```

Or:

```bash
python main.py -d year -l 50
```

### View command-line help

```bash
python main.py --help
```

The CLI exposes these arguments:

| Option | Long form | Default | Description |
| --- | --- | ---: | --- |
| `-d` | `--duration` | `week` | Time window: `day`, `week`, `month`, or `year` |
| `-l` | `--limit` | `10` | Number of repositories to request/display; must be a positive integer |

## Example Output

A successful run produces output similar to:

```text
GitHub Trending Repositories
Duration: week
Showing: 10 repositories

1. octocat/example-repository
   Description: An example GitHub repository
   Stars: 1500
   Language: Python
   Link: https://github.com/octocat/example-repository
```

When no repositories are available to display:

```text
No repositories to display.
```

## GitHub API

The application calls the GitHub repository Search API endpoint:

```text
https://api.github.com/search/repositories
```

The request uses parameters equivalent to:

```text
q=created:>YYYY-MM-DD
sort=stars
order=desc
per_page=<limit>
```

A custom user-agent is also sent:

```text
GitHub-Trending-Repos
```

The request timeout is fixed at **10 seconds**.

### API Authentication

The current source code does not implement GitHub authentication or token loading. No `GITHUB_TOKEN` environment variable is read by the application.

Because the application uses GitHub's public API without an authentication mechanism in the current code, API availability and request limits are determined by GitHub.

## Error Handling

`fetch_repos()` handles these cases and returns an empty list when they occur:

- Request timeout
- Connection failure
- HTTP errors
- Other `requests`-level request errors
- Invalid/unparseable JSON responses

The CLI also has top-level exception handling in `github_trending_repos()` so unexpected application exceptions are printed instead of terminating without a message.

## Project Structure

The repository currently contains the following key files:

```text
GitHub-Trending-Repositories/
├── main.py
├── test_main.py
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

### `main.py`

Contains the application logic:

- `positive_int()` — validates positive integer CLI values.
- `parse_arguments()` — defines and parses CLI arguments.
- `calculate_since_date()` — calculates the start date for each supported duration.
- `fetch_repos()` — calls the GitHub Search API and handles request failures.
- `display_repos()` — formats repository information for terminal output.
- `github_trending_repos()` — coordinates the application flow.

### `test_main.py`

Contains the automated test suite for the application's core behavior.

### `requirements.txt`

Lists runtime and development/test dependencies.

### `.gitignore`

Excludes Python cache files, virtual environments, pytest/coverage artifacts, IDE metadata, operating-system files, and `.env` files.

### `LICENSE`

The project is released under the **MIT License**.

## Running the Tests

Install the development dependencies first:

```bash
python -m pip install -r requirements.txt
```

Then run:

```bash
pytest
```

For a more verbose test run:

```bash
pytest -v
```

### Test Coverage

The test suite currently verifies:

- Positive integer validation.
- Rejection of zero, negative numbers, and non-integer values.
- Default CLI argument values.
- All supported duration values.
- Both short and long CLI options.
- Case-insensitive duration parsing.
- Invalid duration handling.
- Invalid limit handling.
- Date calculation for day/week/month/year inputs.
- Fallback date behavior for an unknown duration passed directly to the date-calculation function.
- Successful GitHub API requests, including request URL, query parameters, headers, and timeout.
- HTTP error handling for representative status codes.
- Invalid JSON handling.
- Timeout, connection, and generic request exceptions.
- Empty-result output.
- Normal repository output formatting.
- Output fallbacks for missing or `None` repository fields.
- Correct orchestration between argument parsing, API fetching, and output rendering.
- Top-level exception handling in the application entry point.

The tests mock network calls and date/time dependencies where appropriate, so the suite does not require live GitHub API requests.

## Development Notes

### No persistent application state

The application is stateless. It does not create a database, save API results, or write repository data to local files.

### Date windows

The date ranges are implemented as fixed day offsets from the current local date/time:

| Duration | Offset |
| --- | ---: |
| `day` | 1 day |
| `week` | 7 days |
| `month` | 30 days |
| `year` | 365 days |

The GitHub Search query uses the resulting date with the `created:>` qualifier.

### Result formatting

For missing data, the output layer uses these fallbacks:

| Field | Fallback |
| --- | --- |
| Owner | `No owner` |
| Repository name | `No name` |
| Stars | `0` |
| Language | `Unknown` |
| Description | `No description` |
| URL | `N/A` |

## Code Quality and Testing Approach

The project separates the main responsibilities into small functions, making the application easier to test and maintain.

External API calls are mocked in the test suite instead of relying on live GitHub responses. Date/time behavior is also mocked for deterministic date-calculation tests.

This keeps the automated tests fast and repeatable while still checking the exact API request parameters used by the application.

## Troubleshooting

### `python: command not found`

Make sure Python is installed and available on your `PATH`. On some systems, use `python3` instead of `python`.

### Dependency import errors

Activate your virtual environment and reinstall the dependencies:

```bash
python -m pip install -r requirements.txt
```

### GitHub connection errors

The application requires outbound internet access to `api.github.com`. Check your network connection, firewall, proxy, or DNS configuration.

### Request timeout

The API request has a fixed 10-second timeout. A timeout message indicates that a response was not received within that period.

### HTTP errors

A non-successful GitHub API response is caught and reported by the application. The application does not currently implement retries, authentication, or advanced rate-limit recovery.

## Contributing

Contributions are welcome.

A typical contribution workflow is:

1. Fork the repository.
2. Create a feature or bug-fix branch.
3. Make your changes.
4. Add or update tests for changed behavior.
5. Run the test suite with `pytest`.
6. Commit your changes with a clear message.
7. Open a pull request against the main repository.

Please keep changes focused and maintain the existing separation between CLI parsing, date calculation, API access, output formatting, and orchestration.

## Issues and Feature Requests

For bugs, improvements, and feature requests, please use the repository's GitHub Issues section:

[Open an issue on GitHub](https://github.com/Omid-Zamzami/GitHub-Trending-Repositories/issues)

## Security and Secrets

Do not commit API tokens, credentials, or other secrets to the repository.

The project's `.gitignore` already excludes `.env` files and common local-development artifacts. If future features introduce environment-based credentials, keep them outside source control.

## License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for the full license text.

Copyright (c) 2026 Omid-Zamzami.

## Author

**Omid-Zamzami**

- GitHub: [@Omid-Zamzami](https://github.com/Omid-Zamzami)
- Repository: [GitHub-Trending-Repositories](https://github.com/Omid-Zamzami/GitHub-Trending-Repositories)

---

## Disclaimer

This project is an independent command-line utility that uses GitHub's public API. It is not affiliated with or endorsed by GitHub.
