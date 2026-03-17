"""
Plotting helpers for Gaslab states.

This module contains lightweight Matplotlib translations of the educational
plots from the original MATLAB version. The plotting functions operate on
``GasState`` objects and their histories but do not mutate state.
"""

from itertools import cycle
import io
import re
import types

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from .relations import nspr, pbyp0, pmnu, tbm, thetamax
from .state import GasState

STATE_COLORS = (
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
)


def _attach_notebook_repr(fig: Figure) -> Figure:
    def _repr_png_(self):
        buffer = io.BytesIO()
        self.savefig(buffer, format="png", bbox_inches="tight")
        return buffer.getvalue()

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {"image/png": self._repr_png_()}, {}

    fig._repr_png_ = types.MethodType(_repr_png_, fig)
    fig._repr_mimebundle_ = types.MethodType(_repr_mimebundle_, fig)
    return fig


def _machrange_array(defaults) -> np.ndarray:
    machrange = defaults.machrange
    if isinstance(machrange, tuple) and len(machrange) == 2:
        return np.linspace(machrange[0], machrange[1], 500)
    return np.asarray(machrange, dtype=float)


def _rayleigh_curve(m0: float, s0: float, t0: float, gamma: float, machrange: np.ndarray):
    trat = lambda m: (1 + 0.5 * (gamma - 1) * m**2) ** (-1)
    tstar = lambda m: m**2 * (((1 + gamma * m**2) / (1 + gamma)) ** (-2))
    pstar = lambda m: (gamma + 1) / (1 + gamma * m**2)
    sstar = lambda m: np.log(tstar(m) * (pstar(m) ** ((1 - gamma) / gamma)))

    x = sstar(machrange) - sstar(m0) + s0
    y = t0 * trat(m0) * tstar(machrange) / tstar(m0)
    return x, y


def _fanno_curve(m0: float, s0: float, t0: float, gamma: float, machrange: np.ndarray):
    trat = lambda m: (1 + 0.5 * (gamma - 1) * m**2) ** (-1)
    tstar = lambda m: (gamma + 1) / (2 + (gamma - 1) * m**2)
    pstar = lambda m: (m / np.sqrt(tstar(m))) ** (-1)
    sstar = lambda m: np.log(tstar(m) * (pstar(m) ** ((1 - gamma) / gamma)))

    x = sstar(machrange) - sstar(m0) + s0
    y = t0 * trat(m0) * tstar(machrange) / tstar(m0)
    return x, y


def process_figure(state: GasState, property_name: str = "mach", property_label: str = "Mach"):
    """
    Create a single-metric process-history bar chart.

    Parameters
    ----------
    state : GasState
        Final state in a process chain.
    property_name : str, default "mach"
        Name of the numeric ``GasState`` attribute or property to plot.
    property_label : str, default "Mach"
        Display label for the selected property.

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the process-history chart.
    """
    states = list(state.history())
    fontsize = states[0].defaults.fontsize

    fig = Figure(figsize=(6.5, 4.5))
    FigureCanvasAgg(fig)
    _attach_notebook_repr(fig)
    ax = fig.subplots()

    labels = [f"{idx}. {st.proc}" for idx, st in enumerate(states, start=1)]
    ypos = np.arange(len(states))
    colors = [STATE_COLORS[i % len(STATE_COLORS)] for i in range(len(states))]
    values = []
    defined = []
    for st in states:
        try:
            value = float(getattr(st, property_name))
        except Exception:
            value = np.nan
        values.append(value)
        defined.append(np.isfinite(value))

    finite_values = [value for value, ok in zip(values, defined) if ok]
    if finite_values:
        xmin = min(0.0, min(finite_values))
        xmax = max(1.0, max(finite_values))
    else:
        xmin = 0.0
        xmax = 1.0
    span = xmax - xmin
    if span <= 0:
        span = max(1.0, abs(xmax), abs(xmin))
    xpad = 0.18 * span
    text_offset = 0.02 * span
    undefined_x = xmin + 0.04 * span
    for y, value, color, ok in zip(ypos, values, colors, defined):
        if ok:
            ax.barh(y, value, color=color, height=0.65)

    ax.set_title(property_label, fontsize=fontsize)
    ax.set_xlabel(property_label)
    ax.set_yticks([])
    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.35)
    ax.set_xlim(xmin - 0.02 * span, xmax + xpad)

    for y, value, label, ok in zip(ypos, values, labels, defined):
        if ok:
            label_x = value + text_offset if value >= 0 else value - text_offset
            ha = "left" if value >= 0 else "right"
            text = label
        else:
            label_x = undefined_x
            ha = "left"
            text = f"{label} (undefined)"
        ax.text(
            label_x,
            y,
            text,
            ha=ha,
            va="center",
            fontsize=max(7, fontsize - 3),
        )

    fig.tight_layout()
    return fig


