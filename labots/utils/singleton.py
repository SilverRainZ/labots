class SingletonError(Exception):
    '''
    SingletonError is raised when create another instace of Singleton class.
    '''
    cls = None

    def __init__(self, cls = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cls = cls

    def __str__(self):
        return 'Class %s only allows one instance' % self.cls

class Singleton(object):
    '''
    Singleton ensure that only one instance of it exists.
    '''

    _instance = None

    def __new__(cls, *args, **kwargs):
        # Let's pray that subclass wont override __new__.
        if isinstance(cls._instance, Singleton):
            raise SingletonError(cls = cls)
        cls._instance = object.__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance
