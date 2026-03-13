"""
Gas-dynamic relations and inverse solves used by :mod:`gaslab`.

This module contains the scalar perfect-gas formulas that underpin the
process methods on :class:`gaslab.state.GasState`. Forward relations are kept
as plain functions, while inverse relations use :func:`scipy.optimize.root_scalar`
to stay consistent with the architecture of the Python port.
"""

import math

import numpy as np
from scipy.optimize import root_scalar


def pbyp0(M, gamma):
    """
    Static-to-stagnation pressure ratio.

    p/p0 = (1 + (γ−1)/2 M^2)^(-γ/(γ−1))

    Parameters
    ----------
    M : float or ndarray
        Mach number.
    gamma : float
        Ratio of specific heats.

    Returns
    -------
    float or ndarray
        Pressure ratio ``p / p0``.
    """
    return (1 + 0.5*(gamma-1)*M**2)**(-gamma/(gamma-1))


def tbyt0(M, gamma):
    """
    Static-to-stagnation temperature ratio.

    T/T0 = (1 + (γ−1)/2 M^2)^(-1)

    Parameters
    ----------
    M : float or ndarray
        Mach number.
    gamma : float
        Ratio of specific heats.

    Returns
    -------
    float or ndarray
        Temperature ratio ``T / T0``.
    """
    return (1 + 0.5*(gamma-1)*M**2)**(-1)


def normalshock_M2(M1, gamma):
    """
    Downstream Mach number after a normal shock.

    Parameters
    ----------
    M1 : float
        Upstream Mach number.
    gamma : float
        Ratio of specific heats.

    Returns
    -------
    float
        Downstream Mach number.
    """
    num = 1 + 0.5*(gamma-1)*M1**2
    den = gamma*M1**2 - 0.5*(gamma-1)
    return (num/den)**0.5


def nspr(M1, gamma):
    """
    Static pressure ratio across a normal shock, p2/p1.

    Parameters
    ----------
    M1 : float
        Upstream Mach number.
    gamma : float
        Ratio of specific heats.

    Returns
    -------
    float
        Pressure ratio ``p2 / p1``.
    """
    return 1 + 2*gamma/(gamma+1)*(M1**2 - 1)


def arstar(M, gamma):
    """
    Area ratio A/A* for isentropic flow.

    Parameters
    ----------
    M : float or ndarray
        Mach number.
    gamma : float
        Ratio of specific heats.

    Returns
    -------
    float or ndarray
        Critical area ratio ``A / A*``.
    """

    term1 = 1/M
    term2 = (2/(gamma+1)*(1 + (gamma-1)/2*M**2))**((gamma+1)/(2*(gamma-1)))

    return term1 * term2


def t0star(M, gamma):
    """
    Rayleigh critical stagnation-temperature ratio T0/T0*.

    Returns
    -------
    float or ndarray
        Stagnation-temperature ratio relative to the Rayleigh critical state.
    """
    fac = 1 + 0.5 * (gamma - 1) * M**2
    return 2 * (gamma + 1) * fac * M**2 / (1 + gamma * M**2) ** 2


def fstar(M, gamma):
    """
    Fanno critical friction parameter 4fL*/D.

    Returns
    -------
    float or ndarray
        Remaining friction parameter to reach the sonic Fanno state.
    """
    fac = 1 + 0.5 * (gamma - 1) * M**2
    return (1 - M**2) / (gamma * M**2) + ((gamma + 1) / (2 * gamma)) * np.log(
        ((gamma + 1) / 2) * M**2 / fac
    )


def tbm(M, beta, gamma):
    """
    Theta-beta-M relation for oblique shocks.

    Returns
    -------
    float or ndarray
        Flow deflection angle ``theta`` in radians.
    """
    numerator = 2 * 1 / np.tan(beta) * (M**2 * np.sin(beta) ** 2 - 1)
    denominator = M**2 * (gamma + np.cos(2 * beta)) + 2
    return np.arctan(numerator / denominator)