def mollier_figure(state: GasState):
    """
    Create a Mollier (T-s) diagram for a state and its history.

    Parameters
    ----------
    state : GasState
        Final state in a process chain.

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the Mollier diagram.
    """
    states = list(state.history())
    defaults = states[0].defaults
    gamma = states[0].gamma
    machrange = _machrange_array(defaults)
    linewidth = defaults.linewidth
    fontsize = defaults.fontsize
    colors = cycle(STATE_COLORS)

    ent = np.array([st.entropy for st in states], dtype=float)
    temp = np.array([st.temp for st in states], dtype=float)
    stagtemp = np.array([st.stagtemp for st in states], dtype=float)

    fig = Figure(figsize=(5.5, 4.5))
    FigureCanvasAgg(fig)
    _attach_notebook_repr(fig)
    ax = fig.subplots()

    for idx, st in enumerate(states, start=1):
        color = next(colors)
        fx, fy = _fanno_curve(st.mach, st.entropy, st.stagtemp, gamma, machrange)
        rx, ry = _rayleigh_curve(st.mach, st.entropy, st.stagtemp, gamma, machrange)
        ax.plot(fx, fy, color=color, linewidth=linewidth)
        ax.plot(rx, ry, color=color, linewidth=linewidth, linestyle="--")
        ax.plot(
            st.entropy,
            st.temp,
            marker="o",
            markersize=12,
            markerfacecolor=color,
            markeredgecolor=color,
            linestyle="None",
        )

    xmax = max(0.5, 1.25 * float(np.max(ent)))
    xmin = -xmax
    ymax = 1.1 * float(np.max(stagtemp))
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(0.0, ymax)
    ax.grid(True)
    ax.set_xlabel("(s - s1) / cp")
    ax.set_ylabel("T (K)" if states[0].dimmode else "T / T0i")
    ax.tick_params(labelsize=fontsize)
    fig.tight_layout()
    return fig


