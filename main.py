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
            file_name = os.path.basename(f)
            
            # --- CUSTOM MAPPING FOR NEW CSV FORMAT (A, D, AD) ---
            # Identifies the new sheet by column count and lack of 'Publisher' header
            if 'Publisher' not in temp_df.columns and len(temp_df.columns) >= 30:
                mapped_df = pd.DataFrame()
                mapped_df['Publisher'] = temp_df.iloc[:, 0]        # Column A
                mapped_df['Price 1st'] = temp_df.iloc[:, 3]        # Column D
                mapped_df['Referral Link 1st'] = temp_df.iloc[:, 29] # Column AD
                
                # Tag this specifically as "Own Source"
                mapped_df['Source_Label'] = "Own Source"
                mapped_df['Best Seller 1st'] = "Direct Provider"
                
                # Defaults to keep UI stable
                mapped_df['Type'] = 'Guest Post' 
                mapped_df['Rating 1st'] = 'N/A'
                mapped_df['DR'] = temp_df.iloc[:, 1] if len(temp_df.columns) > 1 else "N/A"
                
                temp_df = mapped_df
            else:
                # For original CSVs, label them by their filename or a generic tag
                temp_df['Source_Label'] = "Marketplace"

            temp_df['Source_File'] = file_name
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")

    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        
        if 'Publisher' in combined_df.columns:
            combined_df['Publisher'] = combined_df['Publisher'].astype(str).str.strip().str.lower()
        
        # Sort by price so iloc[0] is always the cheapest
        if 'Price 1st' in combined_df.columns:
            combined_df['temp_price'] = pd.to_numeric(
                combined_df['Price 1st'].astype(str).str.replace('$', '').str.replace(',', ''), 
                errors='coerce'
            )
            combined_df = combined_df.sort_values(by=['Publisher', 'temp_price'], ascending=[True, True])
            
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
                
                # Display the "Own Source" or "Marketplace" detail here
                source_tag = base_info.get('Source_Label', 'Standard')
                st.caption(f"**Provider:** {source_tag} | **File:** {base_info.get('Source_File')}")

            st.divider()

            left_col, right_col = st.columns(2)

            with left_col:
                st.header("📝 Guest Post")
                guest_data = results[results['Type'].str.contains('Guest Post', case=False, na=False)]
                if not guest_data.empty:
                    row = guest_data.iloc[0]
                    with st.container(border=True):
                        # Show label in the subheader if it's Own Source
                        label_prefix = "⭐ [Own Source] " if row.get('Source_Label') == "Own Source" else "🥇 "
                        st.subheader(f"{label_prefix}{row.get('Best Seller 1st', 'N/A')}")
                        
                        m1, m2 = st.columns(2)
                        m1.metric("Best Price", f"${row.get('Price 1st', 'N/A')}")
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
                    st.info("No Guest Post data available.")

            with right_col:
                st.header("🔗 Link Insertion")
                link_data = results[results['Type'].str.contains('Link Insertion', case=False, na=False)]    
                if not link_data.empty:
                    row = link_data.iloc[0]
                    with st.container(border=True):
                        label_prefix = "⭐ [Own Source] " if row.get('Source_Label') == "Own Source" else "🥇 "
                        st.subheader(f"{label_prefix}{row.get('Best Seller 1st', 'N/A')}")        
                        
                        m1, m2 = st.columns(2)
                        m1.metric("Best Price", f"${row.get('Price 1st', 'N/A')}")
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
                    st.info("No Link Insertion data available.")
        else:
            st.error(f"No data found for '{search_query}'.")
    else:
        st.info("👈 Enter a domain in the sidebar to search.")        
        st.subheader("Database Overview")
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Records", len(df))
        s2.metric("Unique Domains", df['Publisher'].nunique())        
        if 'DR' in df.columns:
            avg_dr = int(pd.to_numeric(df['DR'], errors='coerce').mean() or 0)
            s3.metric("Avg. Domain Rating", avg_dr)      
        
        st.write("### All Records (Sorted by Price)")
        st.dataframe(df.drop(columns=['temp_price'], errors='ignore').head(100), hide_index=True)
else:
    st.warning("No CSV files found. Please place your CSV files in the `csv_data` folder.")
