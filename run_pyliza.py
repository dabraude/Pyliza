# /usr/bin/env python3

import pathlib
import argparse
import logging

import pyliza


parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--script",
    default=open(
        pathlib.Path(__file__).parent / "1966_01_CACM_article_Eliza_script.txt"
    ),
    type=argparse.FileType(),
    help="Eliza Script File",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Increase verbostity",
)
args = parser.parse_args()

logging.basicConfig(
    level={0: logging.WARN, 1: logging.INFO}.get(args.verbose, logging.DEBUG)
)


pyliza.run_commandline(args.script)
