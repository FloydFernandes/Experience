import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json


# Google Sheets Setup

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], [
    "https://spreadsheets.google.com/feeds", 
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

# Load Pubs and Travel Data
SHEET_ID = '1hxPGdXIaqmx8jl3N8dtUOKIkhMBy-eoAfF8H8OP0bQk'
sheet = client.open_by_key(SHEET_ID)
pubs_sheet = sheet.worksheet("PubsData")
travel_sheet = sheet.worksheet("TravelData")

# Convert Sheets to DataFrames
pubs_data = pd.DataFrame(pubs_sheet.get_all_records())
travel_data = pd.DataFrame(travel_sheet.get_all_records())

# Process Pubs Data
pubs = {}
for _, row in pubs_data.iterrows():
    pub_name = row["Pub Name"]
    if pub_name not in pubs:
        pubs[pub_name] = {"table_fee": row["Table Fee"], "beers": {}, "rating": row["Google Rating"], "zomato_rating": row["Zomato Rating"]}
    pubs[pub_name]["beers"][row["Beer Name"]] = row["Beer Price"]

# Streamlit UI
# Apply custom styling
st.markdown(
    """
    <style>

        img {
            border-radius: 50%;
        }

        .logo-text {
            align: center;
            font-size: 30px;
        }
        .header-text {
            align: center;
            font-size: 25px;
            padding-bottom: 5px;
        }

        /* Card-like questions */
        .card {
            background: #000000;
            padding: 15px;
            border-radius: 15px;
            # box-shadow: 0px 4px 8px rgba(255, 255, 255, 0.2);
            margin-bottom: 10px;
            # color: #FFC55A;
        }
        .card h4 {
            # margin-bottom: 10px;
        }
        /* Buttons */
        div.stButton > button {
            background-color: #FC4100;
            color: white;
            border-radius: 10px;
            font-size: 18px;
            padding: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Load Logo and Title
col1, col2 = st.columns([1, 4])
with col1:
    st.image(r"https://github.com/FloydFernandes/Experience/blob/9aec1a84cfb9f536a4a9195a7c5a41a6e422cb63/Plannabe%20Logo.png", width=100)  # Ensure "logo.png" is in the same folder
with col2:
    st.markdown("<div class='logo-text'>Welcome to Plannabe!<br></div><div class='header-text'>Plan your beer hopping experience with us 🍻</div>", unsafe_allow_html=True)

# Page title
# st.title("🍻 Plan Your Beer Hopping Experience")
st.write("Select your preferences below and we’ll handle the rest!")

# Number of People
st.markdown('<div class="card"> <h4>👥 How many people?</h4></div>', unsafe_allow_html=True)
num_people = st.number_input("Number of People", min_value=1, step=1, value=2)

# Select Pubs
st.markdown('<div class="card"> <h4>🏠 Select Pubs</h4></div>', unsafe_allow_html=True)
selected_pubs = st.multiselect("Choose up to 4 pubs", list(pubs.keys()), max_selections=4)
selected_beers = {}

# Beer Selection per Pub
for pub in selected_pubs:
    st.markdown(f'<div class="card"> <h4>{pub} (⭐ {pubs[pub]["rating"]} | 🍽 Zomato: {pubs[pub]["zomato_rating"]})</h4></div>', unsafe_allow_html=True)
    selected_beers[pub] = st.multiselect(f"🍺 Select Beers at {pub}", list(pubs[pub]["beers"].keys()))

# Transport Option
st.markdown('<div class="card"> <h4>🚖 Select Transport Option</h4></div>', unsafe_allow_html=True)
travel_options = travel_data["Travel Option"].tolist()
selected_travel = st.radio("Choose an option", travel_options, index=0)
travel_price = travel_data[travel_data["Travel Option"] == selected_travel]["Price"].values[0]

# Table Reservation
st.markdown('<div class="card"> <h4>📌 Table Reservation</h4></div>', unsafe_allow_html=True)
reserve_table = st.radio("By default, we reserve tables (₹50 per pub). Would you like to opt-out?", ["Keep Reservation", "Opt-out"])

# Calculate total cost
total_cost = travel_price
for pub in selected_pubs:
    total_cost += pubs[pub]["table_fee"] if reserve_table == "Keep Reservation" else 0
    for beer in selected_beers[pub]:
        total_cost += pubs[pub]["beers"][beer]

# Display total price
st.subheader(f"💰 Total Cost: ₹{total_cost}/-")

# Submit form
if st.button("📩 Submit Booking"):
    st.success("🎉 Booking Submitted! We’ll confirm your itinerary soon.")
    
    # Store in Google Sheets
    booking_sheet = sheet.worksheet("Bookings")
    booking_sheet.append_row([num_people, str(selected_pubs), str(selected_beers), selected_travel, total_cost])
