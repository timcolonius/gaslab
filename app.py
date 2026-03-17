import panel as pn
import math
from pathlib import Path
from html import escape
from urllib.parse import quote

from gaslab import GasState
from gaslab.plotting import (
    STATE_COLORS,
    mollier_figure,
    pressure_deflection_figure,
    process_figure,
    theta_beta_m_figure,
)
from gaslab.relations import pbyp0, tbyt0
from gaslab.ui_tooltips import TOOLTIPS

pn.extension(
    sizing_mode="stretch_width",
    raw_css=[
        """
        .gaslab-input-valid input,
        .gaslab-input-valid .bk-input,
        .gaslab-input-valid textarea {
          background: white !important;
          border: 1px solid #9CA3AF !important;
          box-shadow: none !important;
          outline: none !important;
        }
        .gaslab-input-valid input:focus,
        .gaslab-input-valid .bk-input:focus,
        .gaslab-input-valid textarea:focus {
          border: 1px solid #6B7280 !important;
          box-shadow: none !important;
          outline: none !important;
        }
        .gaslab-input-error input,
        .gaslab-input-error .bk-input,
        .gaslab-input-error textarea {
          background: #FCE7F3 !important;
          border: 1px solid #EC4899 !important;
          box-shadow: 0 0 0 1px #EC4899 !important;
          outline: none !important;
        }
        .gaslab-input-error input:focus,
        .gaslab-input-error .bk-input:focus,
        .gaslab-input-error textarea:focus {
          background: #FCE7F3 !important;
          border: 1px solid #EC4899 !important;
          box-shadow: 0 0 0 1px #EC4899 !important;
          outline: none !important;
        }
        """,
    ],
)

VALID_INPUT_STYLESHEET = """
.bk-input-group label,
.bk-input-group .bk-input-group-title,
.bk-input-group .bk-input-group-label,
label.bk,
.bk-clearfix label {
  width: 100% !important;
  display: block !important;
  text-align: center !important;
}
input, .bk-input, textarea {
  background: white !important;
  border: 1px solid #9CA3AF !important;
  box-shadow: none !important;
  outline: none !important;
}
input:focus, .bk-input:focus, textarea:focus {
  border: 1px solid #6B7280 !important;
  box-shadow: none !important;
  outline: none !important;
}
"""

ERROR_INPUT_STYLESHEET = """
.bk-input-group label,
.bk-input-group .bk-input-group-title,
.bk-input-group .bk-input-group-label,
label.bk,
.bk-clearfix label {
  width: 100% !important;
  display: block !important;
  text-align: center !important;
}
input, .bk-input, textarea {
  background: #F8D7DA !important;
  border: 1px solid #DC3545 !important;
  box-shadow: 0 0 0 1px #DC3545 !important;
  outline: none !important;
}
input:focus, .bk-input:focus, textarea:focus {
  background: #F8D7DA !important;
  border: 1px solid #DC3545 !important;
  box-shadow: 0 0 0 1px #DC3545 !important;
  outline: none !important;
}
"""

if "__file__" in globals():
    BANNER_PATH = Path(__file__).resolve().parent / "assets" / "gaslab_banner.png"
else:
    BANNER_PATH = Path("assets") / "gaslab_banner.png"

CARD_STYLE = {
    "background": "#F3F4F6",
    "box-shadow": "none",
}
CARD_HEADER_COLOR = "#E5E7EB"

SUBPANEL_STYLE = {
    "background": "#E5E7EB",
    "padding": "5px 8px",
    "border-radius": "6px",
    "border": "1px solid #F3F4F6",
}

OUTLINE_BUTTON_STYLE = {
    "background": "white",
    "border": "1px solid #999",
    "box-shadow": "none",
}

PROCESS_BUTTON_STYLE = {
    "background": "white",
    "border": "1px solid #9CA3AF",
    "box-shadow": "none",
    "border-radius": "6px",
}

PROCESS_ICONS = {
    "Reset": """<svg width="120" height="100" viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg"><g transform="rotate(-90 60 50)" stroke="#4b5563" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M60 20 A30 30 0 1 1 30 50"/><polyline points="20,60 30,50 40,60"/></g></svg>""",
    "Area Change": """<svg width="180" height="90" viewBox="0 0 180 90" xmlns="http://www.w3.org/2000/svg"><g stroke="#4b5563" stroke-width="6" stroke-linecap="round" fill="none"><path d="M20 20 L82 35 L160 20"/><path d="M20 70 L82 55 L160 70"/><line x1="45" y1="45" x2="135" y2="45"/><polyline points="120,35 135,45 120,55"/></g></svg>""",
    "Fanno": """<svg width="220" height="90" viewBox="0 0 220 90" xmlns="http://www.w3.org/2000/svg"><g stroke="#4b5563" stroke-width="6" stroke-linecap="round" fill="none"><line x1="15" y1="22" x2="205" y2="22"/><line x1="15" y1="68" x2="205" y2="68"/><line x1="15" y1="45" x2="55" y2="45"/><path d="M65 45 C75 35, 85 55, 95 45 C105 35, 115 55, 125 45 C135 35, 145 55, 155 45 C165 35, 175 55, 185 45"/><line x1="185" y1="45" x2="205" y2="45"/><polyline points="190,35 205,45 190,55"/></g><text x="108" y="18" text-anchor="middle" font-family="Arial, sans-serif" font-size="42" font-weight="600" fill="#374151">+ μ</text></svg>""",
    "Rayleigh": """<svg width="220" height="90" viewBox="0 0 220 90" xmlns="http://www.w3.org/2000/svg"><g stroke="#4b5563" stroke-width="6" stroke-linecap="round" fill="none"><line x1="15" y1="22" x2="205" y2="22"/><line x1="15" y1="68" x2="205" y2="68"/><line x1="15" y1="45" x2="55" y2="45"/><path d="M65 45 C75 35, 85 55, 95 45 C105 35, 115 55, 125 45 C135 35, 145 55, 155 45 C165 35, 175 55, 185 45"/><line x1="185" y1="45" x2="205" y2="45"/><polyline points="190,35 205,45 190,55"/></g><text x="108" y="18" text-anchor="middle" font-family="Arial, sans-serif" font-size="42" font-weight="600" fill="#374151">+ q</text></svg>""",
    "Normal Shock": """<svg width="220" height="90" viewBox="0 0 220 90" xmlns="http://www.w3.org/2000/svg"><g stroke="#4b5563" stroke-width="6" stroke-linecap="round" fill="none"><line x1="15" y1="22" x2="205" y2="22"/><line x1="15" y1="68" x2="205" y2="68"/><line x1="20" y1="45" x2="110" y2="45"/><polyline points="95,35 110,45 95,55"/><line x1="125" y1="28" x2="125" y2="62" stroke="#d94841"/><line x1="140" y1="45" x2="185" y2="45"/><polyline points="170,35 185,45 170,55"/></g></svg>""",
    "Deflect": """<svg width="240" height="100" viewBox="0 0 240 100" xmlns="http://www.w3.org/2000/svg"><g stroke="#4b5563" stroke-width="6" stroke-linecap="round" fill="none"><line x1="15" y1="70" x2="95" y2="70"/><line x1="95" y1="70" x2="190" y2="54"/><line x1="25" y1="40" x2="95" y2="40"/><polyline points="80,30 95,40 80,50"/><line x1="95" y1="70" x2="155" y2="10" stroke="#4f46e5"/><line x1="145" y1="44" x2="190" y2="36"/><polyline points="177,30 190,36 179,46"/></g></svg>""",
}

PROCESS_PLOT_OPTIONS = {
    "Mach": "mach",
    "Gamma": "gamma",
    "Flow Angle": "flowangle",
    "Pressure": "pres",
    "Stagnation Pressure": "stagpres",
    "Temperature": "temp",
    "Stagnation Temperature": "stagtemp",
    "Density": "density",
    "Speed": "speed",
    "Sound Speed": "soundsp",
    "Area Ratio to Critical": "arcrit",
    "Rayleigh Critical Ratio": "t0rcrit",
    "Fanno Critical Parameter": "fcrit",
    "Mach Angle": "machangle",
    "Maximum Deflection": "thetamax",
}


def process_button_stylesheet(title: str) -> str:
    svg = quote(PROCESS_ICONS[title])
    return f"""
button, .bk-btn {{
  background-color: #ECFDF3 !important;
  background-image: url("data:image/svg+xml;utf8,{svg}") !important;
  background-position: center !important;
  background-repeat: no-repeat !important;
  background-size: 88% 88% !important;
  border: 1px solid #9CA3AF !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important;
  min-width: 82px !important;
  min-height: 36px !important;
  width: 82px !important;
  height: 36px !important;
  padding: 0 !important;
  cursor: pointer !important;
  transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease, background-color 120ms ease !important;
}}
button:hover, .bk-btn:hover {{
  background-color: #DFF7E8 !important;
  border-color: #6B7280 !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12) !important;
  transform: translateY(-1px) !important;
}}
button:active, .bk-btn:active {{
  background-color: #D1F2DD !important;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.12) !important;
  transform: translateY(0) !important;
}}
button:disabled, .bk-btn:disabled,
.bk-btn[disabled], button[disabled] {{
  background-color: #E5E7EB !important;
  background-image: url("data:image/svg+xml;utf8,{svg}") !important;
  background-position: center !important;
  background-repeat: no-repeat !important;
  background-size: 88% 88% !important;
  border: 1px solid #C7CDD6 !important;
  box-shadow: none !important;
  opacity: 0.45 !important;
  filter: grayscale(1) contrast(0.8) !important;
  cursor: not-allowed !important;
  transform: none !important;
}}
"""

EPS = 1e-6


def history_columns(dimensional: bool, angle_units: str):
    angle_suffix = "(deg)" if angle_units == "Degrees" else "(rad)"
    if dimensional:
        return [
            ("State", "state"),
            ("Process", "proc"),
            ("M", "mach"),
            ("γ", "gamma"),
            (f"θ {angle_suffix}", "flowangle"),
            ("T (K)", "temp"),
            ("T₀ (K)", "stagtemp"),
            ("p (atm)", "pres"),
            ("p₀ (atm)", "stagpres"),
            ("ρ (kg/m³)", "density"),
            ("u (m/s)", "speed"),
            ("a (m/s)", "soundsp"),
            ("A/A*", "arcrit"),
            ("T₀/T₀*", "t0rcrit"),
            ("4fL*/D", "fcrit"),
            (f"μ {angle_suffix}", "machangle"),
            (f"θ_max {angle_suffix}", "thetamax"),
        ]

    return [
        ("State", "state"),
        ("Process", "proc"),
        ("M", "mach"),
        ("γ", "gamma"),
        (f"θ {angle_suffix}", "flowangle"),
        ("T/T₀ᵢ", "temp"),
        ("T₀/T₀ᵢ", "stagtemp"),
        ("p/p₀ᵢ", "pres"),
        ("p₀/p₀ᵢ", "stagpres"),
        ("ρ/ρ₀ᵢ", "density"),
        ("u/a₀ᵢ", "speed"),
        ("a/a₀ᵢ", "soundsp"),
        ("A/A*", "arcrit"),
        ("T₀/T₀*", "t0rcrit"),
        ("4fL*/D", "fcrit"),
        (f"μ {angle_suffix}", "machangle"),
        (f"θ_max {angle_suffix}", "thetamax"),
    ]


def _angle_value(value: float, angle_units: str) -> str:
    if angle_units == "Degrees":
        return f"{math.degrees(value):.6g}"
    return f"{value:.6g}"


def display_values(state: GasState, dimensional: bool, angle_units: str):
    if dimensional:
        if not state.dimmode:
            raise ValueError("Dimensional display requires a state initialized in dimensional mode")

        return {
            "mach": f"{state.mach:.6g}",
            "gamma": f"{state.gamma:.6g}",
            "flowangle": _angle_value(state.flowangle, angle_units),
            "temp": f"{state.temp:.6g}",
            "stagtemp": f"{state.stagtemp:.6g}",
            "pres": f"{state.pres:.6g}",
            "stagpres": f"{state.stagpres:.6g}",
            "density": f"{state.density:.6g}",
            "speed": f"{state.speed:.6g}",
            "soundsp": f"{state.soundsp:.6g}",
            "arcrit": f"{state.arcrit:.6g}",
            "t0rcrit": f"{state.t0rcrit:.6g}",
            "fcrit": f"{state.fcrit:.6g}",
            "machangle": _angle_value(state.machangle, angle_units),
            "thetamax": _angle_value(state.thetamax, angle_units),
        }

    return {
        "mach": f"{state.mach:.6g}",
        "gamma": f"{state.gamma:.6g}",
        "flowangle": _angle_value(state.flowangle, angle_units),
        "temp": f"{state.temp / state.t0r:.6g}",
        "stagtemp": f"{state.t0:.6g}",
        "pres": f"{state.pres / state.p0r:.6g}",
        "stagpres": f"{state.p0:.6g}",
        "density": f"{(state.pres / state.p0r) * (state.t0r / state.temp) if state.dimmode else state.density:.6g}",
        "speed": f"{state.speed / (state.gamma * state.gcon * state.t0r) ** 0.5 if state.dimmode else state.speed:.6g}",
        "soundsp": f"{state.soundsp / (state.gamma * state.gcon * state.t0r) ** 0.5 if state.dimmode else state.soundsp:.6g}",
        "arcrit": f"{state.arcrit:.6g}",
        "t0rcrit": f"{state.t0rcrit:.6g}",
        "fcrit": f"{state.fcrit:.6g}",
        "machangle": _angle_value(state.machangle, angle_units),
        "thetamax": _angle_value(state.thetamax, angle_units),
    }


