import streamlit as st
import pandas as pd
import glob
import os

# 1. Page Configuration
st.set_page_config(page_title="Team Publisher Portal", layout="wide")

# 2. Function to Load and Combine all CSVs
@st.cache_data(ttl=60)
def load_all_data():
    path = 'csv_data'
    
    if not os.path.exists(path):
        os.makedirs(path)
        # For local testing, if the folder is empty but a file was provided:
        # return pd.read_csv('Inventory_2026-02-27_15-12-56_PM.csv')
        return None

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
        if 'Publisher' in combined_df.columns:
            combined_df['Publisher'] = combined_df['Publisher'].astype(str).str.strip().str.lower()
        return combined_df
    return None

# 3. App Interface
st.title("🌐 Team Publisher Data Portal")
st.markdown("Compare Guest Post and Link Insertion prices with SEO metrics.")

df = load_all_data()

if df is not None:
    # Sidebar for Search
    st.sidebar.header("Search Filters")
    unique_files = df['Source_File'].unique() if 'Source_File' in df.columns else ["Uploaded File"]
    st.sidebar.info(f"Connected to {len(unique_files)} CSV source(s).")
    
    # --- SEARCH FORM WITH GO BUTTON ---
    with st.sidebar.form("search_form"):
        search_query = st.text_input("Enter Domain (e.g., reddit.com)").strip().lower()
        # This button allows both clicking "Go" and pressing the "Enter" key
        submit_button = st.form_submit_button("Search 🔍", use_container_width=True)

    if search_query:
        results = df[df['Publisher'] == search_query]

        if not results.empty:
            # Get common metrics from the first matching row
            base_info = results.iloc[0]
            
            st.success(f"Results for: **{search_query}**")
            
            # --- NEW: SITE METRICS SECTION ---
            with st.expander("📊 View Site SEO Stats", expanded=True):
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Authority Score (AS)", base_info.get('AS', 'N/A'))
                m2.metric("Domain Rating (DR)", base_info.get('DR', 'N/A'))
                m3.metric("Total Traffic", f"{base_info.get('Total Organic Traffic', 0):,}")
                m4.metric("Top Country", base_info.get('Top Country', 'N/A').upper())
                
                st.write(f"**Category:** {base_info.get('Category', 'General')} | **Link Type:** {base_info.get('Link Follow', 'N/A')}")

            st.divider()

            # Create two big columns for side-by-side comparison
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
                            
                            c1, c2 = st.columns(2)
                            c1.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                            c2.metric("Rating", f"⭐ {row.get('Rating 1st', 'N/A')}")
                            
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
                    st.info("No Guest Post data found.")

            # --- RIGHT COLUMN: LINK INSERTION ---
            with right_col:
                st.header("🔗 Link Insertion")
                link_data = results[results['Type'].str.contains('Link Insertion', case=False, na=False)]
                if not link_data.empty:
                    for _, row in link_data.iterrows():
                        with st.container(border=True):
                            st.subheader("🏆 Best Platform")
                            st.write(f"**{row.get('Best Seller 1st', 'N/A')}**")
                            
                            c1, c2 = st.columns(2)
                            c1.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                            c2.metric("Rating", f"⭐ {row.get('Rating 1st', 'N/A')}")
                            
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
                    st.info("No Link Insertion data found.")
        else:
            st.error(f"No data found for '{search_query}'. Please check the spelling or domain extension.")
    else:
        st.info("👈 Enter a publisher domain (e.g., yahoo.com) in the sidebar and click Go.")
        
        # Dashboard Overview
        st.subheader("Database Overview")
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Records", len(df))
        s2.metric("Unique Domains", df['Publisher'].nunique())
        s3.metric("Avg. DR", int(df['DR'].mean()) if 'DR' in df.columns else 0)
        
        st.write("### Recent Data (Top 50)")
        st.dataframe(df.head(50), hide_index=True)
else:
    st.warning("No CSV files found in the `csv_data` folder. Please add files to begin.")

