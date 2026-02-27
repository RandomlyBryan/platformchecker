import streamlit as st
import pandas as pd
import glob
import os

# 1. Page Configuration
st.set_page_config(page_title="Best Rate Portal", layout="wide", page_icon="🌐")

# 2. Function to Load and Combine all CSVs
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
            temp_df = pd.read_csv(f, low_memory=False)
            temp_df['Source_File'] = os.path.basename(f)
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")
    
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        if 'Publisher' in combined_df.columns:
            # Clean domain names
            combined_df['Publisher'] = combined_df['Publisher'].astype(str).str.strip().str.lower()
            
            # Convert Price to numeric for accurate sorting across different files
            if 'Price 1st' in combined_df.columns:
                combined_df['Price_Numeric'] = pd.to_numeric(
                    combined_df['Price 1st'].astype(str).str.replace(r'[$,]', '', regex=True), 
                    errors='coerce'
                )
            
            # --- NEW ADDITION: Remove duplicates to ensure 1st and 2nd best are unique ---
            # This drops rows where Publisher, Type, and Price are identical
            combined_df = combined_df.drop_duplicates(subset=['Publisher', 'Type', 'Price_Numeric'])
            
            # Sort by Domain, Type, and then Price (Cheapest at the top)
            combined_df = combined_df.sort_values(by=['Publisher', 'Type', 'Price_Numeric'], ascending=True)
            
        return combined_df
    return None

# 3. App Interface
st.title("🔗📝 Best Rate Provider")
st.markdown("Side-by-side comparison of results from multiple sources.")

df = load_all_data()

if df is not None:
    # Sidebar
    st.sidebar.header("Search Filters")
    unique_files = df['Source_File'].unique()
    st.sidebar.info(f"Searching across {len(unique_files)} CSV sources.")
    
    with st.sidebar.form("search_form"):
        search_query = st.text_input("Enter Domain (e.g., reddit.com)").strip().lower()
        submit_button = st.form_submit_button("Search 🔍", use_container_width=True)

    if search_query:
        domain_results = df[df['Publisher'] == search_query]

        if not domain_results.empty:
            # Common SEO Metrics
            base_info = domain_results.iloc[0]
            st.success(f"Results for: **{search_query}**")
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Authority (AS)", base_info.get('AS', 'N/A'))
                col2.metric("Domain Rating (DR)", base_info.get('DR', 'N/A'))
                traffic = base_info.get('Total Organic Traffic', 0)
                traffic_display = f"{int(traffic):,}" if pd.notna(traffic) and isinstance(traffic, (int, float)) else "N/A"
                col3.metric("Total Traffic", traffic_display)
                col4.metric("Top Country", str(base_info.get('Top Country', 'N/A')).upper())

            st.divider()

            left_col, right_col = st.columns(2)

            # --- Logic to display Best vs 2nd Best from different CSV rows ---
            for col, link_type in zip([left_col, right_col], ['Guest Post', 'Link Insertion']):
                with col:
                    st.header(f"{'📝' if 'Guest' in link_type else '🔗'} {link_type}")
                    
                    # Filter for specific type
                    type_data = domain_results[domain_results['Type'].str.contains(link_type, case=False, na=False)]
                    
                    if not type_data.empty:
                        # --- BEST OPTION (Row 1) ---
                        best_row = type_data.iloc[0]
                        with st.container(border=True):
                            st.subheader(f"🥇 Best Option")
                            st.write(f"**Vendor:** {best_row.get('Best Seller 1st', 'N/A')}")
                            
                            m1, m2 = st.columns(2)
                            m1.metric("Price", f"${best_row.get('Price 1st', 'N/A')}")
                            m2.metric("Rating", f"⭐ {best_row.get('Rating 1st', 'N/A')}")

                        # --- 2nd BEST OPTION (Row 2) ---
                        if len(type_data) > 1:
                            second_row = type_data.iloc[1]
                            st.write("**🥈 2nd Best Option (Alternative Source)**")
                            with st.container(border=True):
                                st.write(f"**Vendor:** {second_row.get('Best Seller 1st', 'N/A')}")
                                a1, a2 = st.columns(2)
                                a1.info(f"Price: **${second_row.get('Price 1st', 'N/A')}**")
                        else:
                            st.caption("No alternative sources found for this domain.")
                    else:
                        st.info(f"No {link_type} data found.")
        else:
            st.error(f"No data found for '{search_query}'.")
    else:
        st.info("👈 Enter a domain in the sidebar to search.")
        st.subheader("Database Overview")
        s1, s2 = st.columns(2)
        s1.metric("Total Records", len(df))
        s2.metric("Unique Domains", df['Publisher'].nunique())
        st.dataframe(df.head(20), hide_index=True)
else:
    st.warning("No CSV files found in `csv_data` folder.")
