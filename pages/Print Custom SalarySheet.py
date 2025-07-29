import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Custom Salary Slips", layout="wide")
st.title("📝 Custom Salary Slips (Manual Entry)")

if "custom_sheets" not in st.session_state:
    st.session_state.custom_sheets = []

with st.form("salary_entry"):
    st.subheader("Enter Employee Salary Details")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Employee Name", "")
        designation = st.text_input("Designation/Type", "")
        epf_no = st.text_input("EPF No (optional)", "")
    with col2:
        basic_salary = st.number_input("Basic Salary", min_value=0.0, value=0.0)
        bra = st.number_input("BRA", min_value=0.0, value=0.0)
        salary_for_epf = basic_salary + bra
        normal_rate = st.number_input("Normal Pay Rate (for info only)", min_value=0.0, value=0.0)
        overtime_hourly = st.number_input("Overtime Pay Hourly Rate (for info only)", min_value=0.0, value=0.0)
        sunday_rate = st.number_input("Sunday Pay Rate (for info only)", min_value=0.0, value=0.0)
        attendance_bonus = st.number_input("Attendance Bonus", min_value=0.0, value=0.0)
        other_allow = st.number_input("Other Allowances", min_value=0.0, value=0.0)
        meal = st.number_input("Meal Allowance", min_value=0.0, value=0.0)

    bonus = attendance_bonus
    advance = st.number_input("Advance", min_value=0.0, value=0.0)
    loan = st.number_input("Loan Deduction", min_value=0.0, value=0.0)

    epf_8 = round(salary_for_epf * 0.08, 2)
    epf_12 = round(salary_for_epf * 0.12, 2)
    etf_3 = round(salary_for_epf * 0.03, 2)

    submitted = st.form_submit_button("Add Salary Sheet")

    if submitted and name:
        st.session_state.custom_sheets.append({
            "name": name,
            "designation": designation,
            "epf_no": epf_no,
            "basic_salary": basic_salary,
            "bra": bra,
            "salary_for_epf": salary_for_epf,
            "normal_rate": normal_rate,
            "overtime_hourly": overtime_hourly,
            "sunday_rate": sunday_rate,
            "attendance_bonus": attendance_bonus,
            "other_allow": other_allow,
            "meal": meal,
            "bonus": bonus,
            "advance": advance,
            "loan": loan,
            "epf_8": epf_8,
            "epf_12": epf_12,
            "etf_3": etf_3,
        })
        st.success(f"Added salary sheet for {name}!")
        st.rerun()

# --- DELETE INDIVIDUAL ENTRIES ---
if st.session_state.custom_sheets:
    st.markdown("### Entries:")
    for i, emp in enumerate(st.session_state.custom_sheets):
        st.markdown(f"- {emp['name']} ({emp['designation']})")
        if st.button(f"❌ Remove {emp['name']}", key=f"del_{i}"):
            st.session_state.custom_sheets.pop(i)
            st.st.rerun()
()

# --- HTML RENDER (exact same structure as your Print Salary Slips) ---
def render_salary_slip(emp):
    # For manual entry, no attendance stats, so all are zeroed for display
    full_days = 0
    half_days = 0
    sunday_full = 0
    sunday_half = 0
    weekday_overtime = 0
    ot_pay = 0
    sunday_pay = 0
    base_salary = emp["salary_for_epf"]  # Show as Salary for EPF for manual sheets
    bonus = emp["bonus"]
    other_allow = emp["other_allow"]
    meal = emp["meal"]
    gross = base_salary + bonus + other_allow + meal
    monthly_advance = emp["advance"]
    monthly_loan = emp["loan"]
    epf_8 = emp["epf_8"]
    epf_12 = emp["epf_12"]
    etf_3 = emp["etf_3"]
    net = gross - monthly_advance - monthly_loan - epf_8

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
                border-top: 1px dotted #888 !important;
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
                <tr><td><strong>Employee</strong></td><td align='right'><strong>{emp['name']}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>Salary per Day</td><td align='right'>{emp['normal_rate']:,.2f}</td></tr>
                <tr><td>Full Days</td><td align='right'>{full_days}</td></tr>
                <tr><td>Half Days</td><td align='right'>{half_days}</td></tr>
            </table>
            <hr>
            <table>
                <tr><td><strong>Base Salary</strong></td><td align='right'><strong>{base_salary:,.2f}</strong></td></tr>
                <tr><td>OT ({weekday_overtime:.2f} × {emp['overtime_hourly']})</td><td align='right'>{ot_pay:,.2f}</td></tr>
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
                <tr><td><strong>Employee</strong></td><td align='right'><strong>{emp['name']}</strong></td></tr>
                <tr><td>Designation</td><td align='right'>{emp['designation']}</td></tr>
                <tr><td>EPF No:</td><td align='right'><b>{emp['epf_no']}</b></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>Basic Salary</td><td align='right'>{emp['basic_salary']:,.2f}</td></tr>
                <tr><td>BRA</td><td align='right'>{emp['bra']:,.2f}</td></tr>
            </table>
            <hr style="border-top: 1px dashed #888;">
            <table>
                <tr><td><strong>Salary For EPF</strong></td><td align='right'><strong>{emp['salary_for_epf']:,.2f}</strong></td></tr>
            </table>
            <hr>
            <table>
                <tr><td>OT ({weekday_overtime:.2f} × {emp['overtime_hourly']})</td><td align='right'>{ot_pay:,.2f}</td></tr>
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
    return style + f"""
        <div style="display:flex; flex-direction:row; gap:20px; margin-bottom:30px;">
            {format1}{format2}
        </div>
    """

# --- PRINT ALL SHEETS TOGETHER ---
if st.session_state.custom_sheets:
    st.markdown("## 🖨️ Custom Salary Slips")
    slips_html = ''.join([render_salary_slip(emp) for emp in st.session_state.custom_sheets])
    slips_html += """
    <div class='print-button' style='margin-bottom:20px;'>
        <a href="javascript:window.print()" style="padding:8px 20px; background:#28a745; color:white; text-decoration:none; border-radius:4px; font-size:16px;">🖨️ Print All</a>
    </div>
    """
    components.html(slips_html, height=700 + len(st.session_state.custom_sheets)*340, scrolling=True)