def pressure_deflection_figure(state: GasState, angle_units: str = "Degrees"):
    """
    Create a pressure-deflection diagram for a state and its history.

    Parameters
    ----------
    state : GasState
        Final state in a process chain.

    angle_units : {"Degrees", "Radians"}, default "Degrees"
        Units used for the horizontal axis.

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the pressure-deflection diagram.
    """
    states = list(state.history())
    defaults = states[0].defaults
    gamma = states[0].gamma
    linewidth = defaults.linewidth
    fontsize = defaults.fontsize
    colors = cycle(STATE_COLORS)

    fig = Figure(figsize=(5.5, 4.5))
    FigureCanvasAgg(fig)
    _attach_notebook_repr(fig)
    ax = fig.subplots()
    plotted = False
    maxp = 1.0
    p1 = states[0].pres
    use_degrees = angle_units == "Degrees"
    angle_scale = np.degrees if use_degrees else (lambda x: x)
    x_label = "Angle (deg rel to init state)" if use_degrees else "Angle (rad rel to init state)"

    for idx, st in enumerate(states, start=1):
        color = next(colors)
        if st.mach <= 1:
            continue

        localp = st.pres / p1
        beta = np.linspace(np.arcsin(1 / st.mach), np.pi / 2, 200)
        theta = tbm(st.mach, beta, gamma)

        pshock = localp * nspr(st.mach * np.sin(beta), gamma)
        maxp = max(maxp, float(np.max(pshock)))

        mexp = np.linspace(st.mach, 10 * st.mach, 300)
        thexp = pmnu(mexp, gamma) - pmnu(st.mach, gamma)
        pexp = localp * pbyp0(mexp, gamma) / pbyp0(st.mach, gamma)

        d = st.flowangle
        ax.plot(angle_scale(d + theta), pshock, color=color, linewidth=linewidth)
        ax.plot(angle_scale(d - theta), pshock, color=color, linewidth=linewidth, linestyle="--")
        ax.plot(angle_scale(d - thexp), pexp, color=color, linewidth=linewidth)
        ax.plot(angle_scale(d + thexp), pexp, color=color, linewidth=linewidth, linestyle="--")
        d_plot = float(angle_scale(d))
        ax.plot([d_plot, d_plot], [0, 1.1 * maxp], color=color, linestyle="-.", linewidth=1.0)
        ax.plot(
            d_plot,
            localp,
            marker="o",
            markersize=12,
            markerfacecolor=color,
            markeredgecolor=color,
            linestyle="None",
        )
        plotted = True

    if plotted:
        if use_degrees:
            ax.set_xlim(-50, 50)
        else:
            ax.set_xlim(-np.deg2rad(50), np.deg2rad(50))
        ax.set_ylim(0, 1.1 * maxp)
        ax.set_xlabel(x_label)
        ax.set_ylabel("P / P1")
        ax.tick_params(labelsize=fontsize)
        ax.grid(True)
    else:
        ax.text(0.5, 0.5, "No supersonic states to plot", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()

    fig.tight_layout()
    return fig


def theta_beta_m_figure(state: GasState):
    """
    Create a theta-beta-M diagram with markers for oblique-shock states.

    Parameters
    ----------
    state : GasState
        Final state in a process chain.

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the theta-beta-M diagram.
    """
    states = list(state.history())
    gamma = states[0].gamma
    fontsize = states[0].defaults.fontsize

    mach_vals = np.arange(1.001, 4.001, 0.01)
    beta_vals_deg = np.arange(0.1, 91.0, 1.0)
    mach_grid, beta_grid_deg = np.meshgrid(mach_vals, beta_vals_deg)
    beta_grid = np.radians(beta_grid_deg)

    theta_deg = np.degrees(tbm(mach_grid, beta_grid, gamma))
    theta_deg = np.where(theta_deg < 0, 0, theta_deg)

    fig = Figure(figsize=(5.5, 4.5))
    FigureCanvasAgg(fig)
    _attach_notebook_repr(fig)
    ax = fig.subplots()
    contours = ax.contour(mach_grid, beta_grid_deg, theta_deg, levels=np.arange(5, 40, 5), colors="k", linewidths=2)
    ax.clabel(contours, inline=True, fontsize=max(8, fontsize - 2))

    mr2 = np.arange(1.0, 4.001, 0.01)
    mach_wave_deg = np.degrees(np.arcsin(1.0 / mr2))
    ax.fill_between(mr2, 0, mach_wave_deg, color="#e5e7eb")
    ax.plot(mr2, mach_wave_deg, color="#D55E00", linewidth=2)
    ax.plot(mr2, 90 * np.ones_like(mr2), color="#D55E00", linewidth=2)
    ax.set_xlim(1, 4)
    ax.set_ylim(0, 91)

    mr1 = np.arange(1.01, 4.01, 0.1)
    beta_max_deg = []
    for m in mr1:
        _, beta_star = thetamax(m, gamma, small=states[0].defaults.small)
        beta_max_deg.append(np.degrees(beta_star))
    ax.plot(mr1, beta_max_deg, "k--", linewidth=2)

    for index, st in enumerate(states, start=1):
        if not st.proc.startswith("oblique shock"):
            continue
        match = re.search(r"\(([-+0-9.]+)\s+deg\)", st.proc)
        if not match:
            continue
        beta_deg = float(match.group(1))
        upstream = st.hist
        if upstream is None:
            continue
        color = STATE_COLORS[(index - 1) % len(STATE_COLORS)]
        ax.plot(
            upstream.mach,
            beta_deg,
            marker="o",
            markersize=10,
            markerfacecolor=color,
            markeredgecolor=color,
            linestyle="None",
        )

    ax.set_xlabel("M")
    ax.set_ylabel(r"$\beta$ (deg)")
    ax.text(1.5, 20, "no solution")
    ax.text(3.0, 15, r"$\theta = 0^\circ$", color="#D55E00")
    ax.tick_params(labelsize=fontsize)
    fig.tight_layout()
    return fig
