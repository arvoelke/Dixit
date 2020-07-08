"""Helper file for parsing a JSON config file with comments."""

import json
import re

from copy import deepcopy

RE_REMOVE_COMMENTS = re.compile(r'\/\/[^\n]*')


def _parse(config_filename):
    """Returns the json structure in the file with the given name."""
    with open(config_filename, 'r') as config_file:
        config_json = config_file.read()
    config_json = RE_REMOVE_COMMENTS.sub('', config_json)
    return json.loads(config_json)

def _merge(old, new):
    result = deepcopy(old)
    for key, value in new.items():
        if isinstance(value, dict) and key in result:
            value = _merge(result[key], value)
        result[key] = value

    return result

def parse(default_config_filename, override_config_filename = None):
    config = _parse(default_config_filename)
    if override_config_filename:
        try:
            config = _merge(config, _parse(override_config_filename))
        except FileNotFoundError:
            pass

    return config
