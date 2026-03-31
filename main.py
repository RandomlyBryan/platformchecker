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
        # Update existing
        p_df.loc[p_df['platform'].str.lower() == name_clean.lower(), ['link', 'notes']] = [link.strip(), notes.strip()]
        p_df.to_csv(path, index=False)
        return "updated"
    else:
        # Add new
        updated_df = pd.concat([p_df, new_row], ignore_index=True)
        updated_df.to_csv(path, index=False)
        return "added"

def show_copy_link(link, notes=None):
    if notes and str(notes).strip() and str(notes).lower() != 'nan':
        st.warning(f"📝 **Negotiation Notes:** {notes}")
    st.write("📋 **Copy Link:**")
    st.code(link, language=None)
    st.link_button("Open Dashboard", link, use_container_width=True)

def show_platform_link(seller_name, p_df):
    name_clean = str(seller_name).lower().strip()
    match = p_df[p_df['platform'].str.lower().apply(lambda x: x in name_clean if pd.notna(x) else False)]
    if not match.empty:
        row = match.iloc[0]
        show_copy_link(row['link'], row.get('notes', ""))
    else:
        st.caption("No dashboard link mapped for this seller.")

# --- DATA LOADING ---
df = load_all_data() # Assuming the load_all_data function from previous steps is present
p_df = load_platforms()

tab1, tab2 = st.tabs(["🔍 Search Portal", "⚙️ Manage Platforms"])

with tab1:
    st.sidebar.header("Search Filters")
    with st.sidebar.form("search_form"):
        raw_input = st.text_input("Enter Domain or URL").strip()
        submit_button = st.form_submit_button("Go 🔍", use_container_width=True)

    if raw_input:
        search_query = extract_domain(raw_input)
        direct_match = p_df[p_df['platform'].str.lower() == search_query]
        
        if not direct_match.empty:
            st.success(f"Direct Negotiated Match Found: **{search_query}**")
            with st.container(border=True):
                st.subheader("🤝 Negotiated")
                match_row = direct_match.iloc[0]
                show_copy_link(match_row['link'], match_row.get('notes', ""))
        else:
            # Standard CSV search logic follows here...
            st.info("Searching CSV database...") 
            # (Insert previous CSV search results logic here)

with tab2:
    st.header("Manage Negotiated Sites & Platforms")
    
    # --- UPDATE/EDIT SECTION ---
    mode = st.radio("Action", ["Add New", "Edit Existing"], horizontal=True)
    
    existing_name = ""
    existing_link = ""
    existing_notes = ""
    
    if mode == "Edit Existing" and not p_df.empty:
        target_site = st.selectbox("Select Site to Update", p_df['platform'].tolist())
        row = p_df[p_df['platform'] == target_site].iloc[0]
        existing_name = row['platform']
        existing_link = row['link']
        existing_notes = row['notes'] if pd.notna(row['notes']) else ""
    
    with st.form("platform_form", clear_on_submit=(mode == "Add New")):
        col_a, col_b = st.columns(2)
        
        # If editing, name is read-only to maintain database integrity
        if mode == "Edit Existing":
            u_name = col_a.text_input("Platform/Domain", value=existing_name, disabled=True)
            # We use the disabled value for the update logic
            final_name = existing_name
        else:
            final_name = col_a.text_input("Platform/Domain (e.g. adsy.com)")
            
        u_link = col_b.text_input("Direct Dashboard Link", value=existing_link)
        u_notes = st.text_area("Negotiation Notes", value=existing_notes)
        
        submit_lbl = "Update Platform" if mode == "Edit Existing" else "Save to Database"
        save_btn = st.form_submit_button(submit_lbl)
        
        if save_btn and final_name and u_link:
            result = save_or_update_platform(final_name, u_link, u_notes)
            if result == "updated":
                st.success(f"Updated {final_name} successfully!")
            else:
                st.success(f"Added {final_name} to database!")
            st.rerun()

    st.divider()
    st.subheader("Current Database")
    st.dataframe(p_df, use_container_width=True, hide_index=True)
