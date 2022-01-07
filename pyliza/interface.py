import logging
import typing

from . import script


def run_commandline(script_text: typing.Iterable[str]):
    log = logging.getLogger("pyliza")
    log.info("starting up Pyliza command line")

    liza_script = script.ElizaScript(script_text)
    print(liza_script.greet())
