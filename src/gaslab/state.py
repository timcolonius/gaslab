"""
Core gas-dynamic state representation for the Python port of Gaslab.

The :class:`GasState` class stores a steady-flow state for a calorically
perfect gas. It supports both nondimensional and dimensional initialization
and implements the major process operations from the MATLAB version as methods
that return new ``GasState`` objects.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Optional

from .defaults import Defaults
from .relations import pbyp0, tbyt0


@dataclass
class GasState:
    """
    Gas-dynamic flow state used throughout :mod:`gaslab`.

    A state represents steady unidirectional flow at a station. There are two
    supported initialization modes:

    - Nondimensional mode: specify ``m`` and ``gamma`` only.
    - Dimensional mode: specify ``m``, ``gamma``, ``p``, ``T``, and ``mw``.

    In dimensional mode, the supplied static pressure and temperature define
    the reference stagnation quantities associated with the initialized state.
    Subsequent states preserve that reference so dimensional query properties
    remain in physical units.

    Notes
    -----
    Dynamic state variables are ``m``, ``p0``, ``t0``, ``angle``, and
    ``proc``. Static metadata carried through all descendant states are
    ``gamma``, ``p0r``, ``t0r``, ``gcon``, and ``dimmode``.

    Process methods do not mutate the current state. Each process returns a
    new :class:`GasState` whose ``hist`` pointer references the previous state,
    allowing composite processes to be inspected later.

    Parameters
    ----------
    m : float
        Mach number.
    gamma : float
        Ratio of specific heats for the gas.
    p : float, optional
        Static pressure of the initialized state. In dimensional mode this is
        given in atm.
    T : float, optional
        Static temperature of the initialized state. In dimensional mode this
        is given in K.
    mw : float, optional
        Molecular weight in g/mol for dimensional calculations.
    """

    # required inputs
    m: float # mach number (dynamic)
    gamma: float # required input (static)

    # optional inputs
    p: Optional[float] = None # optional input, reservoir pressure (dimensional)
    T: Optional[float] = None # optionalinput, reservoir temperature (dimensional)
    mw: Optional[float] = None # optional input, gas molecular weight (dimensional)

    # dynamic state variables
    p0: float = 1.0 # stagnation pressure (nondim)
    t0: float = 1.0 # stagnation temperature (nondim)
    angle: float = 0.0 # flow angle
    proc: str = "initstate" # last process

    # static metadata
    dimmode: bool = False # dimensional (1) or nondimensional (0), determined  based on optional inputs
    gcon: float = 1.0 # gas constant (unity in nondimensional mode, 8314/mw in dimensional mode)
    p0r: float = 1.0 # resevoir stagnation pressure (unity in nondimensional mode)
    t0r: float = 1.0 # resevoir stagnation temperature (unity in nondimensional mode)

    # history
    hist: Optional["GasState"] = None

    # defaults
    defaults: Defaults = field(default_factory=Defaults)

    def __post_init__(self):
        """
        Validate the initial state and derive dimensional reference data.
        """
        if not (1.0 < self.gamma < 2.0):
            raise ValueError("gamma must be between 1 and 2")

        if self.m < 0:
            raise ValueError("Mach number must be positive")

        if self.p is not None:
            if None in (self.T, self.mw):
                raise ValueError("p, T, and mw must be supplied together")

            if self.p <= 0 or self.T <= 0:
                raise ValueError("pressure and temperature must be positive")

            if self.mw < 2:
                raise ValueError("molecular weight must be >= 2")

            self.dimmode = True
            self.p0r = self.p / pbyp0(self.m, self.gamma)
            self.t0r = self.T / tbyt0(self.m, self.gamma)
            self.gcon = 8314.0 / self.mw
      
    @classmethod
    def init(cls, m, gamma, p=None, T=None, mw=None):
        """
        Construct an initial gas state.

        This classmethod mirrors the MATLAB constructor usage while providing
        a more explicit entry point for Python users.

        Parameters
        ----------
        m : float
            Mach number.
        gamma : float
            Ratio of specific heats.
        p : float, optional
            Static pressure in atm for dimensional mode.
        T : float, optional
            Static temperature in K for dimensional mode.
        mw : float, optional
            Molecular weight in g/mol for dimensional mode.

        Returns
        -------
        GasState
            Newly initialized state.
        """
        return cls(m=m, gamma=gamma, p=p, T=T, mw=mw)


    
    def normalshock(self):
        """
        Return the downstream state reached by a normal shock.

        The upstream Mach number must be supersonic. Stagnation temperature is
        unchanged, while stagnation pressure decreases through the shock.

        Returns
        -------
        GasState
            Downstream state.

        Raises
        ------
        ValueError
            If the current Mach number is subsonic.
        """

        from .relations import normalshock_M2, nspr, pbyp0

        if self.m < 1:
            raise ValueError("normalshock: M > 1 is required")

        s2 = GasState(self.m, self.gamma)

        # copy state / inherited metadata
        s2.hist = self
        s2.angle = self.angle
        s2.p0r = self.p0r
        s2.t0r = self.t0r
        s2.gcon = self.gcon
        s2.dimmode = self.dimmode
        s2.defaults = self.defaults

        # process update
        s2.m = normalshock_M2(self.m, self.gamma)
        s2.t0 = self.t0
        s2.p0 = self.p0 * nspr(self.m, self.gamma) * pbyp0(self.m, self.gamma) / pbyp0(s2.m, self.gamma)
        s2.proc = "normalshock"

        return s2

    def fanno(self, fric: float):
        """
        Quasi-one-dimensional constant-area flow with friction.

        The input parameter is the nondimensional Fanno friction factor

        ``fric = 4 f L / D``.

        The process moves the state toward sonic conditions. If the specified
        friction factor exceeds the critical value needed to choke the flow,
        an exception is raised.

        Parameters
        ----------
        fric : float
            Nondimensional friction factor ``4 f L / D``.

        Returns
        -------
        GasState
            Downstream Fanno state.

        Raises
        ------
        ValueError
            If the requested friction factor would choke the flow before the
            end of the duct.
        """
        from .relations import fstar, mach_from_fstar

        f2 = fstar(self.m, self.gamma) - fric
        if f2 < 0:
            raise ValueError("Flow is choked at a smaller friction factor than specified")

        s2 = GasState(self.m, self.gamma)

        s2.hist = self
        s2.angle = self.angle
        s2.p0r = self.p0r
        s2.t0r = self.t0r
        s2.gcon = self.gcon
        s2.dimmode = self.dimmode
        s2.defaults = self.defaults

        s2.m = mach_from_fstar(f2, self.gamma, self.m, small=self.defaults.small)
        exponent = (self.gamma + 1) / (2 * self.gamma)
        s2.p0 = (
            self.p0
            * self.m
            * (pbyp0(self.m, self.gamma) / pbyp0(s2.m, self.gamma)) ** exponent
            / s2.m
        )
        s2.t0 = self.t0
        s2.proc = "fanno"

        return s2

    def rayleigh(self, t0ratio: float):
        """
        Quasi-one-dimensional constant-area flow with heat transfer.

        The specified ratio is

        ``t0ratio = T0_2 / T0_1``.

        This process models heat addition or removal in a constant-area duct.
        As with the MATLAB version, the process is limited by the choking
        condition at Mach 1.

        Parameters
        ----------
        t0ratio : float
            Desired stagnation-temperature ratio.

        Returns
        -------
        GasState
            Downstream Rayleigh state.

        Raises
        ------
        ValueError
            If the requested heat addition would choke the flow.
        """
        from .relations import mach_from_t0star, t0star

        f2 = t0ratio * t0star(self.m, self.gamma)
        if f2 > 1:
            raise ValueError("Flow is choked with less heat addition than specified")

        s2 = GasState(self.m, self.gamma)

        s2.hist = self
        s2.angle = self.angle
        s2.p0r = self.p0r
        s2.t0r = self.t0r
        s2.gcon = self.gcon
        s2.dimmode = self.dimmode
        s2.defaults = self.defaults

        s2.m = mach_from_t0star(f2, self.gamma, self.m, small=self.defaults.small)
        s2.t0 = self.t0 * t0ratio
        s2.p0 = (
            self.p0
            * (1 + self.gamma * self.m**2)
            * pbyp0(self.m, self.gamma)
            / pbyp0(s2.m, self.gamma)
            / (1 + self.gamma * s2.m**2)
        )
        s2.proc = "rayleigh"

        return s2

    def deflect(self, ang: float, fam: int = 1, strong: bool = False):
        """
        Turn a supersonic stream through an oblique shock or PM expansion.

        A positive deflection in the selected wave family corresponds to a
        compression and is solved as an oblique shock. A negative deflection
        corresponds to a Prandtl-Meyer expansion.

        Parameters
        ----------
        ang : float
            Signed deflection angle in radians, relative to the current flow
            direction.
        fam : int, default 1
            Wave family. Use ``+1`` for left-running waves and ``-1`` for
            right-running waves.
        strong : bool, default False
            If ``True``, use the strong oblique-shock branch when a shock
            solution exists.

        Returns
        -------
        GasState
            Deflected downstream state.

        Raises
        ------
        ValueError
            If the upstream flow is subsonic or if no valid shock/expansion
            solution exists for the requested turning angle.
        """
        from .relations import oblique, prandtlmeyer

        if self.m < 1:
            raise ValueError("deflect: M > 1 is required for supersonic flow turning")

        s2 = GasState(self.m, self.gamma)

        s2.hist = self
        s2.p0r = self.p0r
        s2.t0r = self.t0r
        s2.gcon = self.gcon
        s2.dimmode = self.dimmode
        s2.defaults = self.defaults

        if ang * fam > 0:
            beta, mn1, m2 = oblique(self.m, abs(ang), self.gamma, strong=strong, small=self.defaults.small)
            if beta is None:
                raise ValueError("deflect: no oblique shock solution for the specified turn")

            s2.m = m2
            s2.p0 = (
                self.p0
                * pbyp0(self.m, self.gamma)
                * (1 + 2 * self.gamma / (self.gamma + 1) * (mn1**2 - 1))
                / pbyp0(s2.m, self.gamma)
            )
            s2.t0 = self.t0
            s2.angle = self.angle + ang
            s2.proc = f"oblique shock ({math.degrees(beta):.2f} deg)"
        else:
            s2.m = prandtlmeyer(self.m, abs(ang), self.gamma, small=self.defaults.small)
            s2.p0 = self.p0
            s2.t0 = self.t0
            s2.angle = self.angle + ang
            s2.proc = "pm expansion"

        return s2
    
    def areachg(self, ar, throat=False):
        """
        Quasi-one-dimensional isentropic area change.

        The area ratio is defined as

        ``ar = A_2 / A_1``.

        For steady isentropic flow, not every area ratio is reachable from a
        given state. The limiting case corresponds to sonic flow at the
        critical area ``A*``.

        Parameters
        ----------
        ar : float
            New area divided by old area.
        throat : bool, default False
            If ``True``, a throat lies between the old and new states, so the
            solution branch switches from subsonic to supersonic or vice
            versa.

        Returns
        -------
        GasState
            Downstream isentropic state.

        Raises
        ------
        ValueError
            If the requested area change would imply an area smaller than the
            critical area.
        """

        from .relations import arstar, mach_from_arstar

        if self.m == 1 and not throat:
            print("Warning: input Mach number is 1 and no throat specified; subsonic branch chosen")

        if throat:
            subsonic = self.m > 1
        else:
            subsonic = self.m <= 1

        a2 = ar * arstar(self.m, self.gamma)

        if a2 < 1:
            raise ValueError("Area ratio is invalid: it reduces the area below the critical area")

        s2 = GasState(self.m, self.gamma)

        # copy static / inherited data
        s2.hist = self
        s2.angle = self.angle
        s2.p0r = self.p0r
        s2.t0r = self.t0r
        s2.gcon = self.gcon
        s2.dimmode = self.dimmode
        s2.defaults = self.defaults

        # process update
        s2.m = mach_from_arstar(a2, self.gamma, subsonic=subsonic, small=self.defaults.small)
        s2.p0 = self.p0
        s2.t0 = self.t0
        s2.proc = "areachg"

        return s2


    def history(self):
        """
        Iterate through the state history from initial state to current.

        Yields
        ------
        GasState
            States in chronological order, beginning with the initialized
            state and ending with the current state.
        """

        stack = []
        s = self

        while s is not None:
            stack.append(s)
            s = s.hist

        for s in reversed(stack):
            yield s
   
    def __iter__(self):
        return self.history() 
  
    @property
    def mach(self) -> float:
        """Mach number of the current state."""
        return self.m

    @property
    def stagpres(self) -> float:
        """Stagnation pressure.

        In nondimensional mode this is relative to the initialized stagnation
        pressure. In dimensional mode the value is returned in atm.
        """
        return self.p0r * self.p0

    @property
    def stagtemp(self) -> float:
        """Stagnation temperature.

        In nondimensional mode this is relative to the initialized stagnation
        temperature. In dimensional mode the value is returned in K.
        """
        return self.t0r * self.t0

    @property
    def pres(self) -> float:
        """Static pressure.

        In nondimensional mode this is ``p / p0_i``. In dimensional mode the
        value is returned in atm.
        """
        return self.p0r * self.p0 * pbyp0(self.m, self.gamma)

    @property
    def temp(self) -> float:
        """Static temperature.

        In nondimensional mode this is ``T / T0_i``. In dimensional mode the
        value is returned in K.
        """
        return self.t0r * self.t0 * tbyt0(self.m, self.gamma)

    @property
    def density(self) -> float:
        """Density.

        In nondimensional mode this is relative to the initialized stagnation
        density. In dimensional mode the value is returned in kg/m^3.
        """
        con = 101325.0 if self.dimmode else 1.0
        return con * (self.pres / self.temp) / self.gcon

    @property
    def entropy(self) -> float:
        """Nondimensional entropy change relative to the initialized state."""
        fac = (self.gamma - 1) / self.gamma
        return math.log(self.temp / self.t0r) - fac * math.log(self.pres / self.p0r)

    @property
    def soundsp(self) -> float:
        """Local speed of sound.

        In nondimensional mode this is relative to the initialized stagnation
        sound speed. In dimensional mode the value is returned in m/s.
        """
        con = self.gamma * self.gcon if self.dimmode else 1.0
        return math.sqrt(con * self.temp)

    @property
    def speed(self) -> float:
        """Flow speed magnitude."""
        return self.m * self.soundsp

    @property
    def t0rcrit(self) -> float:
        """Critical Rayleigh stagnation-temperature ratio ``T0 / T0*``."""
        from .relations import t0star

        return t0star(self.m, self.gamma)

    @property
    def arcrit(self) -> float:
        """Critical area ratio ``A / A*`` for isentropic flow."""
        from .relations import arstar

        return arstar(self.m, self.gamma)

    @property
    def fcrit(self) -> float:
        """Critical Fanno friction parameter needed to reach choking."""
        from .relations import fstar

        return fstar(self.m, self.gamma)

    @property
    def flowangle(self) -> float:
        """Current flow angle in radians relative to the initialized state."""
        return self.angle

    @property
    def machangle(self) -> float:
        """Mach angle in radians.

        Returns ``-inf`` for subsonic flow, matching the MATLAB behavior.
        """
        if self.m < 1:
            return float("-inf")
        return math.asin(1 / self.m)

    @property
    def shockang(self) -> Optional[float]:
        """Oblique-shock angle in radians, or ``None`` if not applicable."""
        match = re.match(r"oblique shock \(([-+0-9.]+)\s+deg\)", self.proc)
        if match is None:
            return None
        return math.radians(float(match.group(1)))

    @property
    def thetamax(self) -> float:
        """Maximum attached oblique-shock deflection angle in radians."""
        from .relations import thetamax

        if self.m < 1:
            return float("-inf")
        theta, _ = thetamax(self.m, self.gamma, small=self.defaults.small)
        return theta
    
