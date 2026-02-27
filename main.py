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
            temp_df = pd.read_csv(f, low_memory=False)
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
st.title("📝🔗 Best Rate Provider")
st.markdown("Side-by-side comparison of Guest Posts and Link Insertions with SEO Metrics.")
df = load_all_data()
if df is not None:
    st.sidebar.header("Search Filters")
    unique_files = df['Source_File'].unique()
    st.sidebar.info(f"Connected to {len(unique_files)} CSV files.")
    with st.sidebar.form("search_form"):
        search_query = st.text_input("Enter Domain (e.g., reddit.com)").strip().lower()
        submit_button = st.form_submit_button("Go 🔍", use_container_width=True)
    if search_query:
        results = df[df['Publisher'] == search_query]
        if not results.empty:
            base_info = results.iloc[0] 
            st.success(f"Results for: **{search_query}**")  
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Authority (AS)", base_info.get('AS', 'N/A'))
                col2.metric("Domain Rating (DR)", base_info.get('DR', 'N/A'))          
                traffic = base_info.get('Total Organic Traffic', 0)
                traffic_display = f"{int(traffic):,}" if pd.notna(traffic) and str(traffic).replace('.','').isdigit() else "N/A"
                col3.metric("Total Traffic", traffic_display)
                col4.metric("Top Country", str(base_info.get('Top Country', 'N/A')).upper())        
                st.caption(f"**Category:** {base_info.get('Category', 'N/A')} | **Link Type:** {base_info.get('Link Follow', 'N/A')}")
            st.divider()
            left_col, right_col = st.columns(2)
            with left_col:
                st.header("📝 Guest Post")
                guest_data = results[results['Type'].str.contains('Guest Post', case=False, na=False)]
                if not guest_data.empty:
                    row = guest_data.iloc[0]
                    with st.container(border=True):
                        st.subheader(f"🥇 {row.get('Best Seller 1st', 'N/A')}")
                        m1, m2 = st.columns(2)
                        m1.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                        m2.metric("Rating", f"⭐ {row.get('Rating 1st', 'N/A')}")         
                        link_1 = row.get('Referral Link 1st', '#')
                        if pd.notna(link_1) and str(link_1).startswith('http'):
                            st.link_button("Order Guest Post", link_1, use_container_width=True)
                        st.divider()
                        st.write("**🥈 Alternatives**")
                        a1, a2 = st.columns(2)
                        a1.info(f"**{row.get('Best Seller 2nd', 'N/A')}**\n\nPrice: ${row.get('Price 2nd', 'N/A')}")
                        a2.info(f"**{row.get('Best Seller 3rd', 'N/A')}**\n\nPrice: ${row.get('Price 3rd', 'N/A')}")
                else:
                    st.info("No Guest Post data available for this domain.")
            with right_col:
                st.header("🔗 Link Insertion")
                link_data = results[results['Type'].str.contains('Link Insertion', case=False, na=False)]    
                if not link_data.empty:
                    row = link_data.iloc[0]
                    with st.container(border=True):
                        st.subheader(f"🥇 {row.get('Best Seller 1st', 'N/A')}")        
                        m1, m2 = st.columns(2)
                        m1.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                        m2.metric("Rating", f"⭐ {row.get('Rating 1st', 'N/A')}")
                        
                        link_1 = row.get('Referral Link 1st', '#')
                        if pd.notna(link_1) and str(link_1).startswith('http'):
                            st.link_button("Order Link Insertion", link_1, use_container_width=True)
                        st.divider()
                        st.write("**🥈 Alternatives**")
                        b1, b2 = st.columns(2)
                        b1.info(f"**{row.get('Best Seller 2nd', 'N/A')}**\n\nPrice: ${row.get('Price 2nd', 'N/A')}")
                        b2.info(f"**{row.get('Best Seller 3rd', 'N/A')}**\n\nPrice: ${row.get('Price 3rd', 'N/A')}")
                else:
                    st.info("No Link Insertion data available for this domain.")
        else:
            st.error(f"No data found for '{search_query}'.")
    else:
        st.info("👈 Enter a domain in the sidebar to search.")        
        st.subheader("Database Overview")
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Records", len(df))
        s2.metric("Unique Domains", df['Publisher'].nunique())        
        if 'DR' in df.columns:
            avg_dr = int(df['DR'].mean())
            s3.metric("Avg. Domain Rating", avg_dr)      
        st.write("### Latest Entries")
        st.dataframe(df.head(50), hide_index=True)
else:
    st.warning("No CSV files found. Please place your CSV files in the `csv_data` folder.")


