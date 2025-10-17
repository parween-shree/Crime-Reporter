import pandas as pd

# Global dictionary to simulate a database for user credentials
# IMPORTANT: In a real app, this would be a secure database (like Firestore).
# For this hackathon, this dictionary will hold the state of registered users.
USER_CREDENTIALS = {
    "judge": "hackathon2024",
    "user1": "pass123"
}

def load_data():
    data = pd.read_csv("crime.csv", encoding='utf-8-sig')
    data.columns = data.columns.map(str)
    data.columns = data.columns.str.strip().str.upper()

    # Convert all columns except STATE/UT, DISTRICT, YEAR to numeric, handling errors
    crime_columns = [col for col in data.columns if col not in ['STATE/UT', 'DISTRICT', 'YEAR']]
    for col in crime_columns:
        # Suppress errors by coercing non-numeric values to NaN, then filling with 0
        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
    return data

def get_states(data):
    return sorted(data["STATE/UT"].unique())

def get_years(data):
    if "YEAR" in data.columns:
        return sorted(data["YEAR"].unique())
    return []

def filter_state_district(data, state, district=None, year=None):
    if year is not None and "YEAR" in data.columns:
        data = data[data["YEAR"] == year]
    data = data[data["STATE/UT"] == state]
    if district:
        data = data[data["DISTRICT"] == district]
    return data

def calculate_safety_ratio(data, selected_state):
    total_state_crimes = data[data["STATE/UT"] == selected_state]["TOTAL IPC CRIMES"].sum()
    total_crimes = data["TOTAL IPC CRIMES"].sum()
    if total_crimes == 0: return 0.0 # Avoid division by zero
    return (1 - (total_state_crimes / total_crimes)) * 100

def get_top_crime_composition(data, state, top_n=5):
    # Filter for the specific state
    state_data = data[data["STATE/UT"] == state].copy()
    
    # Exclude non-crime and total columns
    cols_to_drop = ['STATE/UT', 'DISTRICT', 'YEAR', 'TOTAL IPC CRIMES']
    crime_sums = state_data.drop(columns=cols_to_drop, errors='ignore').sum()
    
    if crime_sums.empty or crime_sums.sum() == 0:
        return pd.Series()
        
    # Get the top N crimes
    top_crimes = crime_sums.nlargest(top_n)
    
    # Calculate the sum of all other crimes
    other_sum = crime_sums.sum() - top_crimes.sum()
    
    # Combine into a single Series for the pie chart
    composition = top_crimes
    if other_sum > 0:
        composition["OTHER IPC CRIMES"] = other_sum
        
    return composition

# --- NEW AUTHENTICATION FUNCTIONS ---

def authenticate_user(username, password):
    """Checks if the username/password combination is valid."""
    return USER_CREDENTIALS.get(username) == password

def register_user(username, password):
    """Registers a new user if the username is not taken."""
    if username in USER_CREDENTIALS:
        return False, "Username already exists. Please choose another."
    
    if not username or not password:
        return False, "Username and Password cannot be empty."
        
    USER_CREDENTIALS[username] = password
    return True, "Registration successful! You can now log in."


def load_data():
    """
    Loads and cleans the crime data from the CSV file.
    Also ensures crime columns are numeric for safe calculations.
    """
    try:
        data = pd.read_csv("crime.csv", encoding='utf-8-sig')
        data.columns = data.columns.str.strip().str.upper()
        
        # Ensure 'TOTAL IPC CRIMES' and other crime columns are treated as numeric.
        # This prevents errors during summation in the comparison logic.
        crime_cols = [col for col in data.columns if col not in ['STATE/UT', 'DISTRICT', 'YEAR']]
        for col in crime_cols:
             # Convert to numeric, errors='coerce' turns non-numeric values into NaN
             data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
             
        # Ensure YEAR is integer if present
        if 'YEAR' in data.columns:
            data['YEAR'] = pd.to_numeric(data['YEAR'], errors='coerce').fillna(0).astype(int)
        
        return data
    except Exception as e:
        print(f"Error loading data: {e}. Ensure 'crime.csv' exists.")
        return pd.DataFrame()


