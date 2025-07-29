import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import calendar
from datetime import date, datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Bulk Salary Slips", layout="wide")
st.title("🖨️ Bulk Print Salary Slips")

# --- GLOBAL STYLE BLOCK ---
STYLE_BLOCK = """
<style>
    .slip-set {
        display: inline-block;
        width: 5.2cm;
        min-width: 5.2cm;
        max-width: 5.3cm;
        vertical-align: top;
        margin: 0 0.4cm 20px 0.4cm;
    }
    .slip {
        width: 5cm;
        height: auto;
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 6px;
        font-size: 11px;
        margin-bottom: 20px;
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        background: white;
        box-sizing: border-box;
    }
    .slip h3, .slip h5 {
        text-align: center;
        margin: 6px 0;
        font-size: 13px;
        font-weight: 600;
    }
    .slip table {
        width: 100%;
        border-collapse: collapse;
    }
    .slip td {
        padding: 2px 0;
        vertical-align: top;
    }
    .slip hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 6px 0;
    }
    .net-box {
        border-top: 2px solid #000;
        padding-top: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .print-button { margin-bottom:20px; }
    @media print {
        .print-button { display: none; }
        .slip-set { page-break-inside: avoid; }
        body { background:white !important; }
    }
    body { background:white !important; }
</style>
"""

# --- FILE PATHS ---
employee_file = "data/employee_data.csv"
deduction_file = "data/monthly_deductions.csv"
summary_root_folder = "data/monthly_summary"
holiday_file = "data/holidays.csv"

# --- LOAD DATA ---
def load_data(path, empty_cols):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=empty_cols)

employee_df = load_data(employee_file, [
    "Employee Name", "Employee Type", "EPF No", "Basic Salary",
    "BRA", "Salary for EPF", "Normal Pay Rate", "Normal Pay Hourly Rate",
    "Overtime Pay Hourly Rate", "Sunday Pay Rate", "Attendance Bonus",
    "Other Allowances", "Meal Allowance", "EPF 8%", "EPF 12%", "ETF 3%"
])
deduction_df = load_data(deduction_file,
    ["Employee Name", "Year", "Month", "Monthly Advanced", "Monthly Loan Deduction"])
holidays_df = load_data(holiday_file, ["Holiday Date", "Holiday Name", "Year", "Month"])
holidays_df['Holiday Date'] = pd.to_datetime(holidays_df['Holiday Date'], errors='coerce')

# --- UI ---
employee_types = sorted(employee_df["Employee Type"].dropna().unique())
selected_types = st.multiselect("Filter by Employee Type", employee_types, default=employee_types)

filtered_employees = employee_df[employee_df["Employee Type"].isin(selected_types)]
selected_employees = st.multiselect("Select Employees", filtered_employees["Employee Name"].tolist(), default=filtered_employees["Employee Name"].tolist())

col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox("Year", list(range(2020, date.today().year + 1)), index=date.today().year - 2020)
with col2:
    selected_month = st.selectbox("Month", list(calendar.month_name)[1:], index=date.today().month - 1)

month_num = list(calendar.month_name).index(selected_month)

