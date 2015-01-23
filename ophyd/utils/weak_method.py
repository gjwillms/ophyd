import weakref


class WeakMethodProxy(object):
    # ref: http://stackoverflow.com/a/24287465/1750151 by user Stick

    """
    A callable object. Takes one argument to init: 'object.method'.  Once
    created, call the instance and pass args/kwargs as you normally would.
    """
    def __init__(self, object_dot_method, quiet=True):
        self.target = weakref.proxy(object_dot_method.__self__, self._deleted)
        self.method = weakref.proxy(object_dot_method.__func__, self._deleted)

        if hasattr(self.target, 'name'):
            self.target_name = self.target.name
        else:
            self.target_name = '{}<0x{:x}>'.format(self.target.__class__.__name__, id(self.target))

        self.method_name = self.method.__name__
        self.quiet = bool(quiet)

    def _deleted(self, ref):
        self.target = self.method = None

    def __call__(self, *args, **kwargs):
        """Call the method with args and kwargs as needed."""
        try:
            if self.method is None:
                raise ReferenceError()

            return self.method(self.target, *args, **kwargs)
        except ReferenceError:
            # TODO: Target or method was deleted; what to do?
            if not self.quiet:
                raise ReferenceError('{0.target_name!r} was deleted and the corresponding method '
                                     '{0.method_name!r} is no longer accessible.'.format(self))
