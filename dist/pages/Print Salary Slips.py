import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import calendar
from datetime import date, datetime

# --- Page Setup ---
st.set_page_config(page_title="Print Salary Slips", layout="wide")
st.title("🖨️ Print Salary Slips")

# --- File Paths ---
employee_file = "data/employee_data.csv"
deduction_file = "data/monthly_deductions.csv"
summary_root_folder = "data/monthly_summary"
holiday_file = "data/holidays.csv"

# --- Load Data ---
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
employee_list = sorted(employee_df["Employee Name"].dropna().unique())
selected_employee = st.selectbox("Select Employee", employee_list)

col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox("Year", list(range(2020, date.today().year + 1)), index=date.today().year - 2020)
with col2:
    selected_month = st.selectbox("Month", list(calendar.month_name)[1:], index=date.today().month - 1)

format_option = st.radio("Select Format", ["1st", "2nd", "Both"])

# --- Load Summary File ---
month_num = list(calendar.month_name).index(selected_month)
summary_file = f"{summary_root_folder}/{selected_year}/{selected_month}/{selected_employee}_{selected_month}_{selected_year}.csv"

if not os.path.exists(summary_file):
    st.warning("⚠️ Salary summary not found. Please export it from 'Attendance Dashboard'.")
    st.stop()

summary_df = pd.read_csv(summary_file, parse_dates=["Date"])
summary_df['Day'] = summary_df['Day'].astype(str)

# --- Attendance Time Parsing ---
def time_to_float(tstr):
    try:
        h, m = map(int, str(tstr).split(":"))
        return round(h + m / 60, 2)
    except:
        return 0

if 'ATT_Time' not in summary_df.columns and 'Work Time' in summary_df.columns:
    summary_df['ATT_Time'] = summary_df['Work Time'].apply(time_to_float)

if 'RND(ATT_Time)' not in summary_df.columns:
    summary_df['RND(ATT_Time)'] = summary_df['ATT_Time'].round().astype(int)

# --- Real Day Classification ---
def classify_real_day(att):
    if att > 6.5:
        return 1.0
    elif 0 < att <= 6.5:
        return 0.5
    return 0.0

summary_df['Real Day'] = summary_df['RND(ATT_Time)'].apply(classify_real_day)

# --- Overtime Calculation ---
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

# --- Breakdown by day type ---
weekday_full = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 1.0)]
weekday_half = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 0.5)]
sunday_full = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 1.0)]
sunday_half = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 0.5)]

weekday_overtime = summary_df[summary_df['Day'].str.lower() != 'sunday']['OT Time'].sum()

# --- Government Holidays ---
filtered_holidays = holidays_df[
    (holidays_df['Year'] == selected_year) & (holidays_df['Month'] == selected_month)
]
govt_holiday_dates = set(filtered_holidays['Holiday Date'].dt.date.dropna())

# --- Absences excluding holidays ---
summary_df['Date'] = pd.to_datetime(summary_df['Date'], errors='coerce')
absents = summary_df[
    (summary_df.get('Absent', '').astype(str).str.lower() == 'true') &
    (~summary_df['Date'].dt.date.isin(govt_holiday_dates))
]
total_absents = len(absents)

# --- Employee Info ---
emp_data = employee_df[employee_df["Employee Name"] == selected_employee]
basic_salary = emp_data["Basic Salary"].values[0]
bra = emp_data["BRA"].values[0]
salary_for_epf = emp_data["Salary for EPF"].values[0]
normal_rate = emp_data["Normal Pay Rate"].values[0]
sunday_rate = emp_data["Sunday Pay Rate"].values[0]
bonus_raw = emp_data["Attendance Bonus"].values[0]
other_allow = emp_data["Other Allowances"].values[0]
meal = emp_data["Meal Allowance"].values[0]
overtime_hourly = emp_data["Overtime Pay Hourly Rate"].values[0]
epf_no = emp_data["EPF No"].values[0] if "EPF No" in emp_data else "N/A"

# --- EPF/ETF Calculation (using Salary for EPF) ---
epf_8 = round(salary_for_epf * 0.08, 2)
epf_12 = round(salary_for_epf * 0.12, 2)
etf_3 = round(salary_for_epf * 0.03, 2)

# --- Bonus Threshold ---
total_days = calendar.monthrange(selected_year, month_num)[1]
all_dates = pd.date_range(f"{selected_year}-{month_num:02d}-01", periods=total_days)
total_sundays = sum(1 for d in all_dates if d.day_name() == "Sunday")
total_weekdays = total_days - total_sundays
govt_weekday_holidays = sum(1 for d in govt_holiday_dates if pd.to_datetime(d).day_name() not in ["Saturday", "Sunday"])
bonus_threshold = total_weekdays - govt_weekday_holidays - 2
bonus = bonus_raw if len(weekday_full) >= bonus_threshold else 0

