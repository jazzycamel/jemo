import argparse

from . import logger
from .jemo import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Emulate Belkin WeMo devices for use with Amazon Echo"
    )
    parser.add_argument(
        "-c", "--config", required=True, help="Specify path to config file"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase verbosity (may increase up to -vvv)",
        action="count",
        default=0,
    )
    args = parser.parse_args()

    # 40-10*0=40==logging.ERROR
    verbosity = max(40 - 10 * args.verbose, 10)
    logger.setLevel(verbosity)

    main(config_file_path=args.config)
