import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime
import shutil

# --- PAGE CONFIG ---
st.set_page_config(page_title="Attendance Dashboard", layout="wide")
st.title("🧾 Attendance Dashboard")

# --- FILE PATHS ---
os.makedirs("data", exist_ok=True)
attendance_file_path = "data/attendance_processed.csv"
holiday_file_path = "data/holidays.csv"

# --- Load Holidays ---
if os.path.exists(holiday_file_path) and os.path.getsize(holiday_file_path) > 0:
    holidays_df = pd.read_csv(holiday_file_path)
    holidays_df['Holiday Date'] = pd.to_datetime(holidays_df['Holiday Date'], errors='coerce')
else:
    holidays_df = pd.DataFrame(columns=["Holiday Date", "Holiday Name", "Year", "Month"])

# --- File Upload (SINGLE FILE ONLY) ---
st.subheader("Step 1: Upload Attendance CSV")
uploaded_file = st.file_uploader("Upload your attendance CSV", type=["csv"])

if uploaded_file:
    with open(attendance_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("✅ CSV uploaded and saved for session")

# --- Load Attendance Data ---
if os.path.exists(attendance_file_path):
    df = pd.read_csv(attendance_file_path)
    df.reset_index(drop=True, inplace=True)
    df.index += 1
    df.index.name = "No."

    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    except:
        st.error("❌ Date format should be DD/MM/YYYY")
        st.stop()

    df['Day'] = df['Date'].dt.day_name()
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name()

    # --- Save/Export/Clear Buttons ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save All Processed Attendance & Summaries"):
            # Already saved at upload, but can re-save to be sure
            df.to_csv(attendance_file_path, index=False)

            # For each employee/year/month, save under data/monthly_summary/year/month/employee_month_year.csv
            employees = sorted(df['Name'].dropna().unique())
            for emp in employees:
                emp_df = df[df['Name'] == emp].copy()
                if emp_df.empty:
                    continue
                emp_df['Work Time'] = emp_df.get('Work Time', '0:00').fillna('0:00')
                emp_df['Clock In'] = emp_df.get('Clock In', '08:00').fillna('08:00').astype(str)
                emp_df['Clock Out'] = emp_df.get('Clock Out', '17:00').fillna('17:00').astype(str)

                def fix_clock_times(row):
                    clock_in = row['Clock In'].strip()
                    clock_out = row['Clock Out'].strip()
                    if clock_in in ["", "nan", "NaN"] and clock_out in ["", "nan", "NaN"]:
                        return pd.Series(["00:00", "00:00"])
                    if clock_in in ["", "nan", "NaN"]:
                        return pd.Series(["08:00", clock_out])
                    if clock_out in ["", "nan", "NaN"]:
                        return pd.Series([clock_in, "17:00"])
                    return pd.Series([clock_in, clock_out])
                emp_df[['Clock In', 'Clock Out']] = emp_df.apply(fix_clock_times, axis=1)

                def time_to_float(tstr):
                    try:
                        h, m = map(int, tstr.split(":"))
                        return round(h + m / 60, 2)
                    except:
                        return 0

                def calc_ot(row):
                    try:
                        out_time = datetime.strptime(row['Clock Out'], "%H:%M")
                        std_out = datetime.strptime("17:00", "%H:%M")
                        if out_time > std_out:
                            overtime_hours = (out_time - std_out).seconds / 3600
                            return round(overtime_hours)
                        return 0
                    except:
                        return 0

                def classify_real_day(att):
                    if att > 6.5:
                        return 1.0
                    elif 0 < att <= 6.5:
                        return 0.5
                    return 0.0

                emp_df['ATT_Time'] = emp_df['Work Time'].apply(time_to_float)
                emp_df['RND(ATT_Time)'] = emp_df['ATT_Time'].round().astype(int)
                emp_df['OT Time'] = emp_df.apply(calc_ot, axis=1)
                emp_df['Real Day'] = emp_df['ATT_Time'].apply(classify_real_day)
                emp_df['Year'] = emp_df['Date'].dt.year
                emp_df['Month'] = emp_df['Date'].dt.month_name()
                summary_cols = ['Date', 'Name', 'Day', 'Work Time', 'Clock In', 'Clock Out', 'Absent', 'ATT_Time',
                                'RND(ATT_Time)', 'OT Time', 'Real Day']
                for (year, month), group in emp_df.groupby(['Year', 'Month']):
                    folder = f"data/monthly_summary/{year}/{month}"
                    os.makedirs(folder, exist_ok=True)
                    emp_filename = f"{emp}_{month}_{year}.csv".replace(" ", "_")
                    group = group.copy()
                    for col in summary_cols:
                        if col not in group.columns:
                            group[col] = ''
                    group[summary_cols].to_csv(os.path.join(folder, emp_filename), index=False)
            st.success("✅ All processed attendance and individual monthly summaries saved for all employees.")

    with col2:
        if st.button("🗑️ Clear Cached Data"):
            # Remove processed attendance file
            if os.path.exists(attendance_file_path):
                os.remove(attendance_file_path)
            # Remove all generated monthly summaries
            monthly_summary_root = "data/monthly_summary"
            if os.path.exists(monthly_summary_root):
                shutil.rmtree(monthly_summary_root)
            st.success("✅ All cached and summary files removed.")
            st.rerun()

    # --- Filters ---
    st.subheader("Step 2: Filter Attendance")
    year = st.selectbox("Select Year", sorted(df['Year'].unique()))
    month = st.selectbox("Select Month", list(calendar.month_name)[1:])
    employee_list = sorted(df['Name'].dropna().unique())
    selected_employee = st.selectbox("Select Employee", employee_list)
    include_sundays = st.checkbox("Include Sundays in table", value=True)

    filtered_df = df[
        (df['Name'] == selected_employee) &
        (df['Year'] == year) &
        (df['Month'] == month)
        ].reset_index(drop=True)

    if not include_sundays:
        filtered_df = filtered_df[filtered_df['Day'] != 'Sunday']

    filtered_df.index += 1
    filtered_df.index.name = "No."
    filtered_df['Date'] = pd.to_datetime(filtered_df['Date'], errors='coerce')

    # Fill missing Work Time if not present
    filtered_df['Work Time'] = filtered_df.get('Work Time', '0:00').fillna('0:00')

    # Format holidays
    filtered_holidays = holidays_df[
        (holidays_df['Year'] == year) & (holidays_df['Month'] == month)
        ]
    holiday_dates_only = [
        pd.to_datetime(d, errors='coerce').date() if not isinstance(d, pd.Timestamp) else d.date()
        for d in filtered_holidays['Holiday Date'].dropna()
    ]

    st.markdown(f"### 📋 Attendance for **{selected_employee}** - {month} {year}")
    if filtered_df.empty:
        st.warning("No attendance records found.")
    else:
        def style_attendance(row):
            date_value = row['Date'].date()
            is_absent = str(row.get('Absent')).strip().lower() == 'true'
            if date_value in holiday_dates_only:
                return ['background-color: yellow'] * len(row)
            elif is_absent:
                return ['background-color: salmon'] * len(row)
            else:
                return ['background-color: lightgreen'] * len(row)


        styled_df = (
            filtered_df.style
            .apply(style_attendance, axis=1)
            .set_properties(**{'font-weight': 'bold', 'color': 'black'})
        )
        st.dataframe(styled_df, use_container_width=True)

        # --- ⏱️ DAILY TIME SUMMARY ---
        st.markdown("### ⏱️ Daily Time Summary")
        summary_df = filtered_df[['Date', 'Day', 'Work Time', 'Clock In', 'Clock Out', 'Absent']].copy()

        # Apply defaults ONLY in this table
        # Set Clock In / Out defaults based on available values
        summary_df['Clock In'] = summary_df['Clock In'].astype(str)
        summary_df['Clock Out'] = summary_df['Clock Out'].astype(str)


        def fix_clock_times(row):
            clock_in = row['Clock In'].strip()
            clock_out = row['Clock Out'].strip()
            if clock_in in ["", "nan", "NaN"] and clock_out in ["", "nan", "NaN"]:
                return pd.Series(["00:00", "00:00"])
            if clock_in in ["", "nan", "NaN"]:
                return pd.Series(["08:00", clock_out])
            if clock_out in ["", "nan", "NaN"]:
                return pd.Series([clock_in, "17:00"])
            return pd.Series([clock_in, clock_out])


        summary_df[['Clock In', 'Clock Out']] = summary_df.apply(fix_clock_times, axis=1)
        summary_df['Work Time'] = summary_df['Work Time'].fillna('0:00')


        def time_to_float(tstr):
            try:
                h, m = map(int, tstr.split(":"))
                return round(h + m / 60, 2)
            except:
                return 0


        def calc_late(row):
            try:
                in_time = datetime.strptime(row['Clock In'], "%H:%M")
                std_in = datetime.strptime("08:00", "%H:%M")
                if in_time > std_in:
                    late_minutes = (in_time - std_in).seconds / 60
                    return round(late_minutes / 60, 2)  # return as decimal hours
                return 0
            except:
                return 0


        def calc_early(row):
            try:
                out_time = row['Clock Out'].strip()
                if out_time in ["0", "00:00"]:
                    return 0
                out_time = datetime.strptime(out_time, "%H:%M")
                std_out = datetime.strptime("17:00", "%H:%M")
                if out_time < std_out:
                    early_minutes = (std_out - out_time).seconds / 60
                    return round(early_minutes / 60, 2)
                return 0
            except:
                return 0


        def calc_ot(row):
            try:
                out_time = datetime.strptime(row['Clock Out'], "%H:%M")
                std_out = datetime.strptime("17:00", "%H:%M")
                if out_time > std_out:
                    overtime_hours = (out_time - std_out).seconds / 3600
                    return round(overtime_hours)  # round to nearest int hour
                return 0
            except:
                return 0


        # Apply conversions
        summary_df['ATT_Time'] = summary_df['Work Time'].apply(time_to_float)
        summary_df['RND(ATT_Time)'] = summary_df['ATT_Time'].round().astype(int)
        summary_df['Late (hr)'] = summary_df.apply(calc_late, axis=1)
        summary_df['Early (hr)'] = summary_df.apply(calc_early, axis=1)
        summary_df['OT Time'] = summary_df.apply(calc_ot, axis=1)


        def classify_real_day(att):
            if att > 6.5:
                return 1.0
            elif 0 < att <= 6.5:
                return 0.5
            return 0.0


        summary_df['Real Day'] = summary_df['RND(ATT_Time)'].apply(classify_real_day)

        display_df = summary_df.drop(columns=["Absent"]).copy()
        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)

        # --- Save All Employees Daily Time Summary (now that year/month is known) ---
        if st.session_state.get('save_daily_summary_clicked', False) or st.session_state.get(
                'save_daily_summary_clicked', None) is None:
            def save_all_employees_summary():
                all_employees = sorted(df['Name'].dropna().unique())
                all_summaries = []
                for emp in all_employees:
                    emp_df = df[
                        (df['Name'] == emp) & (df['Year'] == year) & (df['Month'] == month)
                        ].copy()
                    if emp_df.empty:
                        continue
                    emp_df['Work Time'] = emp_df.get('Work Time', '0:00').fillna('0:00')
                    emp_df['Clock In'] = emp_df['Clock In'].astype(str)
                    emp_df['Clock Out'] = emp_df['Clock Out'].astype(str)

                    emp_df[['Clock In', 'Clock Out']] = emp_df.apply(fix_clock_times, axis=1)
                    emp_df['Work Time'] = emp_df['Work Time'].fillna('0:00')
                    emp_df['ATT_Time'] = emp_df['Work Time'].apply(time_to_float)
                    emp_df['RND(ATT_Time)'] = emp_df['ATT_Time'].round().astype(int)
                    emp_df['OT Time'] = emp_df.apply(calc_ot, axis=1)
                    emp_df['Real Day'] = emp_df['RND(ATT_Time)'].apply(classify_real_day)
                    summary_cols = ['Date', 'Name', 'Day', 'Work Time', 'Clock In', 'Clock Out', 'Absent', 'ATT_Time',
                                    'RND(ATT_Time)', 'OT Time', 'Real Day']
                    emp_summary = emp_df.copy()
                    if 'Name' not in emp_summary.columns:
                        emp_summary['Name'] = emp
                    for col in summary_cols:
                        if col not in emp_summary.columns:
                            emp_summary[col] = ''
                    all_summaries.append(emp_summary[summary_cols])
                if all_summaries:
                    final_summary = pd.concat(all_summaries, ignore_index=True)
                    csv_filename = f"daily_time_summary_{year}_{month}.csv"
                    final_summary.to_csv(csv_filename, index=False)
                    st.success(f"✅ Daily Time Summary for ALL employees saved as {csv_filename}")
                else:
                    st.warning("No attendance data to save for selected month/year.")


            # Actually run if button was pressed
            if st.session_state.get('save_daily_summary_clicked', False):
                save_all_employees_summary()
                st.session_state['save_daily_summary_clicked'] = False

        # --- Summary Totals ---
        month_num = list(calendar.month_name).index(month)
        total_days_in_month = calendar.monthrange(year, month_num)[1]
        all_dates = pd.date_range(start=f"{year}-{month_num:02d}-01", periods=total_days_in_month)
        total_sundays = sum(1 for d in all_dates if d.day_name() == "Sunday")
        total_weekdays = total_days_in_month - total_sundays

        govt_holiday_dates = set(
            pd.to_datetime(filtered_holidays['Holiday Date'], errors='coerce').dt.date.dropna()
        )

        govt_weekday_holidays = sum(
            1 for d in govt_holiday_dates if pd.to_datetime(d).day_name() not in ["Saturday", "Sunday"])
        govt_weekend_holidays = sum(
            1 for d in govt_holiday_dates if pd.to_datetime(d).day_name() in ["Saturday", "Sunday"])

        total_absents = summary_df[
            (summary_df['Absent'].astype(str).str.lower() == 'true') &
            (~summary_df['Date'].dt.date.isin(govt_holiday_dates))
            ].shape[0]

        weekday_full = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 1.0)]
        weekday_half = summary_df[(summary_df['Day'].str.lower() != 'sunday') & (summary_df['Real Day'] == 0.5)]
        sunday_full = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 1.0)]
        sunday_half = summary_df[(summary_df['Day'].str.lower() == 'sunday') & (summary_df['Real Day'] == 0.5)]
        worked_day_count = summary_df[summary_df['Real Day'] > 0].shape[0]

        total_rounded = summary_df['RND(ATT_Time)'].sum()
        total_extra = summary_df['OT Time'].sum()

        st.markdown(f"""
        #### 📊 Monthly Summary:
        - 📅 **Total Days in {month} {year}:** `{total_days_in_month}`
        - 📆 **Total Weekdays:** `{total_weekdays}`
        - 🌞 **Total Sundays:** `{total_sundays}`

        #### ✅ Worked Days Summary:
        - ✅ **Worked Days (Total):** `{worked_day_count}`
          - 🟩 **Worked Weekdays (FULL):** `{len(weekday_full)}`
          - 🟩 **Worked Weekdays (HALF):** `{len(weekday_half)}`
          - 🟦 **Worked Sundays (FULL):** `{len(sunday_full)}`
          - 🟦 **Worked Sundays (HALF):** `{len(sunday_half)}`

        #### 🟨 Government Holidays:
        - 🟨 **Holidays (Govt only) @ weekdays:** `{govt_weekday_holidays}`
        - 🟨 **Holidays (Govt only) @ weekends:** `{govt_weekend_holidays}`

        - ❌ **Absent Days (Excl. Holidays):** `{total_absents}`

        #### 🕒 Time Summary:
        - 🔁 **Total Rounded ATT_Time:** `{total_rounded}` hours  
        - ⏱️ **Total OT Time (After 17:00):** `{total_extra}` hours
        """)

else:
    st.info("📂 Please upload a CSV file to get started.")
