from typing import List

from sqlitedict import SqliteDict

class Storage(object):
    ''' Storage interface for bot. '''

    _db_path: str = None

    def __init__(self, db_path: str = None):
        self._db_path = db_path

    def open(self, table) -> SqliteDict:
        ''' Return a dict-like object for persistent read-write access. '''
        return SqliteDict(self._db_path,
                tablename = table,
                autocommit = True,
                flag = 'c')

    def view(self, table) -> SqliteDict:
        ''' Return a dict-like object for persistent read-only access. '''
        return SqliteDict(self._db_path,
                tablename = table,
                flag = 'r') # Starts with read-only table

    def list(self, table) -> List[str]:
        ''' Return all tables name in db. '''
        return SqliteDict.get_tablenames(table)