def pmnu(M, gamma):
    """
    Prandtl-Meyer function.

    Parameters
    ----------
    M : float or ndarray
        Supersonic Mach number.
    gamma : float
        Ratio of specific heats.

    Returns
    -------
    float or ndarray
        Prandtl-Meyer angle in radians.
    """
    term = np.sqrt((gamma - 1) * (M**2 - 1) / (gamma + 1))
    return np.sqrt((gamma + 1) / (gamma - 1)) * np.arctan(term) - np.arctan(
        np.sqrt(M**2 - 1)
    )

def mach_from_arstar(a_astar, gamma, subsonic=True, small=1e-6):
    """
    Solve A/A* = arstar(M, gamma) for M.

    Parameters
    ----------
    a_astar : float
        Target area ratio A/A*.
    gamma : float
        Ratio of specific heats.
    subsonic : bool, default True
        If True, return the subsonic branch; otherwise return the supersonic branch.
    small : float, default 1e-6
        Small positive number used to avoid singular endpoints.

    Returns
    -------
    float
        Mach number on the requested branch.

    Raises
    ------
    ValueError
        If ``a_astar < 1``.
    RuntimeError
        If the root solve fails to converge.
    """
    if a_astar < 1:
        raise ValueError("A/A* must be >= 1")

    def f(M):
        return arstar(M, gamma) - a_astar

    if subsonic:
        bracket = [small, 1 - small]
    else:
        bracket = [1 + small, 1 / small]

    sol = root_scalar(f, bracket=bracket, method="brentq")

    if not sol.converged:
        raise RuntimeError("mach_from_arstar did not converge")

    return sol.root


def mach_from_fstar(target, gamma, m1, small=1e-6):
    """
    Solve fstar(M, gamma) = target on the branch containing m1 and M=1.

    Parameters
    ----------
    target : float
        Target value of :func:`fstar`.
    gamma : float
        Ratio of specific heats.
    m1 : float
        Initial Mach number used to determine the physical branch.
    small : float, default 1e-6
        Small positive number to avoid a singular bracket endpoint at Mach 1.

    Returns
    -------
    float
        Downstream Mach number on the same Fanno branch.
    """
    def f(M):
        return target - fstar(M, gamma)

    if m1 <= 1:
        bracket = [max(m1, small), 1 - small]
    else:
        bracket = [1 + small, m1]

    sol = root_scalar(f, bracket=bracket, method="brentq")
    if not sol.converged:
        raise RuntimeError("mach_from_fstar did not converge")
    return sol.root


def mach_from_t0star(target, gamma, m1, small=1e-6):
    """
    Solve ``t0star(M, gamma) = target`` using the MATLAB Rayleigh branch logic.

    Parameters
    ----------
    target : float
        Target value of :func:`t0star`.
    gamma : float
        Ratio of specific heats.
    m1 : float
        Initial Mach number used to determine the physical branch.
    small : float, default 1e-6
        Small positive number to avoid a singular bracket endpoint at Mach 1.

    Returns
    -------
    float
        Downstream Mach number on the Rayleigh branch selected by the
        requested stagnation-temperature change.
    """
    current = t0star(m1, gamma)

    if math.isclose(target, current, rel_tol=1e-12, abs_tol=1e-12):
        return m1

    def f(M):
        return target - t0star(M, gamma)

    if target <= current:
        if m1 <= 1:
            bracket = [small, m1]
        else:
            bracket = [m1, 1 / small]
    else:
        if m1 <= 1:
            bracket = [m1, 1]
        else:
            bracket = [1, m1]

    sol = root_scalar(f, bracket=bracket, method="brentq")
    if not sol.converged:
        raise RuntimeError("mach_from_t0star did not converge")
    return sol.root


