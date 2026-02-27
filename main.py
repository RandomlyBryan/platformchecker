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
            temp_df = pd.read_csv(f)
            temp_df['Source_File'] = os.path.basename(f)
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")
    
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        # Clean up Domain column: Remove spaces and make lowercase for easy searching
        if 'Publisher' in combined_df.columns:
            combined_df['Publisher'] = combined_df['Publisher'].astype(str).str.strip().str.lower()
        return combined_df
    return None

# 3. App Interface
st.title("🌐 Links Team Best Rate Checker")

df = load_all_data()

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.header("Search Filters")
    
    # Search Input
    search_query = st.sidebar.text_input("Enter Domain (e.g., lifeunexpected.co.uk)").strip().lower()

    # Hidden toggle for admin use to see raw data
    show_raw_data = st.sidebar.checkbox("Show Full Database")

    # --- MAIN CONTENT ---
    if search_query:
        # Filter the master dataframe
        results = df[df['Publisher'] == search_query]

        if not results.empty:
            st.success(f"Showing results for **{search_query}**")
            
            # Create two big columns for the side-by-side layout
            left_col, right_col = st.columns(2)

            # --- LEFT COLUMN: GUEST POST ---
            with left_col:
                st.header("📝 Guest Post")
                guest_data = results[results['Type'].str.contains('Guest Post', case=False, na=False)]
                if not guest_data.empty:
                    for _, row in guest_data.iterrows():
                        with st.container(border=True):
                            st.subheader("🏆 Best Platform")
                            st.write(f"**{row.get('Best Seller 1st', 'N/A')}**")
                            st.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                            
                            link_1 = row.get('Referral Link 1st', '#')
                            if pd.notna(link_1) and str(link_1).startswith('http'):
                                st.link_button("Order on Best Platform", link_1, use_container_width=True)

                            st.divider()
                            st.subheader("🥈 Alternatives")
                            a1, a2 = st.columns(2)
                            with a1:
                                st.info(f"**{row.get('Best Seller 2nd', 'N/A')}**\n\nPrice: ${row.get('Price 2nd', 'N/A')}")
                            with a2:
                                st.info(f"**{row.get('Best Seller 3rd', 'N/A')}**\n\nPrice: ${row.get('Price 3rd', 'N/A')}")
                else:
                    st.info("No Guest Post data found for this site.")

            # --- RIGHT COLUMN: LINK INSERTION ---
            with right_col:
                st.header("🔗 Link Insertion")
                link_data = results[results['Type'].str.contains('Link Insertion', case=False, na=False)]
                if not link_data.empty:
                    for _, row in link_data.iterrows():
                        with st.container(border=True):
                            st.subheader("🏆 Best Platform")
                            st.write(f"**{row.get('Best Seller 1st', 'N/A')}**")
                            st.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                            
                            link_1 = row.get('Referral Link 1st', '#')
                            if pd.notna(link_1) and str(link_1).startswith('http'):
                                st.link_button("Order on Best Platform", link_1, use_container_width=True)

                            st.divider()
                            st.subheader("🥈 Alternatives")
                            b1, b2 = st.columns(2)
                            with b1:
                                st.info(f"**{row.get('Best Seller 2nd', 'N/A')}**\n\nPrice: ${row.get('Price 2nd', 'N/A')}")
                            with b2:
                                st.info(f"**{row.get('Best Seller 3rd', 'N/A')}**\n\nPrice: ${row.get('Price 3rd', 'N/A')}")
                else:
                    st.info("No Link Insertion data found for this site.")
        else:
            st.error(f"No data found for '{search_query}'.")
            
    # Show welcome message if no search has been performed
    elif not show_raw_data:
        st.info("👈 Enter a publisher domain in the sidebar to begin.")
        st.write("---")
        st.caption("Developed for the Link Building Team")

    # This part shows only if the checkbox in the sidebar is checked
    if show_raw_data:
        st.divider()
        st.subheader("📊 Full Database View")
        st.dataframe(df)

else:
    st.warning("No CSV files found in the `csv_data` folder.")
    st.info("Please add your CSV files to the `csv_data` folder and refresh the page.")
