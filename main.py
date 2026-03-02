import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="Best Rate Portal", layout="wide")

@st.cache_data(ttl=60)
def load_all_data():
    path = 'csv_data'
    if not os.path.exists(path):
        os.makedirs(path)
    
    all_files = glob.glob(os.path.join(path, "*.csv")) + glob.glob(os.path.join(path, "*.CSV"))
    if not all_files:
        return None

    df_list = []
    for f in all_files:
        try:
            # Read the CSV
            temp_df = pd.read_csv(f, low_memory=False)
            
            # --- CUSTOM LOGIC FOR ATTACHED SHEET ---
            # If the CSV has specific column counts or names matching your new sheet
            # Column A (index 0), Column D (index 3), Column AD (index 29)
            if len(temp_df.columns) >= 30: 
                # We rename columns to match your existing logic
                temp_df = temp_df.rename(columns={
                    temp_df.columns[0]: 'Publisher',
                    temp_df.columns[3]: 'Price 1st',
                    temp_df.columns[29]: 'Referral Link 1st'
                })
                # Add dummy 'Type' if missing so it shows in search
                if 'Type' not in temp_df.columns:
                    temp_df['Type'] = 'Guest Post' # Or logic to determine type
            
            temp_df['Source_File'] = os.path.basename(f)
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")

    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        
        # Standardize Publisher names
        if 'Publisher' in combined_df.columns:
            combined_df['Publisher'] = combined_df['Publisher'].astype(str).str.strip().str.lower()
        
        # Convert Price to numeric for accurate sorting
        if 'Price 1st' in combined_df.columns:
            combined_df['Price 1st'] = pd.to_numeric(combined_df['Price 1st'], errors='coerce')
            
        return combined_df
    return None

st.title("📝🔗 Best Rate Provider")
df = load_all_data()

if df is not None:
    st.sidebar.header("Search Filters")
    unique_files = df['Source_File'].unique()
    st.sidebar.info(f"Connected to {len(unique_files)} CSV files.")

    with st.sidebar.form("search_form"):
        search_query = st.text_input("Enter Domain (e.g., reddit.com)").strip().lower()
        submit_button = st.form_submit_button("Go 🔍", use_container_width=True)

    if search_query:
        # 1. Filter by Domain
        results = df[df['Publisher'] == search_query]
        
        if not results.empty:
            # 2. SORT BY PRICE (Lowest first) to ensure the "Best Seller" is actually the cheapest
            results = results.sort_values(by='Price 1st', ascending=True)
            
            # Get metrics from the first row (now the cheapest)
            base_info = results.iloc[0] 
            st.success(f"Results for: **{search_query}**")  
            
            # ... [Metric Display Code remains the same] ...
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Authority (AS)", base_info.get('AS', 'N/A'))
                col2.metric("Domain Rating (DR)", base_info.get('DR', 'N/A'))          
                traffic = base_info.get('Total Organic Traffic', 0)
                traffic_display = f"{int(traffic):,}" if pd.notna(traffic) and str(traffic).replace('.','').isdigit() else "N/A"
                col3.metric("Total Traffic", traffic_display)
                col4.metric("Top Country", str(base_info.get('Top Country', 'N/A')).upper())        

            st.divider()

            left_col, right_col = st.columns(2)
            
            # GUEST POST SECTION
            with left_col:
                st.header("📝 Guest Post")
                # Filter guest posts and ensure we take the lowest price entry
                guest_data = results[results['Type'].str.contains('Guest Post', case=False, na=False)].sort_values('Price 1st')
                
                if not guest_data.empty:
                    best_row = guest_data.iloc[0] # The absolute cheapest across all files
                    with st.container(border=True):
                        st.subheader(f"🥇 Lowest Price: {best_row.get('Source_File', 'N/A')}")
                        m1, m2 = st.columns(2)
                        m1.metric("Price", f"${best_row.get('Price 1st', 'N/A')}")
                        m2.metric("Rating", f"⭐ {best_row.get('Rating 1st', 'N/A')}")          
                        
                        link = best_row.get('Referral Link 1st', '#')
                        st.link_button("Order Best Rate", str(link), use_container_width=True)
                        
                        if len(guest_data) > 1:
                            st.write("**🥈 Other Providers**")
                            st.dataframe(guest_data[['Price 1st', 'Source_File']].iloc[1:], hide_index=True)
                else:
                    st.info("No Guest Post data available.")

            # LINK INSERTION SECTION
            with right_col:
                st.header("🔗 Link Insertion")
                link_data = results[results['Type'].str.contains('Link Insertion', case=False, na=False)].sort_values('Price 1st')
                if not link_data.empty:
                    best_link_row = link_data.iloc[0]
                    with st.container(border=True):
                        st.subheader(f"🥇 Lowest Price: {best_link_row.get('Source_File', 'N/A')}")
                        m1, m2 = st.columns(2)
                        m1.metric("Price", f"${best_link_row.get('Price 1st', 'N/A')}")
                        m2.metric("Rating", f"⭐ {best_link_row.get('Rating 1st', 'N/A')}")
                        
                        l_link = best_link_row.get('Referral Link 1st', '#')
                        st.link_button("Order Best Rate", str(l_link), use_container_width=True)
                else:
                    st.info("No Link Insertion data available.")
        else:
            st.error(f"No data found for '{search_query}'.")
    else:
        st.info("👈 Enter a domain in the sidebar to search.")
        # ... [Database Overview remains the same] ...
