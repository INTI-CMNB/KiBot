# -*- coding: utf-8; -*-

__all__ = ["Bunch", "bunchify"]

from collections.abc import Mapping, MutableMapping, Container, Iterable, Sized

class Bunch:
    """A bunch of named values.

    Can be used instead of a `dict` when `b.someattr` is more readable than
    `d['somekey']`. In terms of `collections.abc`, a `MutableMapping`,
    `Container`, `Iterable`, `Sized`.

    Example::

        b = Bunch(cat="meow", dog="woof")
        assert b.cat == "meow"
        assert b.dog == "woof"
    """
    def __init__(self, **bindings):
        self._data = bindings
        self._reserved_names = []
        self._reserved_names = dir(self)

    def copy(self):
        """Return a copy of this `Bunch`."""
        return Bunch(**{k: v for k, v in self._data.items()})
    def replace(self, other):
        """Replace all data in this `Bunch` with data from the `other` one (shallow-copying it)."""
        if not isinstance(other, Bunch):
            raise TypeError(f"expected Bunch, got {type(other)} with value {repr(other)}")
        self._data = other.copy()._data

    def __getattr__(self, name: str):
        return self._data[name]
    def __setattr__(self, name: str, value):
        if name in ("_data", "_reserved_names"):
            return super().__setattr__(name, value)
        if name in self._reserved_names:  # prevent shadowing get, pop, et al.
            raise AttributeError(f"Cannot write to reserved attribute '{name}'")
        self._data[name] = value
    def __delattr__(self, name: str):
        del self._data[name]

    # Container, Iterable, Sized
    def __contains__(self, name: str):
        return self._data.__contains__(name)
    def __iter__(self):
        return self._data.__iter__()
    def __len__(self):
        return len(self._data)

    # Mapping
    def __getitem__(self, name: str):
        return self._data.__getitem__(name)
    def __setitem__(self, name: str, value):
        return self._data.__setitem__(name, value)
    def __delitem__(self, name: str):
        return self._data.__delitem__(name)
    def keys(self):
        return self._data.keys()
    def items(self):
        return self._data.items()
    def values(self):
        return self._data.values()
    def get(self, name: str, default=None):
        return self[name] if name in self else default
    def __eq__(self, other):
        return other == self._data
    def __ne__(self, other):
        return other != self._data

    # MutableMapping
    def pop(self, name: str, *default):
        return self._data.pop(name, *default)
    def popitem(self):
        return self._data.popitem()
    def clear(self):
        return self._data.clear()
    def update(self, **bindings):
        self._data.update(**bindings)
    def setdefault(self, name: str, *default):
        return self._data.setdefault(name, *default)

    def __repr__(self) -> str:  # pragma: no cover
        bindings = [f"{name:s}={repr(value)}" for name, value in self._data.items()]
        args = ", ".join(bindings)
        return f"Bunch({args})"


# Register virtual abstract base classes.
_virtual_bases = (Mapping, MutableMapping, Container, Iterable, Sized)
for abscls in _virtual_bases:
    abscls.register(Bunch)
del abscls


def bunchify(d):
    """Convert a mapping into a `Bunch`.

    The use case is as a shim, to refer to the contents of a dictionary using
    attribute access syntax::

        d = {"foo": "variable", "bar": "tavern"}
        b = bunchify(d)
        assert b.foo == "variable"
        assert b.bar == "tavern"

    No copy. The original mapping itself is used as the bunch's data storage.

    If you need to copy and efficiently convert the result into a bunch,
    use something like `bunchify(dict(d))` or `bunchify(copy.copy(d))`.

    `d` can be `dict`, but also any mapping that behaves similarly enough.
    The type check passes if `d` implements, from `collections.abc`, the APIs
    `Container`, `Iterable`, `Sized`, `Mapping`, and `MutableMapping` (that is,
    exactly those APIs that `dict` itself implements).

    Each key in `d` must be a valid identifier.

    Return value is the `Bunch` instance with `d` as its data. If `d` is
    already a `Bunch`, then the return value is `d` itself.
    """
    if isinstance(d, Bunch):
        return d
    if not all(isinstance(d, cls) for cls in _virtual_bases):
        raise TypeError(f"`d` did not declare it implements the expected APIs ({_virtual_bases}); got {type(d)} with value {repr(d)}")
    if not all(x.isidentifier() for x in d):
        invalid_keys = [x for x in d if not x.isidentifier()]
        invalid_keys_msg = ", ".join(repr(x) for x in invalid_keys)
        raise ValueError(f"`d` has one or more keys that are not valid identifiers: {invalid_keys_msg}")
    b = Bunch()
    b._data = d
    return b
