import inspect

def current_func_name(): 
    try:
        frame = inspect.stack()[1]
    except Exception:
        return '<unknown>'
    return frame.function
