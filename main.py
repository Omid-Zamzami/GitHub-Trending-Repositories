import argparse


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


def github_trending_repos():
    args = parse_arguments()
    print(args.duration, args.limit)


if __name__ == "__main__":
    github_trending_repos()