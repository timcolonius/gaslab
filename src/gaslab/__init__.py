"""
gaslab
======

Educational compressible-flow utilities for perfect-gas calculations.

The package centers on :class:`gaslab.state.GasState`, which represents a
steady one-dimensional flow state. Process methods such as
``normalshock()``, ``areachg()``, ``fanno()``, ``rayleigh()``, and
``deflect()`` return new ``GasState`` objects so composite calculations can be
built by chaining operations together.

Examples
--------
Create a dimensionless air state and pass it through a normal shock::

    >>> from gaslab import GasState
    >>> s1 = GasState.init(2.0, 1.4)
    >>> s2 = s1.normalshock()
    >>> round(s2.mach, 3)
    0.577

Create a dimensional state and query the static pressure::

    >>> s = GasState.init(0.5, 1.4, p=1.0, T=300.0, mw=28.97)
    >>> round(s.pres, 3)
    1.0
"""

from .state import GasState

__all__ = ["GasState"]