def format_history_table(state: GasState, dimensional: bool, angle_units: str) -> str:
    columns = history_columns(dimensional, angle_units)
    header = "".join(
        f"<th style='padding:6px 8px; border:1px solid #ddd; background:#f5f5f5;'>{escape(label)}</th>"
        for label, _ in columns
    )

    rows = []
    for index, st in enumerate(state.history(), start=1):
        color = STATE_COLORS[(index - 1) % len(STATE_COLORS)]
        values = {
            "state": index,
            "proc": st.proc,
        }
        values.update(display_values(st, dimensional, angle_units))
        cells = []
        for _, key in columns:
            style = "padding:6px 8px; border:1px solid #ddd; white-space:nowrap;"
            if key in {"state", "proc"}:
                style += f" color:{color}; font-weight:600;"
            cells.append(
                f"<td style='{style}'>{escape(str(values[key]))}</td>"
            )
        rows.append(f"<tr>{''.join(cells)}</tr>")

    return (
        "<div style='overflow:auto;'>"
        "<table style='border-collapse:collapse; font-family:monospace; font-size:13px; width:max-content; min-width:100%;'>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )


def _py_value(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return repr(round(value, 12))
    return repr(value)


def format_python_chain(app) -> str:
    args = [_py_value(app.mach_input.value), _py_value(app.gamma_input.value)]
    if app.is_dimensional:
        args.extend(
            [
                f"p={_py_value(app.pres_input.value)}",
                f"T={_py_value(app.temp_input.value)}",
                f"mw={_py_value(app.mw_input.value)}",
            ]
        )

    expr = f"GasState.init({', '.join(args)})"
    for op_name, kwargs in app.operations:
        if kwargs:
            kwargs_text = ", ".join(f"{key}={_py_value(value)}" for key, value in kwargs.items())
            expr += f".{op_name}({kwargs_text})"
        else:
            expr += f".{op_name}()"
    return expr


def process_plot_label(property_key: str, dimensional: bool, angle_units: str) -> str:
    for label, key in history_columns(dimensional, angle_units):
        if key == property_key:
            return label
    return property_key


class GasLabApp:
    def __init__(self):
        self.mode = pn.widgets.RadioButtonGroup(
            name="Mode",
            options=["Nondimensional", "Dimensional"],
            value="Dimensional",
            button_type="default",
        )
        self.angle_units = pn.widgets.RadioButtonGroup(
            name="Angles",
            options=["Radians", "Degrees"],
            value="Degrees",
            button_type="default",
        )

        self.gamma_input = pn.widgets.FloatInput(name="γ", value=1.4, step=0.01, format="0.000")
        self.mw_input = pn.widgets.FloatInput(name="Molecular Weight (g/mol)", value=28.97, step=0.1, format="0.000")

        self.mach_input = pn.widgets.FloatInput(name="M", value=2.0, step=0.1, format="0.000")
        self.pres_input = pn.widgets.FloatInput(name="p reservoir (atm)", value=1.0, step=0.1, format="0.000")
        self.temp_input = pn.widgets.FloatInput(name="T reservoir (K)", value=300.0, step=10.0, format="0.000")

        self.area_ratio_input = pn.widgets.FloatInput(name="A₂/A₁", value=2.0, step=0.1, format="0.000")
        self.throat_input = pn.widgets.Checkbox(name="throat", value=False)
        self.area_choke_input = pn.widgets.Checkbox(name="choke", value=False)
        self.fanno_input = pn.widgets.FloatInput(name="4fL/D", value=0.1, step=0.01, format="0.000")
        self.fanno_choke_input = pn.widgets.Checkbox(name="choke", value=False)
        self.rayleigh_input = pn.widgets.FloatInput(name="T₀₂/T₀₁", value=1.1, step=0.05, format="0.000")
        self.rayleigh_choke_input = pn.widgets.Checkbox(name="choke", value=False)
        self.deflect_input = pn.widgets.FloatInput(name="θ (deg)", value=10.0, step=1.0, format="0.000")
        self.family_input = pn.widgets.RadioButtonGroup(
            name="Family",
            options=["C+", "C-"],
            value="C+",
            button_type="default",
        )
        self.strong_input = pn.widgets.RadioButtonGroup(
            name="Wave",
            options=["Weak", "Strong"],
            value="Weak",
            button_type="default",
        )

        self.initialize_button = pn.widgets.Button(name="Reset", styles=OUTLINE_BUTTON_STYLE)
        self.shock_button = pn.widgets.Button(name="Normal Shock", styles=OUTLINE_BUTTON_STYLE)
        self.area_button = pn.widgets.Button(name="Area Change", styles=OUTLINE_BUTTON_STYLE)
        self.fanno_button = pn.widgets.Button(name="Fanno (friction)", styles=OUTLINE_BUTTON_STYLE)
        self.rayleigh_button = pn.widgets.Button(name="Rayleigh (heat xfer)", styles=OUTLINE_BUTTON_STYLE)
        self.deflect_button = pn.widgets.Button(name="Deflect", styles=OUTLINE_BUTTON_STYLE)

        self.message = pn.pane.Alert("", alert_type="light", visible=False)
        self.history_panel = pn.pane.HTML("", sizing_mode="stretch_width")
        self.mollier_panel = pn.pane.Matplotlib(
            None,
            tight=True,
            sizing_mode="stretch_width",
            height=420,
        )
        self.process_plot_panel = pn.pane.Matplotlib(
            None,
            tight=True,
            sizing_mode="stretch_width",
            height=420,
        )
        self.process_plot_select = pn.widgets.Select(
            name="Quantity",
            options=list(PROCESS_PLOT_OPTIONS.keys()),
            value="Mach",
            width=240,
        )
        self.presdef_panel = pn.pane.Matplotlib(
            None,
            tight=True,
            sizing_mode="stretch_width",
            height=420,
        )
        self.tbm_panel = pn.pane.Matplotlib(
            None,
            tight=True,
            sizing_mode="stretch_width",
            height=420,
        )
        self.copy_python_button = pn.widgets.Button(name="Copy Python", styles=OUTLINE_BUTTON_STYLE)
        self.python_text = pn.widgets.TextAreaInput(
            value="",
            disabled=True,
            sizing_mode="stretch_width",
            height=120,
        )
        self.banner = pn.pane.PNG(
            str(BANNER_PATH),
            sizing_mode="stretch_width",
            height=140,
        )

        self.state = None
        self.operations = []
        self._suspend_watch = False
        self.field_errors = {}
        self.validated_inputs = [
            self.gamma_input,
            self.mach_input,
            self.area_ratio_input,
            self.fanno_input,
            self.rayleigh_input,
        ]
        self.default_values = {
            self.gamma_input.name: self.gamma_input.value,
            self.mw_input.name: self.mw_input.value,
            self.mach_input.name: self.mach_input.value,
            self.pres_input.name: self.pres_input.value,
            self.temp_input.name: self.temp_input.value,
            self.area_ratio_input.name: self.area_ratio_input.value,
            self.fanno_input.name: self.fanno_input.value,
            self.rayleigh_input.name: self.rayleigh_input.value,
            self.deflect_input.name: self.deflect_input.value,
        }
        self.float_inputs = [
            self.gamma_input,
            self.mw_input,
            self.mach_input,
            self.pres_input,
            self.temp_input,
            self.area_ratio_input,
            self.fanno_input,
            self.rayleigh_input,
            self.deflect_input,
        ]
        self.process_buttons = [
            self.shock_button,
            self.area_button,
            self.fanno_button,
            self.rayleigh_button,
            self.deflect_button,
        ]
        self.last_valid_values = {widget.name: widget.value for widget in self.validated_inputs}
        for widget in self.float_inputs:
            widget.stylesheets = [VALID_INPUT_STYLESHEET]
        for widget in self.validated_inputs:
            widget.css_classes = ["gaslab-input-valid"]
            widget.stylesheets = [VALID_INPUT_STYLESHEET]
        self.python_text.stylesheets = [VALID_INPUT_STYLESHEET]
        self.copy_python_button.js_on_click(
            args={"source": self.python_text},
            code="navigator.clipboard.writeText(source.value)",
        )
        self._apply_tooltips()

        self.mode.param.watch(self._update_mode_visibility, "value")
        self.angle_units.param.watch(self._update_angle_units, "value")
        self.gamma_input.param.watch(self._on_gamma_change, "value")
        self.mw_input.param.watch(self._recompute_from_controls, "value")
        self.mach_input.param.watch(self._on_mach_change, "value")
        self.pres_input.param.watch(self._recompute_from_controls, "value")
        self.temp_input.param.watch(self._recompute_from_controls, "value")
        self.area_ratio_input.param.watch(self._on_area_ratio_change, "value")
        self.throat_input.param.watch(self._update_latest_areachg, "value")
        self.area_choke_input.param.watch(self._on_area_choke_change, "value")
        self.fanno_input.param.watch(self._on_fanno_change, "value")
        self.fanno_choke_input.param.watch(self._on_fanno_choke_change, "value")
        self.rayleigh_input.param.watch(self._on_rayleigh_change, "value")
        self.rayleigh_choke_input.param.watch(self._on_rayleigh_choke_change, "value")
        self.deflect_input.param.watch(self._update_latest_deflect, "value")
        self.family_input.param.watch(self._update_latest_deflect, "value")
        self.strong_input.param.watch(self._update_latest_deflect, "value")
        self.process_plot_select.param.watch(self._refresh_process_plot, "value")
        self.initialize_button.on_click(self._initialize_state)
        self.shock_button.on_click(self._apply_normal_shock)
        self.area_button.on_click(self._apply_area_change)
        self.fanno_button.on_click(self._apply_fanno)
        self.rayleigh_button.on_click(self._apply_rayleigh)
        self.deflect_button.on_click(self._apply_deflect)

        self._update_mode_visibility()
        self._initialize_state()

    def _apply_tooltips(self) -> None:
        tooltip_widgets = {
            "mode": self.mode,
            "angle_units": self.angle_units,
            "gamma_input": self.gamma_input,
            "mw_input": self.mw_input,
            "mach_input": self.mach_input,
            "pres_input": self.pres_input,
            "temp_input": self.temp_input,
            "area_ratio_input": self.area_ratio_input,
            "fanno_input": self.fanno_input,
            "rayleigh_input": self.rayleigh_input,
            "deflect_input": self.deflect_input,
            "family_input": self.family_input,
            "strong_input": self.strong_input,
            "process_plot_select": self.process_plot_select,
            "initialize_button": self.initialize_button,
            "shock_button": self.shock_button,
            "area_button": self.area_button,
            "fanno_button": self.fanno_button,
            "rayleigh_button": self.rayleigh_button,
            "deflect_button": self.deflect_button,
            "copy_python_button": self.copy_python_button,
        }
        for key, widget in tooltip_widgets.items():
            widget.description = TOOLTIPS[key]

    def _checkbox_with_tooltip(self, widget, tooltip_key: str):
        return pn.Row(
            widget,
            pn.widgets.TooltipIcon(
                value=TOOLTIPS[tooltip_key],
                width=16,
                height=16,
                margin=(0, 0, 0, 2),
            ),
            width=(widget.width or 28) + 20,
            height=24,
            sizing_mode="fixed",
            styles={"align-items": "center", "justify-content": "center", "gap": "2px"},
        )

    @property
    def is_dimensional(self) -> bool:
        return self.mode.value == "Dimensional"

    def _set_message(self, text: str = "", alert_type: str = "light") -> None:
        self.message.object = text
        self.message.alert_type = alert_type
        self.message.visible = bool(text)

    def _clear_message(self) -> None:
        self._set_message()

    def _set_widget_error(self, widget, message: str) -> None:
        self.field_errors[widget.name] = message
        widget.css_classes = ["gaslab-input-error"]
        widget.stylesheets = [ERROR_INPUT_STYLESHEET]
        self._set_message(message, alert_type="danger")
        self._update_process_availability()

    def _clear_widget_error(self, widget) -> None:
        self.field_errors.pop(widget.name, None)
        widget.css_classes = ["gaslab-input-valid"]
        widget.stylesheets = [VALID_INPUT_STYLESHEET]
        if not self.field_errors and self.message.alert_type == "danger":
            self._clear_message()
        self._update_process_availability()

    def _has_field_errors(self) -> bool:
        return bool(self.field_errors)

    def _restore_invalid_defaults(self) -> None:
        self._suspend_watch = True
        for widget in self.validated_inputs:
            if widget.name in self.field_errors:
                widget.value = self.default_values[widget.name]
                widget.css_classes = ["gaslab-input-valid"]
                widget.stylesheets = [VALID_INPUT_STYLESHEET]
                self.last_valid_values[widget.name] = widget.value
        self._suspend_watch = False
        self.field_errors = {}
        self._clear_message()

    def _update_process_availability(self) -> None:
        if self._has_field_errors():
            for button in self.process_buttons:
                button.disabled = True
            self.initialize_button.disabled = False
            return

        for button in self.process_buttons:
            button.disabled = False
        self.initialize_button.disabled = False

        if self.state is not None and self.state.mach <= 1:
            self.shock_button.disabled = True
            self.deflect_button.disabled = True

    def _validate_range(self, event, *, lower=None, upper=None, lower_open=False, upper_open=False, message: str):
        if self._suspend_watch:
            return False
        value = event.new
        too_low = False
        too_high = False
        if lower is not None:
            too_low = value <= lower if lower_open else value < lower
        if upper is not None:
            too_high = value >= upper if upper_open else value > upper
        if too_low or too_high:
            self._set_widget_error(event.obj, message)
            return False
        self.last_valid_values[event.obj.name] = value
        self._clear_widget_error(event.obj)
        return True

    def _rebuild_state(self) -> None:
        state = self._build_initial_state()
        for op_name, kwargs in self.operations:
            state = getattr(state, op_name)(**kwargs)
        self.state = state

    def _process_base_state(self, op_name: str):
        if self.state is None:
            return None
        if self.operations and self.operations[-1][0] == op_name and self.state.hist is not None:
            return self.state.hist
        return self.state

    def _current_area_ratio_value(self) -> float:
        if self.area_choke_input.value:
            state = self._process_base_state("areachg")
            if state is not None:
                return 1 / state.arcrit
        return self.area_ratio_input.value

    def _current_fanno_value(self) -> float:
        if self.fanno_choke_input.value:
            state = self._process_base_state("fanno")
            if state is not None:
                return state.fcrit
        return self.fanno_input.value

    def _current_rayleigh_value(self) -> float:
        if self.rayleigh_choke_input.value:
            state = self._process_base_state("rayleigh")
            if state is not None:
                return 1 / state.t0rcrit
        return self.rayleigh_input.value

    def _refresh_choke_inputs(self) -> None:
        self._suspend_watch = True
        if self.area_choke_input.value:
            self.area_ratio_input.value = self._current_area_ratio_value()
            self.area_ratio_input.disabled = True
        else:
            self.area_ratio_input.disabled = False

        if self.fanno_choke_input.value:
            self.fanno_input.value = self._current_fanno_value()
            self.fanno_input.disabled = True
        else:
            self.fanno_input.disabled = False

        if self.rayleigh_choke_input.value:
            self.rayleigh_input.value = self._current_rayleigh_value()
            self.rayleigh_input.disabled = True
        else:
            self.rayleigh_input.disabled = False
        self._suspend_watch = False

    def _recompute_from_controls(self, *_events) -> None:
        if self._suspend_watch:
            return
        if self._has_field_errors():
            return
        if self.state is None:
            return
        try:
            self._rebuild_state()
            self._refresh_history()
        except Exception as exc:
            self._set_message(str(exc), alert_type="danger")

    def _on_gamma_change(self, event) -> None:
        if not self._validate_range(
            event,
            lower=1.0,
            upper=2.0,
            lower_open=True,
            upper_open=True,
            message="γ must be greater than 1 and less than 2.",
        ):
            return
        self._recompute_from_controls()

    def _on_mach_change(self, event) -> None:
        if not self._validate_range(
            event,
            lower=EPS,
            upper=10.0,
            lower_open=False,
            upper_open=False,
            message=f"Mach number must be between {EPS:.0e} and 10.",
        ):
            return
        self._recompute_from_controls()

    def _on_area_ratio_change(self, event) -> None:
        if self.area_choke_input.value:
            return
        if not self._validate_range(
            event,
            lower=EPS,
            upper=1 / EPS,
            lower_open=False,
            upper_open=False,
            message=f"Area ratio must be between {EPS:.0e} and {1/EPS:.0e}.",
        ):
            return
        self._update_latest_areachg()

    def _on_area_choke_change(self, *_events) -> None:
        self._refresh_choke_inputs()
        self._update_latest_areachg()

    def _on_fanno_change(self, event) -> None:
        if self.fanno_choke_input.value:
            return
        if not self._validate_range(
            event,
            lower=EPS,
            lower_open=False,
            message=f"Friction parameter 4fL/D must be at least {EPS:.0e}.",
        ):
            return
        self._update_latest_fanno()

    def _on_fanno_choke_change(self, *_events) -> None:
        self._refresh_choke_inputs()
        self._update_latest_fanno()

    def _on_rayleigh_change(self, event) -> None:
        if self.rayleigh_choke_input.value:
            return
        if not self._validate_range(
            event,
            lower=EPS,
            lower_open=False,
            message=f"Rayleigh ratio T₀₂/T₀₁ must be at least {EPS:.0e}.",
        ):
            return
        self._update_latest_rayleigh()

    def _on_rayleigh_choke_change(self, *_events) -> None:
        self._refresh_choke_inputs()
        self._update_latest_rayleigh()

    def _update_mode_visibility(self, *_events) -> None:
        self.mw_input.visible = self.is_dimensional
        self.pres_input.visible = self.is_dimensional
        self.temp_input.visible = self.is_dimensional
        if self.state is not None:
            self._recompute_from_controls()

    def _update_angle_units(self, *_events) -> None:
        self._suspend_watch = True
        if self.angle_units.value == "Degrees":
            self.deflect_input.name = "θ (deg)"
            self.deflect_input.value = 10.0
            self.deflect_input.step = 1.0
        else:
            self.deflect_input.name = "θ (rad)"
            self.deflect_input.value = 0.1
            self.deflect_input.step = 0.01
        self._suspend_watch = False
        if self.state is not None:
            self._update_latest_deflect()
            self._refresh_history()

    def _build_initial_state(self) -> GasState:
        if self.is_dimensional:
            return GasState.init(
                self.mach_input.value,
                self.gamma_input.value,
                p=self.pres_input.value,
                T=self.temp_input.value,
                mw=self.mw_input.value,
            )
        return GasState.init(self.mach_input.value, self.gamma_input.value)

    def _update_latest_operation(self, op_name: str, kwargs: dict) -> None:
        if self._suspend_watch:
            return
        if self._has_field_errors():
            return
        if not self.operations:
            return
        if self.operations[-1][0] != op_name:
            return
        previous_operation = self.operations[-1]
        self.operations[-1] = (op_name, kwargs)
        try:
            self._rebuild_state()
            self._clear_message()
            self._refresh_history()
        except Exception as exc:
            self.operations[-1] = previous_operation
            self._rebuild_state()
            self._set_message(str(exc), alert_type="danger")

    def _apply_operation(self, op_name: str, kwargs: dict) -> None:
        previous_operations = list(self.operations)
        try:
            self.operations.append((op_name, kwargs))
            self._rebuild_state()
            self._clear_message()
            self._refresh_history()
        except Exception as exc:
            self.operations = previous_operations
            self._rebuild_state()
            self._set_message(str(exc), alert_type="danger")

    def _current_deflect_angle_radians(self) -> float:
        angle = self.deflect_input.value
        if self.angle_units.value == "Degrees":
            angle = math.radians(angle)
        return angle

    def _update_latest_areachg(self, *_events) -> None:
        self._update_latest_operation(
            "areachg",
            {"ar": self._current_area_ratio_value(), "throat": self.throat_input.value},
        )

    def _update_latest_fanno(self, *_events) -> None:
        self._update_latest_operation("fanno", {"fric": self._current_fanno_value()})

    def _update_latest_rayleigh(self, *_events) -> None:
        self._update_latest_operation("rayleigh", {"t0ratio": self._current_rayleigh_value()})

    def _update_latest_deflect(self, *_events) -> None:
        self._update_latest_operation(
            "deflect",
            {
                "ang": self._current_deflect_angle_radians(),
                "fam": 1 if self.family_input.value == "C+" else -1,
                "strong": self.strong_input.value == "Strong",
            },
        )

    def _block_on_invalid_fields(self) -> bool:
        if not self._has_field_errors():
            return False
        self._set_message("Correct the highlighted fields before applying a process.", alert_type="danger")
        return True

    def _initialize_state(self, *_events) -> None:
        try:
            if self._has_field_errors():
                self._restore_invalid_defaults()
            self.operations = []
            self._rebuild_state()
            self._clear_message()
            self._refresh_history()
        except Exception as exc:
            self._set_message(str(exc), alert_type="danger")

    def _apply_normal_shock(self, _event) -> None:
        if self._block_on_invalid_fields():
            return
        if self.state is None:
            self._initialize_state()
            return

        self._apply_operation("normalshock", {})

    def _apply_area_change(self, _event) -> None:
        if self._block_on_invalid_fields():
            return
        if self.state is None:
            self._initialize_state()
            return

        self._apply_operation(
            "areachg",
            {"ar": self._current_area_ratio_value(), "throat": self.throat_input.value},
        )

    def _apply_fanno(self, _event) -> None:
        if self._block_on_invalid_fields():
            return
        if self.state is None:
            self._initialize_state()
            return

        self._apply_operation("fanno", {"fric": self._current_fanno_value()})

    def _apply_rayleigh(self, _event) -> None:
        if self._block_on_invalid_fields():
            return
        if self.state is None:
            self._initialize_state()
            return

        self._apply_operation("rayleigh", {"t0ratio": self._current_rayleigh_value()})

    def _apply_deflect(self, _event) -> None:
        if self._block_on_invalid_fields():
            return
        if self.state is None:
            self._initialize_state()
            return

        self._apply_operation(
            "deflect",
            {
                "ang": self._current_deflect_angle_radians(),
                "fam": 1 if self.family_input.value == "C+" else -1,
                "strong": self.strong_input.value == "Strong",
            },
        )

    def _refresh_history(self) -> None:
        try:
            self.history_panel.object = format_history_table(
                self.state,
                self.is_dimensional,
                self.angle_units.value,
            )
        except ValueError as exc:
            self.history_panel.object = format_history_table(
                self.state,
                False,
                self.angle_units.value,
            )
            self._set_message(str(exc), alert_type="warning")
        self.mollier_panel.object = mollier_figure(self.state)
        self._refresh_process_plot()
        self.presdef_panel.object = pressure_deflection_figure(self.state, angle_units=self.angle_units.value)
        self.tbm_panel.object = theta_beta_m_figure(self.state)
        self.python_text.value = format_python_chain(self)
        self._refresh_choke_inputs()
        self._update_process_availability()

    def _refresh_process_plot(self, *_events) -> None:
        if self.state is None:
            self.process_plot_panel.object = None
            return
        property_name = PROCESS_PLOT_OPTIONS[self.process_plot_select.value]
        property_label = process_plot_label(
            property_name,
            self.is_dimensional,
            self.angle_units.value,
        )
        self.process_plot_panel.object = process_figure(
            self.state,
            property_name=property_name,
            property_label=property_label,
        )

    def view(self):
        process_buttons = {
            "Reset": self.initialize_button,
            "Normal Shock": self.shock_button,
            "Area Change": self.area_button,
            "Fanno": self.fanno_button,
            "Rayleigh": self.rayleigh_button,
            "Deflect": self.deflect_button,
        }

        for title, button in process_buttons.items():
            button.name = ""
            button.width = 82
            button.height = 36
            button.styles = PROCESS_BUTTON_STYLE
            button.stylesheets = [process_button_stylesheet(title)]

        for widget in [
            self.area_ratio_input,
            self.fanno_input,
            self.rayleigh_input,
            self.deflect_input,
        ]:
            widget.width = 76
            widget.sizing_mode = "fixed"

        self.family_input.width = 28
        self.family_input.sizing_mode = "fixed"
        self.strong_input.width = 28
        self.strong_input.sizing_mode = "fixed"
        self.family_input.styles = {"font-size": "6px"}
        self.strong_input.styles = {"font-size": "6px"}
        self.throat_input.width = 28
        self.throat_input.sizing_mode = "fixed"
        self.area_choke_input.width = 28
        self.area_choke_input.sizing_mode = "fixed"
        self.fanno_choke_input.width = 28
        self.fanno_choke_input.sizing_mode = "fixed"
        self.rayleigh_choke_input.width = 28
        self.rayleigh_choke_input.sizing_mode = "fixed"

        throat_control = self._checkbox_with_tooltip(self.throat_input, "throat_input")
        area_choke_control = self._checkbox_with_tooltip(self.area_choke_input, "area_choke_input")
        fanno_choke_control = self._checkbox_with_tooltip(self.fanno_choke_input, "fanno_choke_input")
        rayleigh_choke_control = self._checkbox_with_tooltip(self.rayleigh_choke_input, "rayleigh_choke_input")

        def fixed_box(widget, width, height=40):
            return pn.Column(
                widget,
                width=width,
                height=height,
                sizing_mode="fixed",
                styles={
                    "justify-content": "center",
                    "align-items": "center",
                },
            )

        def process_item(title, button, param_widgets=None, option_widgets=None, option_layout="row"):
            param_widgets = param_widgets or []
            option_widgets = option_widgets or []
            option_container_height = 40

            if param_widgets:
                params = pn.Column(
                    *[fixed_box(widget, 76, height=24) for widget in param_widgets],
                    width=82,
                    height=40,
                    sizing_mode="fixed",
                    styles={
                        "justify-content": "center",
                        "gap": "2px",
                    },
                )
            else:
                params = pn.Spacer(width=82, height=40)

            if option_widgets:
                if option_layout == "column":
                    option_width = max(34, max((widget.width or 26) for widget in option_widgets))
                    option_container_height = 60
                    options = pn.Column(
                        *(fixed_box(widget, widget.width or 26, height=24) for widget in option_widgets),
                        width=option_width,
                        height=option_container_height,
                        sizing_mode="fixed",
                        styles={
                            "justify-content": "center",
                            "align-items": "center",
                            "gap": "4px",
                        },
                    )
                elif option_layout == "area":
                    option_width = 96
                    options = pn.Row(
                        fixed_box(option_widgets[1], option_widgets[1].width or 28, height=24),
                        pn.Spacer(width=34, height=24),
                        fixed_box(option_widgets[0], option_widgets[0].width or 28, height=24),
                        pn.Spacer(width=6, height=24),
                        width=option_width,
                        height=40,
                        sizing_mode="fixed",
                        styles={
                            "align-items": "center",
                            "justify-content": "flex-start",
                            "gap": "0px",
                        },
                    )
                else:
                    option_width = max(
                        96,
                        sum((widget.width or 64) for widget in option_widgets) + 8 * (len(option_widgets) - 1),
                    )
                    options = pn.Row(
                        *(fixed_box(widget, widget.width or 64, height=24) for widget in option_widgets),
                        width=option_width,
                        height=40,
                        sizing_mode="fixed",
                        styles={
                            "align-items": "center",
                            "justify-content": "center",
                            "gap": "6px",
                        },
                    )
            else:
                options = pn.Spacer(width=96, height=40)

            return pn.Column(
                pn.pane.HTML(
                    f"<div style='font-size:11px; font-weight:600; color:#4b5563; margin-bottom:2px; line-height:1.1;'>{escape(title)}</div>",
                    sizing_mode="stretch_width",
                ),
                pn.Row(
                    fixed_box(button, 82),
                    pn.Column(
                        fixed_box(params, 82),
                        width=82,
                        height=40,
                        sizing_mode="fixed",
                        styles={"justify-content": "center", "margin-top": "-4px"},
                    ),
                    fixed_box(options, max(getattr(options, 'width', 96), 96), height=option_container_height),
                    sizing_mode="stretch_width",
                    styles={
                        "align-items": "center",
                        "gap": "8px",
                    },
                ),
                sizing_mode="stretch_width",
                styles=SUBPANEL_STYLE,
                margin=4,
            )

        options_panel = pn.Card(
            pn.Column(
                pn.Column(
                    "### State Units",
                    self.mode,
                    sizing_mode="stretch_width",
                    styles=SUBPANEL_STYLE,
                    margin=5,
                ),
                pn.Column(
                    "### Angle Units",
                    self.angle_units,
                    sizing_mode="stretch_width",
                    styles=SUBPANEL_STYLE,
                    margin=5,
                ),
                sizing_mode="stretch_width",
            ),
            title="Options",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        gas_panel = pn.Card(
            self.gamma_input,
            self.mw_input,
            title="Gas",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        initial_state_panel = pn.Card(
            self.mach_input,
            self.pres_input,
            self.temp_input,
            title="Initial State",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        process_panel = pn.Card(
            process_item("Reset", self.initialize_button),
            process_item(
                "Area Change",
                self.area_button,
                [self.area_ratio_input],
                [throat_control, area_choke_control],
                option_layout="area",
            ),
            process_item("Fanno", self.fanno_button, [self.fanno_input], [fanno_choke_control]),
            process_item("Rayleigh", self.rayleigh_button, [self.rayleigh_input], [rayleigh_choke_control]),
            process_item("Normal Shock", self.shock_button),
            process_item(
                "Deflect",
                self.deflect_button,
                [self.deflect_input],
                [self.family_input, self.strong_input],
                option_layout="column",
            ),
            self.message,
            title="Processes",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        history_container = pn.Card(
            self.history_panel,
            title="Process History",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        graphics_container = pn.Card(
            pn.FlexBox(
                pn.Card(
                    pn.Column(
                        self.process_plot_select,
                        self.process_plot_panel,
                        sizing_mode="stretch_width",
                    ),
                    title="Process",
                    collapsed=False,
                    styles=SUBPANEL_STYLE,
                    margin=5,
                    width=520,
                ),
                pn.Card(
                    pn.Column(
                        pn.Spacer(height=42),
                        self.mollier_panel,
                        sizing_mode="stretch_width",
                    ),
                    title="Mollier Diagram",
                    collapsed=False,
                    styles=SUBPANEL_STYLE,
                    margin=5,
                    width=520,
                ),
                pn.Card(
                    self.presdef_panel,
                    title="Pressure-Deflection Diagram",
                    collapsed=True,
                    styles=SUBPANEL_STYLE,
                    margin=5,
                    width=520,
                ),
                pn.Card(
                    self.tbm_panel,
                    title="Theta-Beta-M Diagram",
                    collapsed=True,
                    styles=SUBPANEL_STYLE,
                    margin=5,
                    width=520,
                ),
                flex_wrap="wrap",
                sizing_mode="stretch_width",
            ),
            title="Graphics",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        python_container = pn.Card(
            pn.Column(
                self.copy_python_button,
                self.python_text,
                sizing_mode="stretch_width",
            ),
            title="Python Expression",
            sizing_mode="stretch_width",
            collapsed=False,
            styles=CARD_STYLE,
            header_background=CARD_HEADER_COLOR,
            margin=10,
        )

        left = pn.Column(self.banner, gas_panel, initial_state_panel, process_panel, options_panel, width=390)
        right = pn.Column(history_container, graphics_container, python_container, width=1080)
        return pn.Row(left, right, sizing_mode="stretch_width")


app = GasLabApp()
app.view().servable(title="Gaslab App")
