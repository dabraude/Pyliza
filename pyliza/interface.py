import typing

from . import script


def run(script_text: typing.Iterable[str]):
    liza_script = script.parse_script_file(script_text)
