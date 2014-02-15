"""Helper file for parsing a JSON config file with comments."""

import json
import re

RE_REMOVE_COMMENTS = re.compile(r'\/\/[^\n]*')


def parse(config_filename):
    """Returns the json structure in the file with the given name."""
    with open(config_filename, 'r') as config_file:
        config_json = config_file.read()
    config_json = RE_REMOVE_COMMENTS.sub('', config_json)
    return json.loads(config_json)
