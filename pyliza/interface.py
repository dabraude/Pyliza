import logging
import typing

from . import eliza


def run_commandline(script: typing.Iterable[str]):
    log = logging.getLogger("pyliza")
    log.info("starting up Pyliza command line")

    cmd_eliza = eliza.Eliza(script)

    try:
        cmd_eliza.respond_to("Hello I'm sad.")
        # user_response = input(cmd_eliza.greet())
        # cmd_eliza.respond_to("Hello I'm sad.")
        # while True:
        #     user_response = input(cmd_eliza.respond_to(user_response))
    except (KeyboardInterrupt, EOFError):
        print("GOODBYE")
        exit()
