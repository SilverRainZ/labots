def is_overridden(func) -> bool:
    return not hasattr(func, '__non_overridden')

def is_overridable(func) -> bool:
    return not hasattr(func, '__non_overridable')

def non_overridden(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__non_overridden = None
    return wrapper

def non_overridable(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__non_overridden = None
    wrapper.__non_overridable = None
    return wrapper
