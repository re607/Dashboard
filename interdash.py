import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from streamlit_plotly_events import plotly_events

# Set the page layout to wide by default
st.set_page_config(layout="wide")

# Load and convert the XLSX data to DataFrame
@st.cache_data(ttl=1800)  # Cache the data for 30 minutes
def load_data():
    # Check the current working directory for debugging
    st.write("Current Working Directory:", os.getcwd())

    file_path = "Strava_All_ActivitiesNew.xlsx"  # File is in the same directory
    data = pd.read_excel(file_path)
    return data

# Streamlit dashboard
st.title("Strava Activities Dashboard")

# Load and display data
data = load_data()

# Convert 'Start Date' column to datetime and handle errors (invalid parsing) by coercing them to NaT
data['Start Date'] = pd.to_datetime(data['Start Date'], errors='coerce')

# Ensure 'Start Date' is normalized (date without time component)
data['Start Date'] = data['Start Date'].dt.normalize()

today = pd.to_datetime('today').normalize()
last_12_weeks_data = data[data['Start Date'] >= today - pd.Timedelta(weeks=12)]

last_12_weeks_data['Week'] = last_12_weeks_data['Start Date'].dt.to_period('W')
last_12_weeks_data['Moving Time (min)'] = pd.to_numeric(last_12_weeks_data['Moving Time (min)'], errors='coerce')
last_12_weeks_data['Distance (km)'] = pd.to_numeric(last_12_weeks_data['Distance (km)'], errors='coerce')

last_12_weeks_data = last_12_weeks_data.dropna(subset=['Moving Time (min)', 'Distance (km)'])

col1, col2 = st.columns([1, 2])