# --- Deductions ---
emp_deductions = deduction_df[
    (deduction_df["Employee Name"] == selected_employee) &
    (deduction_df["Year"] == selected_year) &
    (deduction_df["Month"] == selected_month)
]
monthly_advance = emp_deductions["Monthly Advanced"].values[0] if not emp_deductions.empty else 0
monthly_loan = emp_deductions["Monthly Loan Deduction"].values[0] if not emp_deductions.empty else 0

# --- Salary Calculation ---
full_days = len(weekday_full)
half_days = len(weekday_half)
base_salary = (full_days * normal_rate) + (half_days * normal_rate / 2)
sunday_pay = (len(sunday_full) * sunday_rate) + (len(sunday_half) * sunday_rate / 2)
ot_pay = weekday_overtime * overtime_hourly

gross = base_salary + ot_pay + sunday_pay + bonus + other_allow + meal
net = gross - monthly_advance - monthly_loan - epf_8

# --- Monthly Summary Calculation ---
month_num = list(calendar.month_name).index(selected_month)
total_days_in_month = calendar.monthrange(selected_year, month_num)[1]
all_dates = pd.date_range(start=f"{selected_year}-{month_num:02d}-01", periods=total_days_in_month)
total_sundays = sum(1 for d in all_dates if d.day_name() == "Sunday")
total_weekdays = total_days_in_month - total_sundays

filtered_holidays = holidays_df[
    (holidays_df['Year'] == selected_year) & (holidays_df['Month'] == selected_month)
]
govt_holiday_dates = set(filtered_holidays['Holiday Date'].dt.date.dropna())
govt_weekday_holidays = sum(1 for d in govt_holiday_dates if pd.to_datetime(d).day_name() not in ["Saturday", "Sunday"])
govt_weekend_holidays = sum(1 for d in govt_holiday_dates if pd.to_datetime(d).day_name() in ["Saturday", "Sunday"])

absents = summary_df[
    (summary_df.get('Absent', '').astype(str).str.lower() == 'true') &
    (~summary_df['Date'].dt.date.isin(govt_holiday_dates))
]
total_absents = len(absents)

worked_total = summary_df[summary_df['Real Day'] > 0].shape[0]
weekday_full = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 1.0)]
weekday_half = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 0.5)]
sunday_full = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 1.0)]
sunday_half = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 0.5)]

total_att_time = summary_df['RND(ATT_Time)'].sum()
total_ot_time = summary_df[summary_df['Day'].str.lower() != 'sunday']['OT Time'].sum()

# --- Status ---
st.success("📅 Salary details loaded and calculated successfully.")

def render_salary_slip():
    # For consistency, use the actual values for display
    style = """
        <style>
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
            @media print {
                .print-button { display: none; }
            }
        </style>
        """

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

    html = style
    if format_option in ["1st", "Both"]:
        html += format1
    if format_option in ["2nd", "Both"]:
        html += format2

    html += """
        <div class='print-button'>
            <a href="javascript:window.print()" style="
                display: inline-block;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #4CAF50;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 10px;
            ">🖨️ Print</a>
        </div>
        """
    return html

st.markdown(f"""
    ### 📊 Monthly Summary:
    📅 **Total Days in {selected_month} {selected_year}:** `{total_days_in_month}`  
    📆 **Total Weekdays:** `{total_weekdays}`  
    🌞 **Total Sundays:** `{total_sundays}`

    #### ✅ Worked Days Summary:
    ✅ **Worked Days (Total):** `{worked_total}`  
    🟩 **Worked Weekdays (FULL):** `{len(weekday_full)}`  
    🟩 **Worked Weekdays (HALF):** `{len(weekday_half)}`  
    🟦 **Worked Sundays (FULL):** `{len(sunday_full)}`  
    🟦 **Worked Sundays (HALF):** `{len(sunday_half)}`

    #### 🟨 Government Holidays:
    🟨 **Holidays (Govt only) @ weekdays:** `{govt_weekday_holidays}`  
    🟨 **Holidays (Govt only) @ weekends:** `{govt_weekend_holidays}`

    ❌ **Absent Days (Excl. Holidays):** `{total_absents}`

    #### 🕒 Time Summary:
    🔁 **Total Rounded ATT_Time:** `{total_att_time}` hours  
    ⏱️ **Total OT Time (After 17:00):** `{total_ot_time}` hours
    """)
# --- Render Output ---
components.html(render_salary_slip(), height=1300)
