import re

TAGS_REGEX = re.compile(r' (?=[MmLlVvHhZzCcSsQqTtAa])')
BRACKETS_REGEX = re.compile(r'[)(]')
PATH_DELIMITERS_REGEX = re.compile(r'<(?=rect|path|ellipse|g)')
NOT_WORD_REGEX = re.compile(r'\W')
WHITESPACE_REGEX = re.compile(r'(?<!,)\s+')
MULTIPLE_WHITESPACE_REGEX = re.compile(r'\s+')
