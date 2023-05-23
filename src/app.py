import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from engine import Engine
import openai
import streamlit as st

  
def app():
    # some stateful variables
    if 'latest_insertions' not in st.session_state:
        st.session_state['latest_insertions'] = None
    if 'insertion_cancelled' not in st.session_state:
        st.session_state['insertion_cancelled'] = False
    
    # allowed categories
    all_categories = ["Family", "Work", "Friends", "Shopping", "Health", "Finance", "Travel", "Home", "Pets", "Hobbies", "Reminders",
                      "Ideas", "Email", "Phone", "Address", "Other"]
    default_categories = ["Family", "Work", "Friends", "Shopping", "Ideas", "Health", "Other"]

    # setup the engine
    #@st.cache_data
    @st.cache_resource
    def create_engine():
        return Engine(default_categories=default_categories)
    engine = create_engine()   

    
    st.markdown("<h1 style='text-align: center; color: black;'>SLICEMATE</h1>", unsafe_allow_html=True)
    st.markdown("<h6 style='text-align: center; color: black;'>Dump, Retrieve, and Explore your world of facts, reminders, purchases, prices, notes and more!</h1>", unsafe_allow_html=True)
    
    # --------------------------------------------------------------------------------
    # Sidebar
    # -------------------------------------------------------------------------------- 
    # get the OpenAI API key, wither from the OPENAI_API_KEY environment variable or from user input.
    st.sidebar.header("Parameters")

    token = st.sidebar.text_input('OpenAI API access token', 
                                openai.api_key if openai.api_key is not None else '', 
                                type='password',
                                help='Get it on https://beta.openai.com/')

    #engine.gpt3_parameters["engine"] = st.sidebar.text_input("GPT3 Engine", "text-davinci-003")
    #engine.gpt3_parameters["temperature"] = st.sidebar.slider("GPT3 Temperature", value=0.1, min_value=0.0, max_value=1.0, step=0.1)

    selected_categories = st.sidebar.multiselect('Possible categories to consider when adding facts', 
                                                  all_categories,
                                                  engine.allowed_categories())


    engine.update_categories(selected_categories)
    engine.set_openai_api_key(token)


    # different tabs for searching and for data insertion
    tab1, tab2 = st.tabs(["Search facts", "Add facts"])

    # --------------------------------------------------------------------------------
    # Search facts tab
    # --------------------------------------------------------------------------------
    with tab1:
        
        query = st.text_input('Query', '', help='Type a few keywords to query.')
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            categories_filter = st.multiselect(
                                    'Filter by Category:',
                                    engine.unique_categories_in_database(),
                                    [])
        with filter_col2:
            entry_types_filter = st.multiselect(
                                        'Filter by Type:',
                                        engine.unique_entry_types_in_database(),
                                        [])
        with filter_col3:
            people_filter = st.multiselect(
                                        'Filter by People:',
                                        engine.unique_people_in_database(),
                                        [])

        
        
        df_results = engine.query(query, 
                                  categories=categories_filter, 
                                  entry_types=entry_types_filter, 
                                  people=people_filter)
        st.subheader("Results")
        st.dataframe(df_results, use_container_width=True)

        # download results 
        st.caption("You can download this view of the data as a CSV, TSV or Excel file.")

        download_col1, download_col2, download_col3 = st.columns(3)
        with download_col1:
            generate_excel_download = st.button("Generate downloadable Excel")
        with download_col2:
            generate_csv_download = st.button("Generate downloadable CSV")
        with download_col3:
            generate_tsv_download = st.button("Generate downloadable TSV")
        
        def export_selected_data(file_type):
            return engine.export_data_to_binary(df_results, file_type=file_type)

        if generate_csv_download:
            st.download_button("Download this beautiful data!", 
                                        data=export_selected_data(file_type="csv"),
                                        file_name="out.csv",
                                        mime='text/csv')
        if generate_tsv_download:
            st.download_button("Download this beautiful data!", 
                                        data=export_selected_data(file_type="tsv"),
                                        file_name="out.tsv",
                                        mime='text/tsv')

        if generate_excel_download:
            st.download_button("Download this beautiful data!", 
                                        data=export_selected_data(file_type="excel"),
                                        file_name="out.xlsx",
                                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
    # --------------------------------------------------------------------------------
    # Insert facts tab
    # --------------------------------------------------------------------------------
    with tab2:
        st.text("Type your facts, reminders, purchases, etc.")
        with st.form("new_facts_form", clear_on_submit=True):
            new_facts_utterance = st.text_input('New Facts', '', help='Write your facts here.')
            add_facts = st.form_submit_button("Add facts")

        manual_check = st.checkbox("Check before adding", value=False)

        # placeholder for where the manual check pane will be
        manual_check_pane = st.empty() 
        
        # auxiliary function to commit extraction, will be used more than once below
        def aux_commit_extraction():
            st.session_state['latest_insertions'] = engine.extracted_facts()
            engine.commit()
            

        # EXTRACT: If we don't have extracted facts yet, let's try to do that.
        if not engine.has_extracted_facts():
            if add_facts:
                engine.extract_facts(new_facts_utterance)

        
        # COMMIT: If now we have the extracted facts, prepare to commit or commit them directly.
        if engine.has_extracted_facts():

            # does the user wants to manually check the extracted facts?
            if manual_check:
                with manual_check_pane.container():
                    accept = st.button("Accept fact extraction")
                    cancel = st.button("Cancel fact extraction")
                    st.write("Extracted facts:")
                    st.write(engine.extracted_facts())

                    if accept:
                        aux_commit_extraction()
                        
                    elif cancel:
                        engine.cancel()
                        st.session_state['insertion_cancelled'] = True

            else: # no manual check needed, let's just commit
                aux_commit_extraction()

            
                

    # --------------------------------------------------------------------------------
    # Status messages           
    # -------------------------------------------------------------------------------- 
    if st.session_state['latest_insertions']  is not None:
        st.success(f"Added {st.session_state['latest_insertions']}.")
        st.session_state['latest_insertions'] = None
        manual_check_pane.empty()
    elif st.session_state['insertion_cancelled'] == True:
        st.info("Insertion cancelled.")
        st.session_state['insertion_cancelled'] = False
        manual_check_pane.empty()
    

if __name__ == '__main__':
    app()