# --- SALARY SLIP RENDER (structure identical to Print Salary Slips.py) ---
def render_salary_slip(
    selected_employee, emp_data, summary_df, deduction_df,
    selected_year, selected_month, month_num, holidays_df
):
    normal_rate = emp_data["Normal Pay Rate"].values[0]
    overtime_hourly = emp_data["Overtime Pay Hourly Rate"].values[0]
    sunday_rate = emp_data["Sunday Pay Rate"].values[0]
    bonus_raw = emp_data["Attendance Bonus"].values[0]
    other_allow = emp_data["Other Allowances"].values[0]
    meal = emp_data["Meal Allowance"].values[0]
    epf_no = emp_data["EPF No"].values[0] if "EPF No" in emp_data else "N/A"
    basic_salary = emp_data["Basic Salary"].values[0]
    bra = emp_data["BRA"].values[0]
    salary_for_epf = emp_data["Salary for EPF"].values[0]
    epf_8 = round(salary_for_epf * 0.08, 2)
    epf_12 = round(salary_for_epf * 0.12, 2)
    etf_3 = round(salary_for_epf * 0.03, 2)

    summary_df['Day'] = summary_df['Day'].astype(str)

    def classify_real_day(att):
        if att > 6.5:
            return 1.0
        elif 0 < att <= 6.5:
            return 0.5
        return 0.0

    if 'ATT_Time' not in summary_df.columns and 'Work Time' in summary_df.columns:
        def time_to_float(tstr):
            try:
                h, m = map(int, str(tstr).split(":"))
                return round(h + m / 60, 2)
            except:
                return 0
        summary_df['ATT_Time'] = summary_df['Work Time'].apply(time_to_float)
    if 'RND(ATT_Time)' not in summary_df.columns:
        summary_df['RND(ATT_Time)'] = summary_df['ATT_Time'].round().astype(int)
    summary_df['Real Day'] = summary_df['RND(ATT_Time)'].apply(classify_real_day)

    if 'OT Time' not in summary_df.columns:
        if 'Clock Out' in summary_df.columns:
            def calc_ot(row):
                try:
                    out = str(row['Clock Out']).strip()
                    if out in ["", "0", "00:00", "nan", "NaN"]:
                        return 0
                    out_time = datetime.strptime(out, "%H:%M")
                    std_out = datetime.strptime("17:00", "%H:%M")
                    if out_time > std_out:
                        return round((out_time - std_out).seconds / 3600)
                    return 0
                except:
                    return 0
            summary_df['OT Time'] = summary_df.apply(calc_ot, axis=1)
        else:
            summary_df['OT Time'] = 0

    weekday_full = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 1.0)]
    weekday_half = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 0.5)]
    sunday_full = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 1.0)]
    sunday_half = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 0.5)]

    weekday_overtime = summary_df[summary_df['Day'].str.lower() != 'sunday']['OT Time'].sum()

    filtered_holidays = holidays_df[
        (holidays_df['Year'] == selected_year) & (holidays_df['Month'] == selected_month)
    ]
    govt_holiday_dates = set(filtered_holidays['Holiday Date'].dt.date.dropna())

    total_days = calendar.monthrange(selected_year, month_num)[1]
    all_dates = pd.date_range(f"{selected_year}-{month_num:02d}-01", periods=total_days)
    total_sundays = sum(1 for d in all_dates if d.day_name() == "Sunday")
    total_weekdays = total_days - total_sundays
    govt_weekday_holidays = sum(1 for d in govt_holiday_dates if pd.to_datetime(d).day_name() not in ["Saturday", "Sunday"])
    bonus_threshold = total_weekdays - govt_weekday_holidays - 2
    bonus = bonus_raw if len(weekday_full) >= bonus_threshold else 0

    emp_deductions = deduction_df[
        (deduction_df["Employee Name"] == selected_employee) &
        (deduction_df["Year"] == selected_year) &
        (deduction_df["Month"] == selected_month)
    ]
    monthly_advance = emp_deductions["Monthly Advanced"].values[0] if not emp_deductions.empty else 0
    monthly_loan = emp_deductions["Monthly Loan Deduction"].values[0] if not emp_deductions.empty else 0

    # ---- Managerial Override ----
    emp_type = emp_data["Employee Type"].values[0]
    if emp_type in ["Employee (ORIN)", "Employee (Nescafe)", "Employee (Siyallanka)"]:
        base_salary = salary_for_epf
        sunday_pay = 0
        ot_pay = 0
        bonus = bonus_raw
        gross = base_salary + bonus + other_allow + meal
        net = gross - monthly_advance - monthly_loan - epf_8
        # For neatness in slip display:
        weekday_full = []
        weekday_half = []
        sunday_full = []
        sunday_half = []
        weekday_overtime = 0
    else:
        base_salary = (len(weekday_full) * normal_rate) + (len(weekday_half) * normal_rate / 2)
        sunday_pay = (len(sunday_full) * sunday_rate) + (len(sunday_half) * sunday_rate / 2)
        ot_pay = weekday_overtime * overtime_hourly
        gross = base_salary + ot_pay + sunday_pay + bonus + other_allow + meal
        net = gross - monthly_advance - monthly_loan - epf_8

    # --- Both formats (unchanged) ---
    format1 = f"""
        <div class='slip'>
            <table>
                <tr><td><strong>Employee</strong></td><td align='right'><strong>{selected_employee}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>Salary per Day</td><td align='right'>{normal_rate:,.2f}</td></tr>
                <tr><td>Full Days</td><td align='right'>{len(weekday_full)}</td></tr>
                <tr><td>Half Days</td><td align='right'>{len(weekday_half)}</td></tr>
            </table>
            <hr>
            <table>
                <tr><td><strong>Base Salary</strong></td><td align='right'><strong>{base_salary:,.2f}</strong></td></tr>
                <tr><td>OT ({weekday_overtime:.2f} × {overtime_hourly})</td><td align='right'>{ot_pay:,.2f}</td></tr>
                <tr><td>Sunday Pay</td><td align='right'>{sunday_pay:,.2f}</td></tr>
                <tr><td>Attendance Bonus</td><td align='right'>{bonus:,.2f}</td></tr>
                <tr><td>Other Allowances</td><td align='right'>{other_allow:,.2f}</td></tr>
            </table>
            <hr>
            <table>
                <tr><td><strong>Gross Salary</strong></td><td align='right'><strong>{gross:,.2f}</strong></td></tr>
                <tr><td>Meal Allowance</td><td align='right'>{meal:,.2f}</td></tr>
                <tr><td>Advance</td><td align='right'>{monthly_advance:,.2f}</td></tr>
                <tr><td>Loan</td><td align='right'>{monthly_loan:,.2f}</td></tr>
                <tr><td>EPF 8%</td><td align='right'>{epf_8:,.2f}</td></tr>
            </table>
            <hr>
            <table class='net-box'>
                <tr><td><strong>Net Salary</strong></td><td align='right'><strong>{net:,.2f}</strong></td></tr>
            </table>
        </div>
        """

    format2 = f"""
        <div class='slip'>
            <h3>Darshana Enterprises</h3>
            <table>
                <tr><td>{selected_month} - {selected_year}</td><td align='right'>EPF No: <strong>{epf_no}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td><strong>Employee</strong></td><td align='right'><strong>{selected_employee}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>Basic Salary</td><td align='right'>{basic_salary:,.2f}</td></tr>
                <tr><td>BRA</td><td align='right'>{bra:,.2f}</td></tr>
            </table>
            <hr style="border-top: 1px dashed #888;">
            <table>
                <tr><td><strong>Salary For EPF</strong></td><td align='right'><strong>{salary_for_epf:,.2f}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>OT ({weekday_overtime:.2f} × {overtime_hourly})</td><td align='right'>{ot_pay:,.2f}</td></tr>
                <tr><td>Sunday Pay</td><td align='right'>{sunday_pay:,.2f}</td></tr>
                <tr><td>Attendance Bonus</td><td align='right'>{bonus:,.2f}</td></tr>
                <tr><td>Other Allowances</td><td align='right'>{other_allow:,.2f}</td></tr>
            </table>
            <hr>
            <table>
                <tr><td><strong>Gross Salary</strong></td><td align='right'><strong>{gross:,.2f}</strong></td></tr>
                <tr><td>Meal Allowance</td><td align='right'>{meal:,.2f}</td></tr>
                <tr><td>Advance</td><td align='right'>{monthly_advance:,.2f}</td></tr>
                <tr><td>Loan</td><td align='right'>{monthly_loan:,.2f}</td></tr>
                <tr><td>EPF 8%</td><td align='right'>{epf_8:,.2f}</td></tr>
            </table>
            <hr>
            <table class='net-box'>
                <tr><td><strong>Net Salary</strong></td><td align='right'><strong>{net:,.2f}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>EPF 12%</td><td align='right'>{epf_12:,.2f}</td></tr>
                <tr><td>ETF 3%</td><td align='right'>{etf_3:,.2f}</td></tr>
            </table>
        </div>
        """
    return f"<div class='slip-set'>{format1}{format2}</div>"

