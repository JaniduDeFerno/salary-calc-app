import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date

# --- PAGE SETUP ---
st.set_page_config(page_title="Monthly Salary Summary", layout="wide")
st.title("📊 Monthly Salary Summary (By Department/Employee Type & Total)")

# --- FILE PATHS ---
employee_file = "data/employee_data.csv"
deduction_file = "data/monthly_deductions.csv"

# --- LOAD DATA ---
def load_data(path, empty_cols):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=empty_cols)

employee_df = load_data(employee_file, [
    "Employee Name", "Employee Type", "Department", "EPF No", "Basic Salary",
    "BRA", "Salary for EPF", "Normal Pay Rate", "Normal Pay Hourly Rate",
    "Overtime Pay Hourly Rate", "Sunday Pay Rate", "Attendance Bonus",
    "Other Allowances", "Meal Allowance", "EPF 8%", "EPF 12%", "ETF 3%"
])
deduction_df = load_data(deduction_file, [
    "Employee Name", "Year", "Month", "Monthly Advanced", "Monthly Loan Deduction"
])

# --- UI ---
years = sorted(deduction_df['Year'].unique()) if not deduction_df.empty else [date.today().year]
selected_year = st.selectbox("Year", years, index=len(years)-1)
months = list(calendar.month_name)[1:]
selected_month = st.selectbox("Month", months, index=date.today().month - 1)

# --- SMART GROUP FIELD (Department or Employee Type) ---
group_field = "Department" if "Department" in employee_df.columns else "Employee Type"
emp_cols = ["Employee Name", group_field, "Basic Salary", "BRA", "Salary for EPF",
            "Other Allowances", "Meal Allowance", "Attendance Bonus"]

# --- DEPARTMENT/TYPE FILTER ---
all_depts = sorted(employee_df[group_field].dropna().unique())
selected_depts = st.multiselect(
    f"Filter by {group_field} (or select All)",
    options=all_depts,
    default=all_depts,
    key="dept_filter"
)

# --- MERGE DATA FOR THE MONTH ---
month_df = deduction_df[
    (deduction_df["Year"] == selected_year) &
    (deduction_df["Month"] == selected_month)
].copy()

# (Merge for all employees/types, even if no entry in month)
summary = pd.merge(employee_df[emp_cols], month_df, how="left", on="Employee Name")

# --- FILTER ON SELECTED DEPARTMENTS/TYPES ---
if selected_depts:
    summary = summary[summary[group_field].isin(selected_depts)]

# --- CALCULATE AMOUNTS, FILLING NA WITH 0 ---
summary["Basic Salary"] = summary["Basic Salary"].fillna(0)
summary["BRA"] = summary["BRA"].fillna(0)
summary["Salary for EPF"] = summary["Salary for EPF"].fillna(0)
summary["Other Allowances"] = summary["Other Allowances"].fillna(0)
summary["Meal Allowance"] = summary["Meal Allowance"].fillna(0)
summary["Attendance Bonus"] = summary["Attendance Bonus"].fillna(0)
summary["Monthly Advanced"] = summary["Monthly Advanced"].fillna(0)
summary["Monthly Loan Deduction"] = summary["Monthly Loan Deduction"].fillna(0)

summary["Gross Salary"] = summary["Basic Salary"] + summary["BRA"] + \
    summary["Other Allowances"] + summary["Meal Allowance"] + summary["Attendance Bonus"]
summary["EPF 8%"] = summary["Salary for EPF"] * 0.08
summary["EPF 12%"] = summary["Salary for EPF"] * 0.12
summary["ETF 3%"] = summary["Salary for EPF"] * 0.03

summary["Advance"] = summary["Monthly Advanced"]
summary["Loan"] = summary["Monthly Loan Deduction"]
summary["EPF Deduction"] = summary["EPF 8%"]
summary["ETF Contribution"] = summary["ETF 3%"]

# --- AGGREGATE BY GROUP FIELD (always include all types) ---
grouped = summary.groupby(group_field, dropna=False).agg({
    "Gross Salary": "sum",
    "Advance": "sum",
    "Loan": "sum",
    "EPF Deduction": "sum",
    "ETF Contribution": "sum"
}).reindex(all_depts, fill_value=0).reset_index()

# --- SHOW GROUP-WISE SUMMARY ---
st.markdown(f"### 🏢 {group_field} wise Salary Summary")
st.dataframe(grouped.style.format({
    "Gross Salary": "Rs {:,.2f}",
    "Advance": "Rs {:,.2f}",
    "Loan": "Rs {:,.2f}",
    "EPF Deduction": "Rs {:,.2f}",
    "ETF Contribution": "Rs {:,.2f}",
}), use_container_width=True)

# --- SHOW OVERALL TOTAL ---
totals = grouped[["Gross Salary", "Advance", "Loan", "EPF Deduction", "ETF Contribution"]].sum()
st.markdown("### 🏦 Company Total")
st.write(
    f"""
    <table style='width:400px'>
        <tr><td><b>Total Salary</b></td><td align='right'><b>Rs {totals['Gross Salary']:,.2f}</b></td></tr>
        <tr><td><b>Total Advances</b></td><td align='right'>Rs {totals['Advance']:,.2f}</td></tr>
        <tr><td><b>Total Loan Deductions</b></td><td align='right'>Rs {totals['Loan']:,.2f}</td></tr>
        <tr><td><b>Total EPF Deductions</b></td><td align='right'>Rs {totals['EPF Deduction']:,.2f}</td></tr>
        <tr><td><b>Total ETF Contributions</b></td><td align='right'>Rs {totals['ETF Contribution']:,.2f}</td></tr>
    </table>
    """,
    unsafe_allow_html=True
)

# --- OPTIONAL: List All Employee Values ---
with st.expander("See detailed per-employee breakdown"):
    st.dataframe(
        summary[["Employee Name", group_field, "Gross Salary", "Advance", "Loan", "EPF Deduction", "ETF Contribution"]]
        .sort_values([group_field, "Employee Name"])
        .style.format({
            "Gross Salary": "Rs {:,.2f}",
            "Advance": "Rs {:,.2f}",
            "Loan": "Rs {:,.2f}",
            "EPF Deduction": "Rs {:,.2f}",
            "ETF Contribution": "Rs {:,.2f}",
        }),
        use_container_width=True
    )
