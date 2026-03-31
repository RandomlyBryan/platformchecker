import streamlit as st
import pandas as pd
import glob
import os
import re

st.set_page_config(page_title="Best Rate Portal", layout="wide")

def extract_domain(url):
    url = str(url)
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.split('/')[0]
    return url.strip().lower()

def load_platforms():
    path = 'platforms.csv'
    if os.path.exists(path):
        try:
            p_df = pd.read_csv(path)
            p_df.columns = [c.strip().lower() for c in p_df.columns]
            return p_df
        except Exception:
            return pd.DataFrame(columns=['platform', 'link'])
    return pd.DataFrame(columns=['platform', 'link'])

def save_platform(name, link):
    path = 'platforms.csv'
    new_data = pd.DataFrame([[name.strip(), link.strip()]], columns=['platform', 'link'])
    if os.path.exists(path):
        existing_df = pd.read_csv(path)
        # Prevent duplicates
        if name.strip().lower() not in existing_df.iloc[:, 0].str.lower().values:
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            updated_df.to_csv(path, index=False)
            return True
    else:
        new_data.to_csv(path, index=False)
        return True
    return False

@st.cache_data(ttl=60)
def load_all_data():
    path = 'csv_data'
    if not os.path.exists(path): os.makedirs(path)
    all_files = glob.glob(os.path.join(path, "*.csv")) + glob.glob(os.path.join(path, "*.CSV"))
    if not all_files: return None
    
    df_list = []
    for f in all_files:
        try:
            temp_df = pd.read_csv(f, low_memory=False)
            if 'Publisher' not in temp_df.columns and len(temp_df.columns) >= 30:
                mapped_df = pd.DataFrame()
                mapped_df['Publisher'] = temp_df.iloc[:, 0]
                mapped_df['Price 1st'] = temp_df.iloc[:, 3]
                mapped_df['Referral Link 1st'] = temp_df.iloc[:, 29]
                mapped_df['Best Seller 1st'] = "MPE Premium Sheet"
                mapped_df['Type'] = 'Guest Post' 
                mapped_df['Rating 1st'] = 'N/A'
                mapped_df['DR'] = temp_df.iloc[:, 1] if len(temp_df.columns) > 1 else "N/A"
                temp_df = mapped_df
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")

    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        if 'Publisher' in combined_df.columns:
            combined_df['Publisher'] = combined_df['Publisher'].apply(extract_domain)
        if 'Price 1st' in combined_df.columns:
            combined_df['temp_price'] = pd.to_numeric(
                combined_df['Price 1st'].astype(str).str.replace('$', '').str.replace(',', ''), 
                errors='coerce'
            )
            combined_df = combined_df.sort_values(by=['Publisher', 'temp_price'], ascending=[True, True])
        return combined_df
    return None

def show_platform_link(seller_name, p_df):
    name_clean = str(seller_name).lower().strip()
    match = p_df[p_df['platform'].str.lower().apply(lambda x: x in name_clean if pd.notna(x) else False)]
    if not match.empty:
        link = match.iloc[0]['link']
        st.info(f"🔗 **Platform Link:** `{link}`")
        st.link_button(f"Open Dashboard", link, use_container_width=True)
    else:
        st.caption("No dashboard link mapped for this seller.")

# --- UI START ---
st.title("📝🔗 Best Rate Provider")

df = load_all_data()
p_df = load_platforms()

tab1, tab2 = st.tabs(["🔍 Search Portal", "⚙️ Manage Platforms"])

with tab1:
    st.sidebar.header("Search Filters")
    with st.sidebar.form("search_form"):
        raw_input = st.text_input("Enter Domain or URL").strip()
        submit_button = st.form_submit_button("Go 🔍", use_container_width=True)

    if raw_input:
        search_query = extract_domain(raw_input)
        results = df[df['Publisher'] == search_query] if df is not None else pd.DataFrame()
        
        if not results.empty:
            base_info = results.iloc[0] 
            st.success(f"Results for: **{search_query}**")  
            
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("AS", base_info.get('AS', 'N/A'))
                c2.metric("DR", base_info.get('DR', 'N/A'))          
                c3.metric("Traffic", base_info.get('Total Organic Traffic', 'N/A'))
                c4.metric("Top Country", str(base_info.get('Top Country', 'N/A')).upper())        

            l_col, r_col = st.columns(2)
            for col, p_type in zip([l_col, r_col], ['Guest Post', 'Link Insertion']):
                with col:
                    st.header(f"{'📝' if p_type == 'Guest Post' else '🔗'} {p_type}")
                    subset = results[results['Type'].str.contains(p_type, case=False, na=False)]
                    if not subset.empty:
                        row = subset.iloc[0]
                        with st.container(border=True):
                            seller = row.get('Best Seller 1st', 'N/A')
                            st.subheader(f"🥇 {seller}")
                            m1, m2 = st.columns(2)
                            m1.metric("Best Price", f"${row.get('Price 1st', 'N/A')}")
                            m2.metric("Rating", f"⭐ {row.get('Rating 1st', 'N/A')}")
                            show_platform_link(seller, p_df)
                    else:
                        st.info(f"No {p_type} data.")
        else:
            st.error("No data found.")

with tab2:
    st.header("Add New Platform")
    with st.form("add_platform_form", clear_on_submit=True):
        new_name = st.text_input("Platform Name (e.g. Adsy)")
        new_link = st.text_input("Direct Dashboard Link")
        add_btn = st.form_submit_button("Save Platform")
        
        if add_btn and new_name and new_link:
            if save_platform(new_name, new_link):
                st.success(f"Added {new_name} successfully!")
                st.rerun()
            else:
                st.warning("Platform already exists or error occurred.")

    st.divider()
    st.subheader("Current Platform Map")
    st.dataframe(p_df, use_container_width=True, hide_index=True)
