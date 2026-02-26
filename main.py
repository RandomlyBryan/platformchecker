import streamlit as st
import pandas as pd
import glob
import os

# 1. Page Configuration
st.set_page_config(page_title="Team Publisher Portal", layout="wide")

# 2. Function to Load and Combine all CSVs
@st.cache_data(ttl=60)  # Refresh data every 60 seconds
def load_all_data():
    path = 'csv_data'
    
    # Check if folder exists
    if not os.path.exists(path):
        os.makedirs(path)
        return None

    # Find all CSV files (handles .csv and .CSV)
    all_files = glob.glob(os.path.join(path, "*.csv")) + glob.glob(os.path.join(path, "*.CSV"))
    
    if not all_files:
        return None

    df_list = []
    for f in all_files:
        try:
            # Load each file
            temp_df = pd.read_csv(f)
            # Add a column to see which file the data came from (helpful for debugging)
            temp_df['Source_File'] = os.path.basename(f)
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")
    
    if df_list:
        # Combine all files into one master table
        combined_df = pd.concat(df_list, ignore_index=True)
        
        # Clean up Domain column: Remove spaces and make lowercase for easy searching
        if 'Publisher' in combined_df.columns:
            combined_df['Publisher'] = combined_df['Publisher'].astype(str).str.strip().str.lower()
        
        return combined_df
    return None

# 3. App Interface
st.title("🌐 Team Publisher Data Portal")
st.markdown("This app merges all CSVs in your `csv_data` folder automatically.")

df = load_all_data()

if df is not None:
    # Sidebar for Search
    st.sidebar.header("Search Filters")
    
    # Show how many files are being read
    unique_files = df['Source_File'].unique()
    st.sidebar.info(f"Connected to {len(unique_files)} CSV files.")
    
    # Search Input
    search_query = st.sidebar.text_input("Enter Domain (e.g., lifeunexpected.co.uk)").strip().lower()

    if search_query:
        # Filter the master dataframe
        results = df[df['Publisher'] == search_query]

        if not results.empty:
            st.success(f"Found {len(results)} entry/entries for **{search_query}**")
            
            # Loop through results (in case there is a Guest Post and a Link Insertion)
            for _, row in results.iterrows():
                with st.expander(f"Type: {row.get('Type', 'N/A')} | DR: {row.get('DR', 'N/A')} | Traffic: {row.get('Organic Traffic', 'N/A')}", expanded=True):
                    
                    # Section 1: Best Platform
                    st.subheader("1. Best platform to get order from")
                    c1, c2, c3 = st.columns([2, 1, 1])
                    
                    seller_1 = row.get('Best Seller 1st', 'N/A')
                    price_1 = row.get('Price 1st', 'N/A')
                    link_1 = row.get('Referral Link 1st', '#')
                    
                    c1.markdown(f"### 🏆 {seller_1}")
                    c2.metric("Best Price", f"${price_1}")
                    if pd.notna(link_1) and str(link_1).startswith('http'):
                        c3.link_button("Open Website", link_1)
                    else:
                        c3.write("No Link Available")

                    st.divider()

                    # Section 2: Alternative Platforms
                    st.subheader("2. Alternative platforms")
                    alt1, alt2 = st.columns(2)

                    with alt1:
                        st.info(f"**{row.get('Best Seller 2nd', 'N/A')}**")
                        st.write(f"Price: ${row.get('Price 2nd', 'N/A')}")
                        link_2 = row.get('Referral Link 2nd')
                        if pd.notna(link_2) and str(link_2).startswith('http'):
                            st.link_button("View Option 2", link_2)

                    with alt2:
                        st.info(f"**{row.get('Best Seller 3rd', 'N/A')}**")
                        st.write(f"Price: ${row.get('Price 3rd', 'N/A')}")
                        link_3 = row.get('Referral Link 3rd')
                        if pd.notna(link_3) and str(link_3).startswith('http'):
                            st.link_button("View Option 3", link_3)
        else:
            st.error(f"No data found for '{search_query}'. Check the spelling or if it's in your CSVs.")
    else:
        st.info("👈 Enter a publisher domain in the sidebar to start.")
        
        # Dashboard Overview
        st.subheader("Database Statistics")
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Rows", len(df))
        s2.metric("Unique Sites", df['Publisher'].nunique())
        s3.metric("Categories", df['Category'].nunique() if 'Category' in df.columns else 0)
        
        st.write("### All Data Preview")
        st.dataframe(df.head(100)) # Shows the first 100 rows
else:
    st.warning("No CSV files found in the `csv_data` folder.")
    st.info("Please add your CSV files to `E:\\publisher_app\\csv_data` and refresh this page.")