# --- RENDER ALL SELECTED EMPLOYEES, 3 SETS PER ROW ---
html_blocks = []
for idx, emp_name in enumerate(selected_employees):
    emp_data = employee_df[employee_df["Employee Name"] == emp_name]
    summary_path = f"{summary_root_folder}/{selected_year}/{selected_month}/{emp_name}_{selected_month}_{selected_year}.csv"
    if not os.path.exists(summary_path) or emp_data.empty:
        continue
    summary_df = pd.read_csv(summary_path)
    html_blocks.append(render_salary_slip(emp_name, emp_data, summary_df, deduction_df, selected_year, selected_month, month_num, holidays_df))

print_btn = """<div class='print-button' style='margin-bottom:20px;'>
<a href="javascript:window.print()" style="padding:8px 20px; background:#28a745; color:white; text-decoration:none; border-radius:4px; font-size:16px;">🖨️ Print All</a></div>
"""

# --- GROUP 3 SETS PER ROW FOR PRINT LAYOUT ---
rows = []
for i in range(0, len(html_blocks), 3):
    row = "<div style='width:100%; display:flex; flex-direction:row; justify-content:space-between; margin-bottom:10px;'>"
    for j in range(3):
        if i + j < len(html_blocks):
            row += html_blocks[i + j]
    row += "</div>"
    rows.append(row)
final_html = STYLE_BLOCK + print_btn + ''.join(rows)

# --- OUTPUT ---
components.html(final_html, height=min(1800, 400 * ((len(html_blocks)+2)//3)), scrolling=True)
