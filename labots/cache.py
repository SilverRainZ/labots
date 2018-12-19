from typing import List

from sqlitedict import SqliteDict

class Cache(object):
    ''' Cache interface for bot. '''

    _db_path: str = None

    def __init__(self, db_path: str = None):
        self._db_path = db_path

    def open(self, table) -> SqliteDict:
        ''' Return a dict-like object for non-persistent read-write access. '''
        return SqliteDict(self._db_path,
                tablename = table,
                autocommit = True,
                flag = 'w') # Starts with empty table

    def view(self, table) -> SqliteDict:
        ''' Return a dict-like object for non-persistent read-only access. '''
        return SqliteDict(self._db_path,
                tablename = table,
                flag = 'r') # Starts with read-only table

    def list(self, table) -> List[str]:
        ''' Return all tables name in db. '''
        return SqliteDict.get_tablenames(table)
