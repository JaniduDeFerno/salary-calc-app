import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta

# --- Page Setup ---
st.set_page_config(page_title="Monthly Deductions")
st.title("📉 Monthly Deductions")

# File paths
os.makedirs("data", exist_ok=True)
deductions_file = "data/monthly_deductions.csv"
attendance_cache_path = "data/attendance_processed.csv"

# Load data
deductions_df = pd.read_csv(deductions_file) if os.path.exists(deductions_file) else pd.DataFrame(columns=[
    "Employee Name", "Year", "Month", "Monthly Advanced", "Monthly Loan Deduction"
])

# Load employee list
if os.path.exists(attendance_cache_path):
    try:
        attendance_df = pd.read_csv(attendance_cache_path)
        employee_names = sorted(attendance_df['Name'].dropna().unique())
        st.success(f"✅ Loaded {len(employee_names)} employee(s).")
    except:
        employee_names = sorted(deductions_df["Employee Name"].dropna().unique())
else:
    employee_names = sorted(deductions_df["Employee Name"].dropna().unique())

# --- Utility: Merge/Upsert Helper ---
def upsert_deduction(df, name, year, month, advance, loan):
    mask = (
        (df["Employee Name"] == name) &
        (df["Year"] == year) &
        (df["Month"] == month)
    )
    if mask.any():
        if advance is not None:
            df.loc[mask, "Monthly Advanced"] = advance
        if loan is not None:
            df.loc[mask, "Monthly Loan Deduction"] = loan
    else:
        new_row = pd.DataFrame([{
            "Employee Name": name,
            "Year": year,
            "Month": month,
            "Monthly Advanced": advance if advance is not None else 0.0,
            "Monthly Loan Deduction": loan if loan is not None else 0.0
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    return df

# --- Deduction Form ---
st.subheader("🧾 Set Monthly Deductions")

if employee_names:
    selected_employee = st.selectbox("Select Employee", employee_names)

    ### --- ADVANCE SECTION ---
    st.markdown("### 💰 Advance")
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        adv_year = st.selectbox("Advance Year", list(range(2020, 2031)), index=date.today().year - 2020, key="adv_year")
    with adv_col2:
        adv_month = st.selectbox("Advance Month", list(calendar.month_name)[1:], index=date.today().month - 1, key="adv_month")

    # Get existing advance for this employee/month
    existing_adv = deductions_df[
        (deductions_df["Employee Name"] == selected_employee) &
        (deductions_df["Year"] == adv_year) &
        (deductions_df["Month"] == adv_month)
    ]
    adv_val = float(existing_adv["Monthly Advanced"].values[0]) if not existing_adv.empty else 0.0
    curr_loan = float(existing_adv["Monthly Loan Deduction"].values[0]) if not existing_adv.empty else 0.0
    advance_amount = st.number_input("Monthly Advanced", min_value=0.0, value=adv_val, key="advance_input")

    if st.button("💾 Save Advance"):
        deductions_df = upsert_deduction(
            deductions_df,
            selected_employee, adv_year, adv_month,
            advance_amount,
            curr_loan  # keep loan as is
        )
        deductions_df.to_csv(deductions_file, index=False)
        st.success(f"✅ Saved advance for {selected_employee} in {adv_month} {adv_year}.")

    st.divider()

    ### --- LOAN SECTION ---
    st.markdown("### 🏦 Loan")

    # Get existing loan (for prefill, optional)
    loan_val = 0.0
    if not deductions_df.empty:
        existing_loan = deductions_df[
            (deductions_df["Employee Name"] == selected_employee) &
            (deductions_df["Monthly Loan Deduction"] > 0)
        ]
        if not existing_loan.empty:
            loan_val = float(existing_loan["Monthly Loan Deduction"].values[0])

    loan_amount = st.number_input("Monthly Loan Deduction", min_value=0.0, value=loan_val, key="loan_input")

    # Start/End Month as before
    start_month = st.date_input(
        "Loan Start Month",
        value=date.today().replace(day=1),
        min_value=date(2020, 1, 1),
        key="loan_start"
    )
    end_month = st.date_input(
        "Loan End Month",
        value=date.today().replace(day=1),
        min_value=start_month,
        key="loan_end"
    )
    start_month = start_month.replace(day=1)
    end_month = end_month.replace(day=1)
    loan_duration = (end_month.year - start_month.year) * 12 + (end_month.month - start_month.month) + 1
    st.info(f"Loan Duration: **{loan_duration} month(s)**")

    if st.button("💾 Save Loan"):
        for i in range(loan_duration):
            entry_date = start_month + relativedelta(months=i)
            year = entry_date.year
            month = calendar.month_name[entry_date.month]
            # Get any current advance for this month (to preserve both)
            exist_row = deductions_df[
                (deductions_df["Employee Name"] == selected_employee) &
                (deductions_df["Year"] == year) &
                (deductions_df["Month"] == month)
            ]
            curr_advance = float(exist_row["Monthly Advanced"].values[0]) if not exist_row.empty else 0.0
            deductions_df = upsert_deduction(
                deductions_df,
                selected_employee, year, month,
                curr_advance,
                loan_amount
            )
        deductions_df.to_csv(deductions_file, index=False)
        st.success(
            f"✅ Saved loan deduction(s) for {selected_employee} from {start_month.strftime('%B %Y')} to {end_month.strftime('%B %Y')}."
        )

# --- Summary Table with Filtering ---
if not deductions_df.empty:
    st.subheader("📊 Deduction Summary")

    # Employee filter
    employee_options = ["All"] + sorted(deductions_df["Employee Name"].dropna().unique())
    filter_employee = st.selectbox("👤 Filter Employee", employee_options)

    filter_year = st.selectbox("📆 Filter Year", sorted(deductions_df["Year"].dropna().unique()), index=0)
    months = ["All"] + list(calendar.month_name)[1:]
    filter_month = st.selectbox("🗓️ Filter Month", months)

    # Apply filters
    filtered = deductions_df[deductions_df["Year"] == filter_year]
    if filter_month != "All":
        filtered = filtered[filtered["Month"] == filter_month]
    if filter_employee != "All":
        filtered = filtered[filtered["Employee Name"] == filter_employee]

    if not filtered.empty:
        st.dataframe(
            filtered.sort_values(by=["Employee Name", "Year", "Month"]),
            use_container_width=True
        )

        # --- THEME-FRIENDLY DEDUCTION TOTALS SUMMARY ---
        total_advance = filtered["Monthly Advanced"].sum()
        total_loan = filtered["Monthly Loan Deduction"].sum()

        st.markdown("#### 🧾 Deduction Totals (Filtered Data)")
        st.info(
            f"**Total Advance:** Rs. {total_advance:,.2f}\n\n"
            f"**Total Loan Deduction:** Rs. {total_loan:,.2f}"
        )

    else:
        st.info("ℹ️ No deductions found for selected period.")
else:
    st.info("ℹ️ No deduction records available.")
