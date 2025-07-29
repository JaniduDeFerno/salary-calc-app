import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date

# Setup
st.set_page_config(page_title="Manage Holidays")
st.title("📅 Manage Holidays")

# Paths
os.makedirs("data", exist_ok=True)
holiday_file_path = "data/holidays.csv"

# Load holiday data
if os.path.exists(holiday_file_path) and os.path.getsize(holiday_file_path) > 0:
    holidays_df = pd.read_csv(holiday_file_path, parse_dates=["Holiday Date"])
else:
    holidays_df = pd.DataFrame(columns=["Holiday Date", "Holiday Name", "Year", "Month"])

# --- Add New Holiday ---
st.subheader("➕ Add New Holiday")

col1, col2 = st.columns(2)
with col1:
    new_date = st.date_input("Holiday Date")
with col2:
    new_name = st.text_input("Holiday Name")

if st.button("Add Holiday"):
    new_entry = pd.DataFrame([{
        "Holiday Date": pd.to_datetime(new_date),
        "Holiday Name": new_name,
        "Year": new_date.year,
        "Month": calendar.month_name[new_date.month]
    }])
    holidays_df = pd.concat([holidays_df, new_entry], ignore_index=True).drop_duplicates(subset=["Holiday Date"])
    holidays_df.sort_values("Holiday Date", inplace=True)
    holidays_df.to_csv(holiday_file_path, index=False)
    st.success(f"✅ Holiday added: {new_name} on {new_date.strftime('%Y-%m-%d')}")

# --- Manage Existing Holidays ---
st.subheader("📝 Edit Holidays")

if holidays_df.empty:
    st.info("No holidays saved yet.")
else:
    editable_df = holidays_df.copy()
    editable_df["Holiday Date"] = pd.to_datetime(editable_df["Holiday Date"], errors="coerce")
    editable_df["Day of Week"] = editable_df["Holiday Date"].dt.day_name()
    editable_df["Holiday Date"] = editable_df["Holiday Date"].dt.strftime("%Y-%m-%d")

    # Show day of week in the data editor (read-only for user)
    updated_df = st.data_editor(
        editable_df[["Holiday Date", "Day of Week", "Holiday Name"]],
        num_rows="dynamic",
        use_container_width=True,
        key="holiday_editor"
    )

    if st.button("💾 Save Changes"):
        updated_df["Holiday Date"] = pd.to_datetime(updated_df["Holiday Date"], errors='coerce')
        updated_df["Year"] = updated_df["Holiday Date"].dt.year
        updated_df["Month"] = updated_df["Holiday Date"].dt.month_name()
        # Drop the Day of Week column before saving
        updated_df = updated_df.drop(columns=["Day of Week"])
        updated_df.drop_duplicates(subset=["Holiday Date"], inplace=True)
        updated_df.to_csv(holiday_file_path, index=False)
        st.success("✅ Holidays updated successfully.")

    st.divider()
    st.subheader("❌ Delete Holiday")

    for index, row in holidays_df.iterrows():
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.write(f"📅 {row['Holiday Date'].strftime('%Y-%m-%d')}")
        with col2:
            st.write(f"🏷️ {row['Holiday Name']}")
        with col3:
            if st.button("Delete", key=f"del_{index}"):
                holidays_df = holidays_df.drop(index)
                holidays_df.to_csv(holiday_file_path, index=False)
                st.success(f"🗑️ Deleted holiday on {row['Holiday Date'].strftime('%Y-%m-%d')}")
                st.rerun()
