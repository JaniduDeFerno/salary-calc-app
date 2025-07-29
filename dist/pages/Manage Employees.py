import math
import streamlit as st
import pandas as pd
import os

# --- Page Setup ---
st.set_page_config(page_title="Manage Employees")
st.title("👤 Manage Employee Settings")

# File paths
os.makedirs("data", exist_ok=True)
attendance_cache_path = "data/attendance_processed.csv"
employee_data_file = "data/employee_data.csv"

# Load existing employee data
if os.path.exists(employee_data_file) and os.path.getsize(employee_data_file) > 0:
    employee_df = pd.read_csv(employee_data_file)
else:
    employee_df = pd.DataFrame(columns=[
        "Employee Name", "Employee Type", "EPF No", "Basic Salary",
        "BRA", "Salary for EPF",  # <-- ADD THESE LINES
        "Normal Pay Rate", "Normal Pay Hourly Rate", "Overtime Pay Hourly Rate",
        "Sunday Pay Rate", "Attendance Bonus", "Other Allowances", "Meal Allowance",
        "EPF 8%", "EPF 12%", "ETF 3%"
    ])
# Load employee names from attendance file
if os.path.exists(attendance_cache_path):
    attendance_df = pd.read_csv(attendance_cache_path)
    employee_names = sorted(attendance_df['Name'].dropna().unique())
else:
    employee_names = sorted(employee_df["Employee Name"].unique())

# Employee Types and Presets with explicit float values
employee_type_presets = {
    "Working Staff (BULB)": {
        "Basic Salary": 24000.0, "Normal Pay Rate": 1080.0, "Sunday Pay Rate": 1620.0, "Attendance Bonus": 1500.0},
    "Employee (ORIN)": {
        "Basic Salary": 24000.0, "Normal Pay Rate": 1080.0, "Sunday Pay Rate": 1620.0, "Attendance Bonus": 3000.0},
    "Employee (Nescafe)": {
        "Basic Salary": 24000.0, "Normal Pay Rate": 1080.0, "Sunday Pay Rate": 1620.0, "Attendance Bonus": 3000.0},
    "Employee (Siyallanka)": {
        "Basic Salary": 24000.0, "Normal Pay Rate": 1080.0, "Sunday Pay Rate": 1620.0, "Attendance Bonus": 3000.0}
}

# --- Salary Data Form ---
st.subheader("📝 Set or Update Static Salary Details")

if employee_names:
    selected_employee = st.selectbox("Select Employee", employee_names)

    existing = employee_df[employee_df["Employee Name"] == selected_employee]

    def get_val(field, default=0.0):
        return float(existing[field].values[0]) if not existing.empty and field in existing else default

    def get_str(field, default=""):
        return str(existing[field].values[0]) if not existing.empty and field in existing else default

    employee_type = st.selectbox(
        "Employee Type",
        list(employee_type_presets.keys()),
        index=list(employee_type_presets.keys()).index(get_str("Employee Type", "Working Staff (BULB)"))
    )

    # Load presets automatically
    preset = employee_type_presets[employee_type]

    epf_no = st.text_input("EPF No", value=get_str("EPF No"))

    basic_salary = st.number_input(
        "Basic Salary",
        min_value=0.0,
        value=get_val("Basic Salary", float(preset["Basic Salary"]))
    )
    bra = st.number_input(
        "BRA",
        min_value=0.0,
        value=get_val("BRA", 3000.0)
    )
    salary_for_epf = basic_salary + bra
    st.markdown(f"**Salary for EPF:** Rs. `{salary_for_epf:,.2f}`")

    normal_rate = st.number_input(
        "Normal Pay Rate (Daily)",
        min_value=0.0,
        value=get_val("Normal Pay Rate", float(preset["Normal Pay Rate"]))
    )

    normal_hourly = math.ceil(normal_rate / 8)
    overtime_hourly = math.ceil(normal_hourly * 1.5)

    st.markdown(f"**⏱️ Normal Pay Hourly Rate:** Rs. `{normal_hourly}`")
    st.markdown(f"**⏱️ Overtime Pay Hourly Rate (1.5x):** Rs. `{overtime_hourly}`")

    sunday_rate = st.number_input(
        "Sunday Pay Rate",
        min_value=0.0,
        value=get_val("Sunday Pay Rate", float(preset["Sunday Pay Rate"]))
    )
    bonus = st.number_input(
        "Attendance Bonus",
        min_value=0.0,
        value=get_val("Attendance Bonus", float(preset["Attendance Bonus"]))
    )
    other_allow = st.number_input(
        "Other Allowances",
        min_value=0.0,
        value=get_val("Other Allowances")
    )
    meal = st.number_input(
        "Meal Allowance",
        min_value=0.0,
        value=get_val("Meal Allowance")
    )

    epf_8 = round(salary_for_epf * 0.08, 2)
    epf_12 = round(salary_for_epf * 0.12, 2)
    etf_3 = round(salary_for_epf * 0.03, 2)

    st.markdown(f"**📌 EPF 8% (Employee):** Rs. `{epf_8}`")
    st.markdown(f"**📌 EPF 12% (Employer):** Rs. `{epf_12}`")
    st.markdown(f"**📌 ETF 3% (Employer):** Rs. `{etf_3}`")

    if st.button("💾 Save Employee Data"):
        new_record = pd.DataFrame([{
            "Employee Name": selected_employee,
            "Employee Type": employee_type,
            "EPF No": epf_no,
            "Basic Salary": basic_salary,
            "BRA": bra,
            "Salary for EPF": salary_for_epf,
            "Normal Pay Rate": normal_rate,
            "Normal Pay Hourly Rate": normal_hourly,
            "Overtime Pay Hourly Rate": overtime_hourly,
            "Sunday Pay Rate": sunday_rate,
            "Attendance Bonus": bonus,
            "Other Allowances": other_allow,
            "Meal Allowance": meal,
            "EPF 8%": epf_8,
            "EPF 12%": epf_12,
            "ETF 3%": etf_3
        }])

        employee_df = employee_df[employee_df["Employee Name"] != selected_employee]
        employee_df = pd.concat([employee_df, new_record], ignore_index=True)
        employee_df.to_csv(employee_data_file, index=False)
        st.success(f"✅ Salary data saved for {selected_employee}")
else:
    st.warning("⚠️ No employee names available. Upload an attendance CSV first.")
