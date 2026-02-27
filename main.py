import streamlit as st
import pandas as pd
import glob
import os

# 1. Page Configuration
st.set_page_config(page_title="Rate Checker", layout="wide", page_icon="🌐")

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
            
            # Convert Price to numeric for accurate sorting
            if 'Price 1st' in combined_df.columns:
                combined_df['Price_Numeric'] = pd.to_numeric(
                    combined_df['Price 1st'].astype(str).str.replace(r'[$,]', '', regex=True), 
                    errors='coerce'
                )
            
            # Sort everything by domain and price (lowest first)
            combined_df = combined_df.sort_values(by=['Publisher', 'Type', 'Price_Numeric'], ascending=True)
            
        return combined_df
    return None

# 3. App Interface
st.title("🌐 Best Rate Portal")
st.markdown("Side-by-side comparison. Showing the **Best Price** found across all files.")

df = load_all_data()

if df is not None:
    # Sidebar
    st.sidebar.header("Search Filters")
    unique_files = df['Source_File'].unique()
    st.sidebar.info(f"Connected to {len(unique_files)} CSV files.")
    
    with st.sidebar.form("search_form"):
        search_query = st.text_input("Enter Domain (e.g., reddit.com)").strip().lower()
        submit_button = st.form_submit_button("Search 🔍", use_container_width=True)

    if search_query:
        # Filter for the domain
        domain_results = df[df['Publisher'] == search_query]

        if not domain_results.empty:
            # SEO Metrics (taken from the very first available row)
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

            # --- Logic to display Lowest vs 2nd Lowest ---
            for col, link_type in zip([left_col, right_col], ['Guest Post', 'Link Insertion']):
                with col:
                    st.header(f"{'📝' if 'Guest' in link_type else '🔗'} {link_type}")
                    
                    # Filter for specific type (Guest Post or Link Insertion)
                    type_data = domain_results[domain_results['Type'].str.contains(link_type, case=False, na=False)]
                    
                    if not type_data.empty:
                        # 1st Lowest Price Record
                        best_deal = type_data.iloc[0]
                        
                        with st.container(border=True):
                            st.subheader(f"🥇 Cheapest: {best_deal.get('Best Seller 1st', 'N/A')}")
                            m1, m2 = st.columns(2)
                            m1.metric("Price", f"${best_deal.get('Price 1st', 'N/A')}")
                            m2.metric("Source", best_deal['Source_File'])
                            
                            link = best_deal.get('Referral Link 1st', '#')
                            if pd.notna(link) and str(link).startswith('http'):
                                st.link_button(f"Order on {best_deal.get('Best Seller 1st', 'Platform')}", link, use_container_width=True)

                        # 2nd Lowest Price Record (if it exists)
                        if len(type_data) > 1:
                            second_deal = type_data.iloc[1]
                            st.write("**🥈 2nd Best Option**")
                            with st.container(border=True):
                                a1, a2 = st.columns(2)
                                a1.info(f"**{second_deal.get('Best Seller 1st', 'N/A')}**\n\nPrice: ${second_deal.get('Price 1st', 'N/A')}")
                                a2.info(f"Source: {second_deal['Source_File']}")
                        else:
                            st.caption("No other CSVs contain this domain for comparison.")
                    else:
                        st.info(f"No {link_type} data found.")
        else:
            st.error(f"No data found for '{search_query}'.")
    else:
        st.info("👈 Enter a domain in the sidebar to search.")
        st.subheader("Database Overview")
        s1, s2 = st.columns(2)
        s1.metric("Total Rows in CSVs", len(df))
        s2.metric("Unique Domains", df['Publisher'].nunique())
        st.dataframe(df.head(50), hide_index=True)
else:
    st.warning("No CSV files found in `csv_data` folder.")