with col1:
    st.write("### Recent Activities")
    for index, row in data.head(10).iterrows():
        activity_name = row['Name']
        activity_type = row['Type']
        activity_distance = f"{row['Distance (km)']:.2f} km"
        activity_time = f"{row['Moving Time (min)']:.0f} min"
        activity_elevation = f"{row['Total Elevation Gain (m)']} m"
        activity_date = pd.to_datetime(row['Start Date']).strftime('%d/%m/%y')

        activity_details = f"{activity_name} - {activity_type} {activity_distance} {activity_time} {activity_elevation} {activity_date}"

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; background-color: #f0f0f0; border-radius: 10px; padding: 15px; margin-bottom: 15px;">
                <div style="flex: 1; font-size: 14px; font-weight: bold; padding-right: 10px;">{activity_name}</div>
                <div style="font-size: 14px; padding-right: 10px;">{activity_type}</div>
                <div style="font-size: 14px; padding-right: 10px;">{activity_distance}</div>
                <div style="font-size: 14px; padding-right: 10px;">{activity_time}</div>
                <div style="font-size: 14px; padding-right: 10px;">{activity_elevation}</div>
                <div style="font-size: 14px;">{activity_date}</div>
            </div>
            """, unsafe_allow_html=True)

with col2:
    st.markdown("<h3 style='text-align: left;'>Select Sport</h3>", unsafe_allow_html=True)

    activity_filter = st.selectbox("Select Activity Type:", ["All", "Cycling", "Run"])

    if activity_filter == "Cycling":
        last_12_weeks_data = last_12_weeks_data[last_12_weeks_data['Type'].isin(['Ride', 'Virtual Ride'])]
    elif activity_filter == "Run":
        last_12_weeks_data = last_12_weeks_data[last_12_weeks_data['Type'] == 'Run']

    data_type_filter = st.selectbox("Select Data Type:", ["Moving Time", "Distance"])

    weekly_data = last_12_weeks_data.groupby('Week').agg({
        'Moving Time (min)': 'sum',
        'Total Elevation Gain (m)': 'sum',
        'Distance (km)': 'sum'
    }).reset_index()

    weekly_data['Week'] = weekly_data['Week'].apply(lambda x: f"{x.start_time.day:02}/{x.start_time.month:02}")

    # Displaying the information with time in hours (XX.XX hours format) and bold pattern for all three columns
    time_in_hours = weekly_data['Moving Time (min)'] / 60
    distance = weekly_data['Distance (km)']
    elevation = weekly_data['Total Elevation Gain (m)']

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; font-size: 16px; padding: 10px;">
        <div style="flex: 1; text-align: center;">
            <strong>Moving Time:</strong> <span style="font-weight: normal;">{time_in_hours.max():.2f} hours</span>
        </div>
        <div style="flex: 1; text-align: center;">
            <strong>Distance:</strong> <span style="font-weight: normal;">{distance.max():.2f} km</span>
        </div>
        <div style="flex: 1; text-align: center;">
            <strong>Elevation:</strong> <span style="font-weight: normal;">{elevation.max()} m</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    fig = go.Figure()

    if data_type_filter == "Moving Time":
        fig.add_trace(go.Scatter(
            x=weekly_data['Week'],
            y=weekly_data['Moving Time (min)'],
            mode='lines+markers',
            line=dict(color="#FC5200", width=3),
            marker=dict(size=8, color="#FC5200"),
            name="Moving Time"
        ))
        yaxis_title = "Moving Time"
        yaxis_tickvals = list(range(0, int(weekly_data['Moving Time (min)'].max()) + 60, 60))
        yaxis_ticktext = [f'{x / 60:.1f}' for x in yaxis_tickvals]
        fillcolor = 'rgba(252, 82, 0, 0.2)'
        line_color = "#FC5200"
    else:
        fig.add_trace(go.Scatter(
            x=weekly_data['Week'],
            y=weekly_data['Distance (km)'],
            mode='lines+markers',
            line=dict(color="#00A9F1", width=3),
            marker=dict(size=8, color="#00A9F1"),
            name="Distance"
        ))
        yaxis_title = "Distance"
        yaxis_tickvals = list(range(0, int(weekly_data['Distance (km)'].max()) + 1, 1))
        yaxis_ticktext = [f'{x:.1f}' for x in yaxis_tickvals]
        fillcolor = 'rgba(0, 169, 241, 0.2)'
        line_color = "#00A9F1"

    for i, value in enumerate(weekly_data[data_type_filter == "Moving Time" and 'Moving Time (min)' or 'Distance (km)']):
        fig.add_shape(
            type="line",
            x0=weekly_data['Week'][i], 
            x1=weekly_data['Week'][i], 
            y0=0, 
            y1=value,
            line=dict(color=line_color, width=1, dash="dot")
        )

    fig.add_trace(go.Scatter(
        x=weekly_data['Week'],
        y=weekly_data[data_type_filter == "Moving Time" and 'Moving Time (min)' or 'Distance (km)'],
        fill='tozeroy',
        mode='none',
        fillcolor=fillcolor,
        name="Area Fill"
    ))

    fig.update_layout(
        title="",  # Remove the title
        plot_bgcolor="white",
        margin=dict(t=0, b=100, l=50, r=50),  # Remove top margin, adjust other margins as needed
        xaxis=dict(
            title="Week",
            showgrid=False
        ),
        yaxis=dict(
            title=yaxis_title,
            tickvals=yaxis_tickvals,
            ticktext=yaxis_ticktext,
        ),
        showlegend=False
    )

    selected_points = plotly_events(fig)

    if not selected_points:
        selected_points = [{'x': weekly_data['Week'].iloc[-1]}]

    clicked_data = selected_points[0]
    clicked_week = clicked_data['x']

    selected_data = weekly_data[weekly_data['Week'] == clicked_week].iloc[0]

    # Displaying the information with time in hours (XX.XX hours format) and bold pattern for all three columns
    time_in_hours = selected_data['Moving Time (min)'] / 60
    distance = selected_data['Distance (km)']
    elevation = selected_data['Total Elevation Gain (m)']
