"""
Utils for checking dict format config.
"""

import logging
from typing import List, Dict, Any

# Initialize logging
logger = logging.getLogger(__name__)

class Item():
    """ """
    key: List[str]
    checkers: List[Any] # Checkers can be function or value.
    default: Any
    required: bool

    def __init__(self,
            key = None,
            checkers = None,
            default = None,
            required = False):
        self.key = key
        self.checkers = checkers
        self.default = default
        self.required = required

def check(d: Dict, items: List[Item]):
    """
    Check whether the dict is satisfied with the constraint of Item list.
    """

    for item in items:
        cur = d
        key = None
        dkey = '.'.join(item.key)
        val = None

        logger.debug('Finding configuration %s', repr(dkey))

        # Get value of key list
        for ki, key in enumerate(item.key):
            # Alway create key if not exists
            if not key in cur:
                cur[key] = None

            if ki != len(item.key) - 1:
                # Alway creates next level
                if cur[key] == None:
                    cur[key] = {}
                cur = cur[key]
            else:
                val = cur[key]

        found = val != None
        if not found:
            # Set default value if not found
            if item.default != None:
                logger.debug('Configuration %s is set to default value %s',
                        repr(dkey), item.default)
                cur[key] = item.default
            elif item.required:
                raise KeyError('Configuration %s is required but not found' %
                        repr(dkey))
            else:
                # Skip non-found and non-required configuration
                continue

        # Apply value checkers
        for chk in item.checkers:
            logger.debug('Applying checker %s', chk.__name__)
            if not chk(val):
                if item.default != None:
                    logger.debug('Configuration %s is set to default value %s',
                            repr(dkey), item.default)
                    cur[key] = item.default
                else:
                    raise ValueError('Configuration %s is not satisfiy %s' %
                        (repr(dkey), chk.__name__))

"""
Checker implements.
"""

def is_not_none(v: Any) -> bool:
    return v != None

def is_bool(v: Any) -> bool:
    return isinstance(v, bool)

def is_int(v: Any) -> bool:
    return isinstance(v, int)

def is_str(v: Any) -> bool:
    return isinstance(v, str)

def is_not_empty_str(v) -> bool:
    if not is_str(v):
        return False
    return v.strip() != ""

def is_port(v: Any) -> bool:
    if not is_int(v):
        return False
    return v > 0 and v <= 65535