def get_states(data):
    """Returns a list of unique states in the dataset."""
    if 'STATE/UT' in data.columns and not data.empty:
        return sorted(data["STATE/UT"].unique())
    return []


def get_years(data):
    """Returns a list of unique years in the dataset."""
    if "YEAR" in data.columns and not data.empty:
        return sorted(data["YEAR"].unique())
    return []


def filter_state_district(data, state, district=None, year=None):
    """
    Filters data by state, district, and year.
    Returns the first matching row if a district is specified.
    """
    filtered_data = data.copy()

    # Convert all column names to strings and normalize them
    filtered_data.columns = filtered_data.columns.map(str)
    # Convert all column names to string, then normalize
    filtered_data.columns = [str(col).strip().upper() for col in filtered_data.columns]


    if year is not None and "YEAR" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["YEAR"] == year]

    # Check if STATE/UT or STATE exists
    if "STATE/UT" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["STATE/UT"] == state.upper()]
    elif "STATE" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["STATE"] == state.upper()]
    else:
        import streamlit as st
        st.error("⚠️ Could not find 'STATE/UT' or 'STATE' column in dataset.")
        st.stop()

    if district and "DISTRICT" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["DISTRICT"] == district]
        # Return only one record for district view
        return filtered_data.head(1)

    return filtered_data


    
    if district and "DISTRICT" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["DISTRICT"] == district]
        # Return only the single record for the district view
        return filtered_data.head(1) 
        
    return filtered_data


def calculate_safety_ratio(data, selected_state):
    """
    Calculates the safety ratio for a given state relative to the total dataset crime.
    """
    if data.empty or "TOTAL IPC CRIMES" not in data.columns:
        return 0.0
        
    total_state_crimes = data[data["STATE/UT"] == selected_state]["TOTAL IPC CRIMES"].sum()
    total_crimes = data["TOTAL IPC CRIMES"].sum()
    
    if total_crimes == 0:
        return 100.0 # Perfectly safe if total crimes is 0
        
    # Safety Ratio calculation: Higher ratio = safer
    return (1 - (total_state_crimes / total_crimes)) * 100


def get_top_crime_composition(data, state, top_n=5):
    """
    Calculates the sum of major crime types for a state and returns the top N 
    plus an 'Other Crimes' category for the composition pie chart.
    """
    state_data = data[data["STATE/UT"] == state]
    
    # List of major crime columns to analyze composition, excluding location/total
    all_crime_columns = [
        "MURDER", "RAPE", "KIDNAPPING & ABDUCTION", "DACOITY", "ROBBERY", 
        "BURGLARY", "THEFT", "DOWRY DEATHS", "ASSAULT ON WOMEN", "CRUELTY BY HUSBAND"
    ]
    
    # Filter for columns that actually exist in the data and are in the list
    crime_columns = [col for col in all_crime_columns if col in state_data.columns]
    
    if not crime_columns:
        return pd.Series(dtype=float)
        
    # Sum up crimes across all rows for that state
    crime_sums = state_data[crime_columns].sum()
    
    # Sort and take the top N listed crimes
    top_crimes = crime_sums.sort_values(ascending=False).head(top_n)
    
    # Calculate 'Other Crimes' (TOTAL IPC CRIMES - sum of top crimes)
    total_ipc = state_data["TOTAL IPC CRIMES"].sum()
    
    # Recalculate 'Other Crimes' based on ALL crimes in the state minus the TOP N
    sum_of_top_n = top_crimes.sum()
    other_crimes_count = total_ipc - sum_of_top_n
    
    # Combine the top crimes and the 'Other Crimes' category
    composition = pd.concat([
        top_crimes, 
        pd.Series([other_crimes_count], index=['OTHER IPC CRIMES'])
    ])

    # Filter out any non-positive values just in case
    composition = composition[composition > 0]
    
    return composition





