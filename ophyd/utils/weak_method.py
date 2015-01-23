import inspect
import weakref


class FunctionProxy(object):
    # ref: http://stackoverflow.com/a/24287465/1750151 by user Stick

    def __init__(self, obj_method, remove_cb=None, quiet=True):
        """
        A callable, weak-referenced function proxy.  Takes either a method or a
        function.

        Call this instance and pass args/kwargs as you normally would.
        """

        if inspect.ismethod(obj_method):
            self.target = weakref.proxy(obj_method.__self__, self._deleted)
            if hasattr(self.target, 'name'):
                self.target_name = self.target.name
            else:
                self.target_name = '{}<0x{:x}>'.format(self.target.__class__.__name__, id(self.target))
            self.method = weakref.proxy(obj_method.__func__, self._deleted)
        else:
            self.target = None
            self.target_name = None
            self.method = weakref.proxy(obj_method, self._deleted)

        self.method_name = self.method.__name__
        self.quiet = bool(quiet)
        self.remove_cb = remove_cb

    def _deleted(self, ref):
        self.target = self.method = None

        if self.remove_cb is not None:
            self.remove_cb(self)
            self.remove_cb = None

    def __call__(self, *args, **kwargs):
        """Call the method with args and kwargs as needed."""
        try:
            if self.method is None:
                raise ReferenceError()

            if self.target is None:
                return self.method(*args, **kwargs)
            else:
                return self.method(self.target, *args, **kwargs)

        except ReferenceError:
            # TODO: Target or method was deleted; what to do?
            if not self.quiet:
                if not self.target_name:
                    raise ReferenceError('Function {0.method_name!r} was garbage collected and '
                                         'is no longer accessible.'.format(self))

                raise ReferenceError('{0.target_name!r} was deleted and the corresponding method '
                                     '{0.method_name!r} is no longer accessible.'.format(self))
