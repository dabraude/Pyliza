import re

from .processing import ProcessingWord


class WordParser:
    tag_re = re.compile(r"\(/\s*(?P<tag>.*)\s*\)")

    @classmethod
    def parse(cls, text):
        text = text.strip()
        tagobj = cls.tag_re.fullmatch(text)
        if tagobj is None:
            return ProcessingWord(text)
        tag = tagobj.group("tag")
        return ProcessingWord(None, {tag})
