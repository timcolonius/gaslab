"""
Editable UI tooltip strings for the GasLab Panel app.

Update the values in ``TOOLTIPS`` to change the hover help shown on buttons
and controls without touching the layout code in ``app.py``.
"""

TOOLTIPS = {
    "mode": "Choose whether GasLab displays and initializes states in nondimensional or dimensional form.",
    "angle_units": "Choose whether entered and displayed angles use radians or degrees.",
    "gamma_input": "Ratio of specific heats for the gas.",
    "mw_input": "Gas molecular weight in grams per mole for dimensional calculations.",
    "mach_input": "Initial Mach number of the starting state.",
    "pres_input": "Reservoir pressure used when initializing a dimensional state, in atmospheres.",
    "temp_input": "Reservoir temperature used when initializing a dimensional state, in kelvin.",
    "area_ratio_input": "Area ratio A2/A1 applied in the quasi-one-dimensional area-change process.",
    "throat_input": "Indicates that the flow passes through a throat between the old and new areas.",
    "area_choke_input": "Automatically use the area ratio that chokes the current upstream state.",
    "fanno_input": "Friction parameter 4fL/D for the Fanno-flow process.",
    "fanno_choke_input": "Automatically use the critical Fanno parameter that chokes the current upstream state.",
    "rayleigh_input": "Stagnation-temperature ratio T0_2/T0_1 for the Rayleigh-flow process.",
    "rayleigh_choke_input": "Automatically use the critical Rayleigh ratio that chokes the current upstream state.",
    "deflect_input": "Flow deflection angle entered in the currently selected angle units.",
    "family_input": "Characteristic family toggle for deflection. Use C+ for the right-running family and C- for the left-running family.",
    "strong_input": "Wave-strength toggle for oblique shocks. Weak selects the weak-shock branch; Strong selects the strong-shock branch.",
    "process_plot_select": "Select which state property to display in the Process bar chart.",
    "initialize_button": "Reset the process chain back to a single initial state using the current gas and initial-state inputs.",
    "shock_button": "Apply a normal shock to the current final state.",
    "area_button": "Apply a quasi-one-dimensional isentropic area change to the current final state.",
    "fanno_button": "Apply a Fanno-flow friction process to the current final state.",
    "rayleigh_button": "Apply a Rayleigh-flow heat-transfer process to the current final state.",
    "deflect_button": "Apply a supersonic flow turn rom the current final state through an oblique shock or Prandtl-Meyer expansion.",
    "copy_python_button": "Copy the equivalent chained Python expression for the current process history.",
}
