import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import folium_static

st.set_page_config(page_title="AQI India", page_icon="🌍", layout="wide")

# ----- Load dataset with caching -----
@st.cache_data
def load_data():
    df = pd.read_csv("AQI.csv")
    df['last_update'] = pd.to_datetime(df['last_update'])

    # AQI Category Labels
    def aqi_category(value):
        if value <= 50:
            return "🟢 Good"
        elif value <= 100:
            return "🟡 Moderate"
        elif value <= 150:
            return "🟠 Unhealthy (Sensitive)"
        elif value <= 200:
            return "🔴 Unhealthy"
        else:
            return "☠️ Hazardous"

    df["AQI_Category"] = df["pollutant_avg"].apply(aqi_category)
    return df


df = load_data()
filtered_df = df.copy()

# ----- Sidebar Navigation -----
st.sidebar.image('Logo.png', use_container_width=True)
st.sidebar.title("🔍 Navigation")
section = st.sidebar.radio("Go to:", ["Main Overview", "Statistical Overview", "Visual Overview", "Geographical Overview", "Download & Reports"])

# ----- AQI Alert System -----
if df["pollutant_avg"].max() > 200:
    st.error("🚨 High pollution levels detected! Consider wearing a mask outdoors.")

# ----- MAIN OVERVIEW -----
if section == "Main Overview":
    st.title("📊 Air Quality Index (AQI) Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Dataset Overview")
        st.dataframe(df.head())

    with col2:
        st.write("### Dataset Summary")
        st.write(df.describe())

    # Missing Values
    st.write("### ❗ Missing Values")
    missing_values = df.isnull().sum().reset_index()
    missing_values.columns = ["Column", "Missing Values"]
    fig = px.bar(missing_values, x="Column", y="Missing Values", title="Missing Values Count")
    st.plotly_chart(fig)

    # AQI Category Distribution
    st.write("### 🌍 AQI Category Distribution")
    category_counts = df["AQI_Category"].value_counts().reset_index()
    category_counts.columns = ["AQI_Category", "Count"]
    fig = px.bar(category_counts, x="AQI_Category", y="Count", color="AQI_Category",
                 title="Number of Locations per AQI Category")
    st.plotly_chart(fig)

    # Key Stats
    st.write(f"**Total Cities:** {df['city'].nunique()} | **Total Stations:** {df['station'].nunique()}")

# ----- STATISTICAL OVERVIEW -----
elif section == "Statistical Overview":
    st.title("📈 Statistical Analysis")

    # Correlation Heatmap
    st.write("### 🔥 Correlation Between Pollutant Levels")
    corr_matrix = df[['pollutant_min', 'pollutant_max', 'pollutant_avg']].corr()
    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r",
                    title="Correlation Heatmap")
    st.plotly_chart(fig)

    # State-wise Average Pollution
    st.write("### 🌍 State-wise Average Pollution Levels")
    state_avg = df.groupby('state')['pollutant_avg'].mean().sort_values(ascending=False).reset_index()
    fig = px.bar(state_avg, x="pollutant_avg", y="state", orientation='h',
                 title="State-wise Average Pollution Levels", color="pollutant_avg", color_continuous_scale="reds")
    st.plotly_chart(fig)
    st.markdown("<h6 style='text-align: center;'>- Odisha is the most polluted state.</h6>", unsafe_allow_html=True)

    # Top 5 Cleanest Cities
    st.write("### 🌱 Top 5 Cleanest Cities")
    cleanest_cities = df.groupby("city")["pollutant_avg"].mean().sort_values().head(5).reset_index()
    fig = px.bar(cleanest_cities, x="pollutant_avg", y="city", orientation='h',
                 title="Top 5 Cleanest Cities", color="pollutant_avg", color_continuous_scale="greens")
    st.plotly_chart(fig)
    st.markdown("<h6 style='text-align: center;'>- Hassan is the cleanest city.</h6>", unsafe_allow_html=True)

# ----- VISUAL OVERVIEW -----
elif section == "Visual Overview":
    st.title("📊 Detailed Visualizations")

    filter_option = st.radio("Filter data by:", ["State", "City"])
    selected = st.multiselect(f"Select {filter_option}(s):", df[filter_option.lower()].unique(),
                              placeholder="Search...")

    if selected:
        filtered_df = df[df[filter_option.lower()].isin(selected)]

    # Boxplot with Outlier Toggle
    st.write("### 📦 Distribution of Pollutant Levels")
    show_outliers = st.checkbox("Show Outliers in Boxplot")
    fig = px.box(filtered_df, y=["pollutant_min", "pollutant_max", "pollutant_avg"],
                 points="all" if show_outliers else False,
                 title=f"Pollutant Level Distribution ({', '.join(selected) if selected else 'All'})")
    st.plotly_chart(fig)
    st.markdown("<h6 style='text-align: center;'>- The box plot represents the max, min, and median AQI values. There is a huge deviation in the max AQI, meaning pollution levels are at a peak right now.</h6>", unsafe_allow_html=True)

    # Pollutant Frequency Distribution
    st.write("### 🔬 Pollutant Type Distribution")
    fig = px.histogram(filtered_df, x="pollutant_id", color="pollutant_id",
                       title="Pollutant Type Distribution", text_auto=True)
    st.plotly_chart(fig)
    st.markdown("<h6 style='text-align: center;'>- OZONE causes the most pollution in India.</h6>", unsafe_allow_html=True)

# ----- GEOGRAPHICAL OVERVIEW -----
elif section == "Geographical Overview":
    st.title("🌍 Geographical Analysis")

    st.write("### 🔥 Air Quality Heatmap")
    m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=5)

    heat_data = df[['latitude', 'longitude', 'pollutant_avg']].dropna().values.tolist()
    HeatMap(heat_data).add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        aqi_label = f"<b>{row['AQI_Category']}</b>"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"<b>Station: {row['station']}</b><br>AQI: {row['pollutant_avg']}<br>{aqi_label}",
            icon=folium.Icon(color="red"),
        ).add_to(marker_cluster)

    folium_static(m)

# ----- DOWNLOAD & REPORTS -----
elif section == "Download & Reports":
    st.title("📄 Download & Reports")

    st.write("### 📥 Download Filtered Data")
    selected_columns = st.multiselect("Select Columns to Download:", df.columns, default=df.columns.tolist())
    csv = filtered_df[selected_columns].to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "AQI_filtered_data.csv", "text/csv")

    st.write("### 📄 Download Full AQI Report")
    pdf_path = "Air_Quality_Report.pdf"

    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    st.download_button(
        label="📥 Download Full Report (PDF)",
        data=pdf_bytes,
        file_name="Air_Quality_Report.pdf",
        mime="application/pdf",
    )

# ----- Feedback Form -----
st.sidebar.write("💬 **Feedback**")
feedback = st.sidebar.text_area("Let us know your thoughts!")
if st.sidebar.button("Submit Feedback"):
    st.sidebar.success("Thank you for your feedback! 😊")
