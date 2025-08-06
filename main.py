
import streamlit as st
import pandas as pd
import plotly.express as px
import ast

# === 1. PAGE CONFIGURATION ===
st.set_page_config(
    page_title="Legal Intake Dashboard",
    page_icon="🧑‍⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Dashboard")

# === 2. LOAD DATA FROM GOOGLE SHEETS (LIVE) ===
cases_url = "https://docs.google.com/spreadsheets/d/1rrxzW09wrNTqw-PNfv_bb3yWop8DX4XLwWFOXMj5vSw/export?format=csv&gid=508184829"
personal_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTdGb0-8t5D17_OHHcgGZ95Is7dYpXmzU2f7_BCdVvkyxq7vOb7W2oVPCm86eD7zVbvkqJWOIIF0_6D/pub?output=csv"

cases = pd.read_csv(cases_url)
personal_df = pd.read_csv(personal_url)

# Helper function: Robust parsing of Cases Id list column
def parse_cases(x):
    if pd.isnull(x) or str(x).strip() == '':
        return []
    try:
        return ast.literal_eval(str(x))
    except Exception:
        return []

# Add parsed 'Cases Id List' column
personal_df["Cases Id List"] = personal_df["Cases Id"].apply(parse_cases)

# Explode for joining
personal_long = personal_df.explode("Cases Id List")
personal_long["Cases Id List"] = personal_long["Cases Id List"].astype(str).str.strip()

# === 3. SIDEBAR FILTERS ===
st.sidebar.header("Filters")
selected_case_type = st.sidebar.selectbox(
    "Filter by Case Type", ["All"] + sorted(cases["Case Type"].unique().tolist())
)
selected_status = st.sidebar.selectbox(
    "Filter by Status", ["All"] + sorted(cases["Case Status"].unique().tolist())
)

# Apply filters
filtered_cases = cases.copy()
if selected_case_type != "All":
    filtered_cases = filtered_cases[filtered_cases["Case Type"] == selected_case_type]
if selected_status != "All":
    filtered_cases = filtered_cases[filtered_cases["Case Status"] == selected_status]
# === 4. SUMMARY METRICS CARDS ===
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Cases", len(filtered_cases))
col2.metric("Open", (filtered_cases["Case Status"] == "Open").sum())
col3.metric("Under Investigation", (filtered_cases["Case Status"] == "Under Investigation").sum())
col4.metric("Unique Clients", personal_df["Name"].nunique())

st.markdown("---")

# === 5. CHARTS SECTION ===
st.subheader("Cases Breakdown")

type_counts = filtered_cases["Case Type"].value_counts()
status_counts = filtered_cases["Case Status"].value_counts()

c1, c2 = st.columns(2)
with c1:
    st.write("**Cases by Type**")
    fig_type = px.pie(
        names=type_counts.index,
        values=type_counts.values,
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    st.plotly_chart(fig_type, use_container_width=True)

with c2:
    st.write("**Cases by Status**")
    fig_status = px.bar(
        x=status_counts.index,
        y=status_counts.values,
        labels={"x": "Status", "y": "Number of Cases"},
        color=status_counts.index,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig_status, use_container_width=True)

st.markdown("---")

# === 6. MERGED TABLE (SHOWING ALL CASES + PERSONAL INFO if available) ===

# Merge so that all cases are shown, with personal details if matched
def parse_cases(x):
    if pd.isnull(x) or x.strip() == '':
        return []
    try:
        return ast.literal_eval(x)
    except Exception:
        return []
personal_df["Cases Id List"] = personal_df["Cases Id"].apply(parse_cases)

personal_exploded = personal_df.explode("Cases Id List")
personal_exploded["Cases Id List"] = personal_exploded["Cases Id List"].astype(str).str.strip()

# Merge—ALL cases shown, regardless of whether matched to person
merged = pd.merge(
    cases,
    personal_exploded,
    left_on="Cases Id",
    right_on="Cases Id List",
    how="left"
)

# Make sure to always display original Cases Id from cases table
display_cols = [
    "Name", "Phone Number", "Address",                  # Personal
    "Case Title", "Case Type", "Case Status", "Case Labels"  # Case info
]
for col in display_cols:
    if col not in merged.columns:
        merged[col] = None  # Guarantee presence

merged["Name"] = merged["Name"].fillna("Unknown")

# Display in Streamlit
st.subheader("Cases (with Personal Info)")
st.dataframe(merged[display_cols].reset_index(drop=True), use_container_width=True)

st.caption("Dashboard auto-updates with live data from Google Sheets.")
