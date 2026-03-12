import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

st.title("Comprehensive Mobile Care Dashboard")
st.subheader("Financial Model")

# -----------------------------
# Load billing data
# -----------------------------
billing = pd.read_csv("data/BillingTable.csv")

billing["Units"] = pd.to_numeric(billing["Units"], errors="coerce").fillna(0)

billing["Charge Amount"] = (
    billing["Charge Amount"]
    .astype(str)
    .str.replace(r"[^0-9.]", "", regex=True)
)
billing["Charge Amount"] = pd.to_numeric(billing["Charge Amount"], errors="coerce").fillna(0)

billing["Non-Facility Difference"] = (
    billing.get("Non-Facility Difference", pd.Series(0))
    .astype(str)
    .str.replace(r"[^0-9.]", "", regex=True)
)
billing["Non-Facility Difference"] = pd.to_numeric(
    billing["Non-Facility Difference"], errors="coerce"
).fillna(0)

cpt_options = billing["CPT Code"].dropna().unique()

# -----------------------------
# Two Column Layout
# -----------------------------
left_col, right_col = st.columns([1,1])

# -----------------------------
# LEFT COLUMN
# -----------------------------
with left_col:

    st.header("Staffing Inputs")

    physician = st.number_input("Physician", min_value=0, value=1, step=1)

    split_time = st.checkbox(
        "Split clinic time between Physician(s) and Advanced Practice Provider(s)"
    )

    physician_time_pct = 1.0
    app_relative_reimbursement = 1.0

    if split_time:

        physician_time_pct = st.slider(
            "Physician share of clinic operating hours",
            0,
            100,
            50
        ) / 100

        st.caption(
            f"Physician is present in the mobile clinic for {physician_time_pct*100:.0f}% of operating hours"
        )

        app_relative_reimbursement = st.slider(
            "Reimbursement Rate of APPs relative to Physicians",
            0,
            100,
            85
        ) / 100

    medical_assistant = st.number_input("Medical Assistant", 0, 10, 1)
    registered_nurse = st.number_input("Registered Nurse", 0, 10, 0)
    driver = st.number_input("Driver", 1, 5, 1, disabled=True)
    community_health_worker = st.number_input("Community Health Worker", 0, 10, 0)

    st.header("Salary and Equipment Costs")

    physician_salary = st.number_input("Physician Salary ($/hour)", 0.0, 500.0, 110.0)
    APP_salary = st.number_input("Advanced Practice Provider Salary ($/hour)", 0.0, 200.0, 62.5)

    medical_assistant_salary = st.number_input("Medical Assistant Salary ($/hour)", 0.0, 200.0, 30.0)
    registered_nurse_salary = st.number_input("Registered Nurse Salary ($/hour)", 0.0, 200.0, 60.0)
    driver_salary = st.number_input("Driver Salary ($/hour)", 0.0, 100.0, 30.0)
    community_health_worker_salary = st.number_input("Community Health Worker Salary ($/hour)", 0.0, 100.0, 25.0)

    equipment_cost = st.number_input("Fixed Weekly Cost ($/week)", 0.0, 10000.0, 100.0)
    gas_energy_cost = st.number_input("Daily Cost ($/day)", 0.0, 1000.0, 50.0)

    st.header("Timeframe")

    num_weeks = st.number_input("Number of weeks", 1, 52, 1)
    days_per_week = st.number_input("Days of operation per week", 1, 7, 3)
    hours_per_day = st.number_input("Hours of operation per day", 1, 24, 4)

# -----------------------------
# RIGHT COLUMN
# -----------------------------
with right_col:

    st.header("Billing Codes for the Mobile Unit")
    st.dataframe(billing.iloc[:, :6])

    st.header("Billing and Reimbursement")

    percent_charge_reimbursed = st.slider(
        "% of charge amount reimbursed", 0, 100, 25
    )

    percent_nonfacility_reimbursed = st.slider(
        "% of non-facility rate reimbursed", 0, 100, 25
    )

    st.subheader("Billing Codes and Clinic Time Allocation")

    if "billing_rows" not in st.session_state:
        st.session_state.billing_rows = [
            {"CPT Code": cpt_options[0], "Percentage": 0.0}
        ]

    def add_row():
        st.session_state.billing_rows.append(
            {"CPT Code": cpt_options[0], "Percentage": 0.0}
        )

    for i, row in enumerate(st.session_state.billing_rows):

        cols = st.columns([2,1,0.5])

        with cols[0]:
            row["CPT Code"] = st.selectbox(
                f"CPT Code {i+1}",
                cpt_options,
                index=list(cpt_options).index(row["CPT Code"]) if row["CPT Code"] in cpt_options else 0,
                key=f"cpt_{i}"
            )

        with cols[1]:
            row["Percentage"] = st.number_input(
                f"% Time {i+1}",
                0.0,
                100.0,
                row["Percentage"],
                key=f"pct_{i}"
            )

        with cols[2]:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.billing_rows.pop(i)
                st.rerun()

    st.button("Add Row", on_click=add_row)

# -----------------------------
# MODEL CALCULATIONS
# -----------------------------

attendance = np.arange(0,101,1)

total_cost = (
    days_per_week*num_weeks*hours_per_day*(
        physician_salary*physician*physician_time_pct +
        APP_salary*physician*(1-physician_time_pct) +
        medical_assistant_salary*medical_assistant +
        registered_nurse_salary*registered_nurse +
        community_health_worker_salary*community_health_worker
    )
    + days_per_week*num_weeks*(hours_per_day+3)*driver_salary
    + num_weeks*equipment_cost
    + num_weeks*days_per_week*gas_energy_cost
)