def prandtlmeyer(M, theta, gamma, small=1e-6):
    """
    Solve the Prandtl-Meyer relation for a positive expansion angle.

    Parameters
    ----------
    M : float
        Upstream supersonic Mach number.
    theta : float
        Positive expansion angle in radians.
    gamma : float
        Ratio of specific heats.
    small : float, default 1e-6
        Small positive number used to define a large supersonic bracket.

    Returns
    -------
    float
        Downstream Mach number after the expansion.

    Raises
    ------
    ValueError
        If the input is not physically admissible.
    RuntimeError
        If the nonlinear solve does not converge.
    """
    if theta < 0:
        raise ValueError("prandtlmeyer: theta must be positive")
    if M <= 1:
        raise ValueError("prandtlmeyer: Mach number must be supersonic")
    if theta == 0:
        return M

    nu_max = 0.5 * math.pi * (math.sqrt((gamma + 1) / (gamma - 1)) - 1)
    nu_2 = theta + pmnu(M, gamma)
    if nu_2 >= nu_max:
        raise ValueError(
            "specified deflection exceeds maximum possible expansion (M->infty)"
        )

    def f(m2):
        return nu_2 - pmnu(m2, gamma)

    sol = root_scalar(f, bracket=[M, 1 / small], method="brentq")
    if not sol.converged:
        raise RuntimeError("prandtlmeyer did not converge")
    return sol.root


def _tbm_residual(M, beta, gamma):
    tan_theta = math.tan(tbm(M, beta, gamma))
    numerator = 2 / math.tan(beta) * (M**2 * math.sin(beta) ** 2 - 1)
    denominator = M**2 * (gamma + math.cos(2 * beta)) + 2
    return numerator / denominator - tan_theta


def thetamax(M, gamma, small=1e-6):
    """
    Maximum attached oblique-shock deflection angle and corresponding shock angle.

    Parameters
    ----------
    M : float
        Upstream supersonic Mach number.
    gamma : float
        Ratio of specific heats.
    small : float, default 1e-6
        Small positive number used to stay away from singular endpoints.

    Returns
    -------
    tuple[float, float]
        Pair ``(theta_max, beta_at_theta_max)`` in radians.
    """
    if M <= 1:
        raise ValueError("thetamax: Mach number must be supersonic")

    beta_min = math.asin(1 / M) + small
    beta_max = 0.5 * math.pi - small

    def dtheta_dbeta(beta):
        h = max(small, 1e-6)
        return (
            tbm(M, beta + h, gamma) - tbm(M, beta - h, gamma)
        ) / (2 * h)

    sol = root_scalar(dtheta_dbeta, bracket=[beta_min, beta_max], method="brentq")
    if not sol.converged:
        raise RuntimeError("thetamax did not converge")

    beta_star = sol.root
    return tbm(M, beta_star, gamma), beta_star


def oblique(M, theta, gamma, strong=False, small=1e-6):
    """
    Solve the theta-beta-M relation for an oblique shock.

    Parameters
    ----------
    M : float
        Upstream supersonic Mach number.
    theta : float
        Positive flow deflection angle in radians.
    gamma : float
        Ratio of specific heats.
    strong : bool, default False
        If ``True``, solve for the strong-shock branch. Otherwise use the weak
        branch.
    small : float, default 1e-6
        Small positive number used to avoid singular endpoints.

    Returns
    -------
    tuple[float | None, float | None, float | None]
        Tuple ``(beta, mn1, m2)`` where ``beta`` is the shock angle, ``mn1``
        is the upstream normal Mach number, and ``m2`` is the downstream Mach
        number. If no attached-shock solution exists, ``(None, None, None)``
        is returned.
    """
    if theta < 0:
        raise ValueError("oblique: theta must be positive")
    if M <= 1:
        raise ValueError("oblique: Mach number must be supersonic")

    theta_max, beta_star = thetamax(M, gamma, small=small)
    if theta > theta_max:
        return None, None, None

    beta_min = math.asin(1 / M) + small
    beta_max = 0.5 * math.pi - small

    def f(beta):
        return math.tan(theta) - 2 / math.tan(beta) * (
            M**2 * math.sin(beta) ** 2 - 1
        ) / (M**2 * (gamma + math.cos(2 * beta)) + 2)

    if strong:
        bracket = [beta_star + small, beta_max]
    else:
        bracket = [beta_min, beta_star - small]

    sol = root_scalar(f, bracket=bracket, method="brentq")
    if not sol.converged:
        raise RuntimeError("oblique did not converge")

    beta = sol.root
    mn1 = M * math.sin(beta)
    mn2 = normalshock_M2(mn1, gamma)
    m2 = mn2 / math.sin(beta - theta)
    return beta, mn1, m2
