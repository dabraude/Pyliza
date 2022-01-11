import logging
import typing
import enum

from .eliza import Eliza


class TerminalColours:
    ELIZA = 96
    USER = 95


def print_colour(text: str, colour_code: int, *args, **kwargs):
    print(f"\033[{colour_code}m" + text + f"\033[0m", *args, **kwargs)


def simulate(script: typing.Iterable[str], conversation: typing.Iterable[str]):
    """Run through a prerecorded conversation."""
    log = logging.getLogger("pyliza")
    log.info("starting up Pyliza conversation simulator")

    eliza = Eliza(script)
    print_colour(eliza.greet(), TerminalColours.ELIZA, end="")
    for line in map(str.strip, conversation):
        if not line or line.startswith("#"):
            continue
        # eliza.respond_to(line)
        print_colour(line, TerminalColours.USER)
        print_colour(eliza.respond_to(line), TerminalColours.ELIZA, end="")


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
