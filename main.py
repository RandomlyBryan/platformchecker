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
            if 'notes' not in p_df.columns:
                p_df['notes'] = ""
            return p_df
        except Exception:
            return pd.DataFrame(columns=['platform', 'link', 'notes'])
    return pd.DataFrame(columns=['platform', 'link', 'notes'])

def save_or_update_platform(name, link, notes):
    path = 'platforms.csv'
    name_clean = name.strip()
    p_df = load_platforms()
    new_row = pd.DataFrame([[name_clean, link.strip(), notes.strip()]], columns=['platform', 'link', 'notes'])
    if not p_df.empty and name_clean.lower() in p_df['platform'].str.lower().values:
        p_df.loc[p_df['platform'].str.lower() == name_clean.lower(), ['link', 'notes']] = [link.strip(), notes.strip()]
        p_df.to_csv(path, index=False)
        return "updated"
    else:
        updated_df = pd.concat([p_df, new_row], ignore_index=True)
        updated_df.to_csv(path, index=False)
        return "added"

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
            # Load the file completely to check column count properly
            temp_raw = pd.read_csv(f, low_memory=False)
            col_count = len(temp_raw.columns)
            
            # --- CASE 1: Your Negotiated Master List (30+ Columns, Data at Row 3) ---
            if col_count >= 30:
                # Reload skipping the first two rows (junk and headers)
                temp_df = pd.read_csv(f, skiprows=2, header=None, low_memory=False)
                if not temp_df.empty:
                    mapped_df = pd.DataFrame()
                    # Column A=0 (Domain), D=3 (Price), AD=29 (Pitchbox)
                    mapped_df['Publisher'] = temp_df.iloc[:, 0].apply(extract_domain)
                    mapped_df['Price 1st'] = temp_df.iloc[:, 3]
                    mapped_df['Referral Link 1st'] = temp_df.iloc[:, 29]
                    mapped_df['Best Seller 1st'] = "Direct Negotiation"
                    mapped_df['Type'] = 'Guest Post'
                    mapped_df['is_direct_csv'] = True 
                    df_list.append(mapped_df)
            
            # --- CASE 2: Standard Marketplace CSVs ---
            elif 'Publisher' in temp_raw.columns or 'publisher' in [c.lower() for c in temp_raw.columns]:
                temp_raw.columns = [c.title() if c.lower() == 'publisher' else c for c in temp_raw.columns]
                temp_raw['is_direct_csv'] = False
                temp_raw['Publisher'] = temp_raw['Publisher'].apply(extract_domain)
                df_list.append(temp_raw)
                
        except Exception:
            continue
            
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        if 'Price 1st' in combined_df.columns:
            combined_df['temp_price'] = pd.to_numeric(
                combined_df['Price 1st'].astype(str).str.replace('$', '').str.replace(',', ''), 
                errors='coerce'
            )
            # Ensure sorting puts Direct at the top and lowest price first
            combined_df = combined_df.sort_values(by=['Publisher', 'is_direct_csv', 'temp_price'], ascending=[True, False, True])
        return combined_df
    return None

def show_copy_link(link, notes=None):
    if notes and str(notes).strip() and str(notes).lower() != 'nan':
        st.warning(f"📝 {notes}")
    
    if pd.isna(link) or str(link).lower() == 'nan' or not str(link).strip():
        st.error("No Link available.")
    else:
        st.write("📋 **Copy Dashboard Link:**")
        st.code(link, language=None)
        st.link_button("🚀 Open Dashboard", link, use_container_width=True)

def show_platform_link(seller_name, p_df, csv_link=None):
    name_clean = str(seller_name).lower().strip()
    match = p_df[p_df['platform'].str.lower().apply(lambda x: x in name_clean if pd.notna(x) else False)]
    
    if not match.empty:
        row = match.iloc[0]
        show_copy_link(row['link'], row.get('notes', ""))
    elif csv_link and str(csv_link).startswith('http'):
        show_copy_link(csv_link, "Link from Master Sheet")
    else:
        st.caption("No link mapped.")

df = load_all_data()
p_df = load_platforms()

st.title("📝🔗 Best Rate Provider")

tab1, tab2 = st.tabs(["🔍 Search Portal", "⚙️ Manage Platforms"])

