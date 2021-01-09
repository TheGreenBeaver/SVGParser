import re

MULTIPLE_WHITESPACE_REGEX = re.compile(r'[\s\n]+')
TAGS_REGEX = re.compile(r' (?=[MmLlVvHhZzCcSsQqTtAa])')
SPLIT_REGEX = re.compile(r', ?| ')
BRACKETS_REGEX = re.compile(r'[)(]')
PATH_DELIMITERS_REGEX = re.compile(r'<(?=rect|path|ellipse|/?g)')
NOT_WORD_REGEX = re.compile(r'\W')

SMALL = 'SMALL'
LARGE = 'LARGE'
