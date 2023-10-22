# * Singleton classes
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if args is not None and len(args) > 0:
            first_arg_value = args[0]
        elif kwargs is not None and len(kwargs) > 0:
            first_arg_name, first_arg_value = next(iter(kwargs.items()))
        else:
            raise ValueError(f"Class {cls.__name__} must have at least one argument")
        if cls._instances.get(first_arg_value) is None:
            cls._instances[first_arg_value] = super().__call__(*args, **kwargs)
        return cls._instances[first_arg_value]

    @classmethod
    def get_instance(cls, arg):
        if cls._instances.get(arg) is None:
            return None
        return cls._instances[arg]

    @classmethod
    def delete_instance(cls, arg):
        if cls._instances.get(arg) is not None:
            cls._instances[arg] = None
            del cls._instances[arg]


if __name__ == "__main__":

    class A(metaclass=SingletonMeta):
        def __init__(self, path=""):
            self.path = path

    x = A(path="path/to/folderX")
    y = A("path/to/folderY")
    z = A("path/to/folderX")
    print("x == y:", x == y)
    print("x == z:", x == z)
    d = A()
