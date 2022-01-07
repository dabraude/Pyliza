import typing

from . import script


def run(script_text: typing.Iterable[str]):
    liza_script = script.ElizaScript(script_text)
