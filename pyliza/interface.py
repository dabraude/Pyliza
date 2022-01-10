import logging
import typing

from .eliza import Eliza


def simulate(script: typing.Iterable[str], conversation: typing.Iterable[str]):
    """Run through a prerecorded conversation."""
    log = logging.getLogger("pyliza")
    log.info("starting up Pyliza conversation simulator")

    eliza = Eliza(script)
    eliza.greet()
    for line in map(str.strip, conversation):
        if not line or line.startswith("#"):
            continue
        print(eliza.respond_to(line), end="")


def run_commandline(script: typing.Iterable[str]):
    log = logging.getLogger("pyliza")
    log.info("starting up Pyliza command line")

    eliza = Eliza(script)

    try:
        user_response = input(eliza.greet())
        while True:
            user_response = input(eliza.respond_to(user_response))
    except (KeyboardInterrupt, EOFError):
        print("GOODBYE")
        exit()