charge_pct = percent_charge_reimbursed/100
nonfacility_pct = percent_nonfacility_reimbursed/100

total_units = num_weeks*days_per_week*hours_per_day*2*physician

total_revenue = 0

for row in st.session_state.billing_rows:

    cpt = row["CPT Code"]
    proportion = row["Percentage"]/100

    match = billing[billing["CPT Code"] == cpt]

    if match.empty:
        continue

    units = match["Units"].iloc[0]
    charge = match["Charge Amount"].iloc[0]
    nonfac = match["Non-Facility Difference"].iloc[0]

    if units == 0:
        continue

    code_freq = total_units*proportion/units

    code_revenue = code_freq*(charge_pct*charge + nonfacility_pct*nonfac)

    total_revenue += code_revenue

adjusted_revenue = total_revenue*(physician_time_pct + (1-physician_time_pct)*app_relative_reimbursement)

break_even_attendance = None
if adjusted_revenue > 0:
    break_even_attendance = (total_cost/adjusted_revenue)*100

# -----------------------------
# FULL WIDTH GRAPH
# -----------------------------

st.header("Cost and Revenue by Attendance Rate")

if break_even_attendance:
    st.metric("Break-Even Attendance Rate", f"{break_even_attendance:.1f}%")

plot_df = pd.DataFrame({
    "Attendance (%)": np.tile(attendance,2),
    "Amount ($)": np.concatenate([
        np.repeat(total_cost,len(attendance)),
        adjusted_revenue*(attendance/100)
    ]),
    "Type": ["Cost"]*len(attendance) + ["Revenue"]*len(attendance)
})

chart = alt.Chart(plot_df).mark_line(strokeWidth=3).encode(
    x="Attendance (%)",
    y="Amount ($)",
    color=alt.Color(
        "Type",
        scale=alt.Scale(domain=["Cost","Revenue"],range=["red","green"]),
        legend=alt.Legend(title="Legend")
    )
)

if break_even_attendance and 0 <= break_even_attendance <= 100:

    breakeven_df = pd.DataFrame({
        "Attendance (%)":[break_even_attendance]
    })

    breakeven_line = alt.Chart(breakeven_df).mark_rule(
        color="blue",
        strokeDash=[6,6],
        strokeWidth=2
    ).encode(
        x="Attendance (%)"
    )

    chart = chart + breakeven_line

st.altair_chart(chart,use_container_width=True)

st.divider()

with st.expander("Glossary and Model Methodology", expanded=False):

    st.subheader("Overview")

    st.write(
        """
        Using a combination of inputs around staffing, equipment, time and billing costs, the above model plots the projected cost/revenue of the mobile clinic as a function of appointment attendance.
        """
    )

    st.subheader("Key Terms")

    st.write(
        """
        **Attendance Rate**  
        The percentage of scheduled appointments actually attended by patients.

        **Break-Even Attendance Rate**  
        The attendance rate for which projected revenue equals projected cost.

        **CPT Code**  
        The billing code used for a specific service. The table on the top right gives descriptions for each code that could be used on the mobile unit.

        **Charge Amount**  
        The set amount charged by the hospital for a given CPT code (based on previous CCP charge data).

        **Non-Facility Difference**  
        The increase between the non-facility rate charged for a given CPT code on the mobile unit compared to the facility rate for that same code at an in-hospital appointment.

        **Advanced Practice Provider (APP)**  
        The APP section in Staffing Inputs considers a scenario where a physician is present for only a portion of clinic hours with an APP working the rest of the time. APPs generally bill at a percentage of the amount physicians can (around 85%), so we included a slider to account for this difference in revenue.
        """
    )

    st.subheader("Model Assumptions")

    st.write(
        """
        **Appointment Capacity**

        The model calculates the total time available for appointments over the given timeframe and divides this time based on the billing code proportions specified in the Billing Codes and Clinic Time Allocation Section. The model then divides a billing code's allocated time by the estimated length of that appointment to estimate the number of appointments of that type. Note: the model assumes that patient attendance impacts all appointment types at roughly equal rates.

        **Staffing Costs**

        While many employees on the unit will be salaried, the model estimates the hourly cost for each worker type and multiplies these values by the total number of hours worked in the specified timeframe. To account for set-up, charging and driving time, the driver's hours per day are estimated to be three greater than the other employees.

        **Operational Costs**

        Operational costs are split into two inputs: fixed weekly costs for general equipment in the unit and the daily cost to account for gas/energy needs that vary by how many days/week the clinic is used.

        **Revenue Estimation**

        Once the model calculates the number of appointments for each billing code in a given scenario, the max potential revenue for a code is calculated as (# of appointments) * (Charge Amount * (% of Charge Amount Reimbursed) + Non-facility Difference * (% of Non-facility Rate Reimbursed)).

        **Attendance Adjustment**

        The revenue line is plotted as the total max potential revenue multiplied by the attendance rate.
        """
    )

    st.subheader("Interpretation")

    st.write(
        """
        While this model is far from perfect and is surely missing factors that will affect profitability of the unit, we hope it can serve as a useful tool for comparing the relative financial feasibility of different staffing and billing scenarios.
        """
    )