import re

from . import ruleset, transformation, processing, utils
from .transformation import ReassemblyRule, DecompositionRule
from .processing import ProcessingWord

from .processing_parser import WordParser


class DecompositionParser:
    @classmethod
    def parse(cls, text) -> DecompositionRule:
        return DecompositionRule(list(cls._parts(text)))

    @classmethod
    def _parts(cls, text):
        text = text.strip()
        while text:
            part, text = cls._options_part(text)
            if part is None:
                part, text = cls._next_part(text)
            yield part

    @classmethod
    def _options_part(cls, text):
        part = None
        if text.startswith("(*"):
            part, endpos = utils.get_bracketed_text(text)
            part = set(map(WordParser.parse, part[1:].strip().split()))
            text = text[endpos:]
        return part, text

    @classmethod
    def _next_part(cls, text):
        mobj = re.match(r"\S+", text)
        try:
            part = int(mobj.group())
        except ValueError:
            part = WordParser.parse(mobj.group())
        text = text[mobj.end() :].lstrip()
        return part, text


class ReassemblyParser:
    rule_re = re.compile(r"(\d)")
    linkage_re = re.compile(r"=\S+")
    transform_linkage_re = re.compile(r"PRE\s+\((?P<assem>.*?)\)\s+\(=(?P<link>\S+)\)$")

    @classmethod
    def parse(cls, text) -> ReassemblyRule:
        if cls.linkage_re.match(text):
            return cls._parse_link(text)
        if cls.transform_linkage_re.match(text):
            return cls._parse_transform_link(text)
        return cls._parse_standard(text)

    @classmethod
    def _parse_reassembly_rule(cls, text):
        def _convert(part):
            try:
                return int(part)
            except ValueError:
                return [processing.ProcessingWord(w) for w in part.split()]

        assembly_parts = list(
            map(_convert, filter(len, map(str.strip, cls.rule_re.split(text))))
        )
        return assembly_parts

    @classmethod
    def _parse_standard(cls, text):
        assembly_parts = cls._parse_reassembly_rule(text)
        return ruleset.ReassemblyRule(assembly_parts, None)

    @classmethod
    def _parse_link(cls, text):
        return transformation.ReassemblyRule(None, processing.ProcessingWord(text[1:]))

    @classmethod
    def _parse_transform_link(cls, text):
        rule = cls.transform_linkage_re.match(text)
        assembly = cls._parse_reassembly_rule(rule.group("assem"))
        link = processing.ProcessingWord(rule.group("link"))
        return transformation.ReassemblyRule(assembly, link)
