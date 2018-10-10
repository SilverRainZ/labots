from typing import List

class Message(object):
    class Origin(object):
        servername: str
        nickname: str
        username: str
        hostname: str

    command: str
    origin: Origin
    params: List[str]