with tab1:
    st.sidebar.header("Search Filters")
    with st.sidebar.form("search_form"):
        raw_input = st.text_input("Enter Domain or URL").strip()
        submit_button = st.form_submit_button("Go 🔍", use_container_width=True)

    if raw_input:
        search_query = extract_domain(raw_input)
        
        # Priority 1: Check Negotiated Master CSV
        csv_negotiated = pd.DataFrame()
        if df is not None:
            csv_negotiated = df[(df['Publisher'] == search_query) & (df['is_direct_csv'] == True)]

        # Priority 2: Check manual platforms.csv
        p_match = p_df[p_df['platform'].str.lower() == search_query]

        if not csv_negotiated.empty:
            # Pick the cheapest negotiated entry
            neg_row = csv_negotiated.sort_values('temp_price').iloc[0]
            st.success(f"Direct Negotiated Match (Master List): **{search_query}**")
            with st.container(border=True):
                st.metric("Negotiated Price", f"${neg_row['Price 1st']}")
                show_copy_link(neg_row['Referral Link 1st'], "Found in Negotiated Master CSV")
        
        elif not p_match.empty:
            st.success(f"Direct Negotiated Match (Platform.csv): **{search_query}**")
            with st.container(border=True):
                match_row = p_match.iloc[0]
                show_copy_link(match_row['link'], match_row.get('notes', ""))
        
        else:
            # Default Marketplace Logic
            results = df[df['Publisher'] == search_query] if df is not None else pd.DataFrame()
            if not results.empty:
                base_info = results.iloc[0] 
                st.success(f"Marketplace Results for: **{search_query}**")  
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("AS", base_info.get('AS', 'N/A'))
                    c2.metric("DR", base_info.get('DR', 'N/A'))          
                    traffic = base_info.get('Total Organic Traffic', 0)
                    traffic_display = f"{int(traffic):,}" if pd.notna(traffic) and str(traffic).replace('.','').isdigit() else "N/A"
                    c3.metric("Traffic", traffic_display)
                    c4.metric("Top Country", str(base_info.get('Top Country', 'N/A')).upper())        

                l_col, r_col = st.columns(2)
                for col, p_type in zip([l_col, r_col], ['Guest Post', 'Link Insertion']):
                    with col:
                        st.subheader(f"{'📝' if p_type == 'Guest Post' else '🔗'} {p_type}")
                        subset = results[results['Type'].str.contains(p_type, case=False, na=False)]
                        if not subset.empty:
                            row = subset.sort_values('temp_price').iloc[0]
                            with st.container(border=True):
                                seller = row.get('Best Seller 1st', 'N/A')
                                t_col, p_col = st.columns([2, 1])
                                t_col.markdown(f"### 🥇 {seller}")
                                p_col.metric("Price", f"${row.get('Price 1st', 'N/A')}")
                                st.divider()
                                show_platform_link(seller, p_df, csv_link=row.get('Referral Link 1st'))
                        else:
                            st.info(f"No {p_type} found.")
            else:
                st.error(f"No results found for '{search_query}'.")

with tab2:
    st.header("Platform links")
    mode = st.radio("Action", ["Add New", "Edit Existing"], horizontal=True)
    existing_name, existing_link, existing_notes = "", "", ""
    if mode == "Edit Existing" and not p_df.empty:
        target_site = st.selectbox("Select Site to Update", p_df['platform'].tolist())
        row = p_df[p_df['platform'] == target_site].iloc[0]
        existing_name, existing_link = row['platform'], row['link']
        existing_notes = row['notes'] if pd.notna(row['notes']) else ""
    
    with st.form("platform_form", clear_on_submit=(mode == "Add New")):
        col_a, col_b = st.columns(2)
        if mode == "Edit Existing":
            col_a.text_input("Platform/Domain", value=existing_name, disabled=True)
            final_name = existing_name
        else:
            final_name = col_a.text_input("Platform/Domain")
        u_link = col_b.text_input("PitchBox Link", value=existing_link)
        u_notes = st.text_area("Negotiation Notes", value=existing_notes)
        save_btn = st.form_submit_button("Save to Database")
        if save_btn and final_name and u_link:
            result = save_or_update_platform(final_name, u_link, u_notes)
            st.success(f"Successfully {result} {final_name}!")
            st.rerun()
    st.dataframe(p_df, use_container_width=True, hide_index=True)
