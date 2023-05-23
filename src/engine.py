import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import config
import io
from src.logger import logging
import openai
import pandas as pd
from pathlib import Path



# --------------------------------------------------------------------------------
# Class Engine
# --------------------------------------------------------------------------------
class Engine:
    """
    The main class of the engine.py. 
    It stores the database and application parameters, as well as coordinates the calls 
    to GPT-3 model, leveraging the preprocessor and postprocessor. 
    """
    def __init__(self, api_key = os.getenv("OPENAI_API_KEY"),
                 database_file_path=Path(config.DATA_DIR, "default_database.csv"),
                 categories_file_path=Path(config.DATA_DIR, "default_categories.csv"),
                 gpt3_engine = "text-davinci-003", gpt3_temperature=0.1,
                 gpt3_frequency_penalty=-0.5, gpt3_presence_penalty=-0.6, 
                 default_categories=["Family", "Work", "Friends", "Shopping", "Health", 
                                     "Finance", "Travel", "Home", "Pets", "Hobbies", "Other"]):
        

        self._database_file_path = database_file_path
        self._categories_file_path = categories_file_path
        self._categories = default_categories

        # load the database or create it from scratch if needed
        try:
            self.database = pd.read_csv(self._database_file_path)
            logging.info(f"Loaded database from {self._database_file_path}.")
        except FileNotFoundError:
            self.database = pd.DataFrame(columns=["Category", "Type", "People", "Key", "Value"])
            self._save()
            logging.info(f"Created database in {self._database_file_path}.")
        

        # load the categories file or create it from scratch if needed
        try:
            df_categories = pd.read_csv(self._categories_file_path)
            self._categories = df_categories["Category"].tolist()
            logging.info(f"Loaded categories {self._categories} from {self._categories_file_path}.")
        except FileNotFoundError:
            self.database = pd.DataFrame(default_categories, columns=["Category"])
            self._save()
            logging.info(f"Created categories {self._categories} in {self._categories_file_path}.")


        openai.api_key = api_key
        self.gpt3_parameters = {"engine": gpt3_engine, "temperature": gpt3_temperature, 
                                "max_tokens":200, "top_p":1.0, "frequency_penalty":gpt3_frequency_penalty, 
                                "presence_penalty":gpt3_presence_penalty, "stop":None}

        self._current_extracted_facts = None

        # create preprocessor and postprocessor for GPT-3 inputs and outputs, respectively
        self._preprocessor = Preprocessor()
        self._postprocessor = Postprocessor()

    def _save(self):
        """
        Saves the current state of the database and allowed categories.

        Parameters:
            None

        Returns:
            None
        """
        logging.info(f"Database has {len(self.database)} facts.")
        logging.info(f"Available categories are {self._categories}")
        
        #os.makedirs(os.path.dirname(self._database_file_path), exist_ok=True)
        self.database.to_csv(self._database_file_path, index=False)
        pd.DataFrame(self._categories, columns=["Category"]).to_csv(self._categories_file_path, index=False)

        logging.info(f"Saved database in {self._database_file_path}.")
        logging.info(f"Saved allowed categories in {self._categories_file_path}.")
        
    # --------------------------------------------------------------------------------
    # Following are the 'Facts Insertion' workflow methods
    # --------------------------------------------------------------------------------

    def extract_facts(self, facts_utterance):
        """
        Extracts facts from a natural language utterance.
        
        Parameters:
            facts_utterance (str): The natural language utterance from which to extract facts.

        Returns:
            A list of tuples (category, type, people, key, value).
        """
        fact_tuples = self._postprocessor.string_to_tuples(self._gpt3_complete(self._preprocessor.extraction_prompt(facts_utterance, self._categories)))
        self._current_extracted_facts = fact_tuples
        return fact_tuples
    
    def has_extracted_facts(self):
        """
        Checks if facts have been extracted.

        Returns:
            True: If facts have been extracted and are available.
            False: If no facts have been extracted or if they have been cleared.
        """
        return self._current_extracted_facts is not None
    
    def extracted_facts(self):
        """
        Returns the current extracted facts as a list of dictionaries.

        Returns:
            A list of dictionaries representing the extracted facts.
        """
        return [{"Category": fact[0], "Type": fact[1], "People": fact[2], "Key": fact[3], "Value": fact[4]} 
                 for fact in self._current_extracted_facts]

    def commit(self):
        """
        Commits the current extracted facts to the database.
       
        Note:
            If no facts have been extracted, the function logs a message indicating that there is 
                nothing to commit.
            The insertion process and database saving are handled by internal methods `_insert_facts`
                and `_save`, respectively.
        """	
        if self._current_extracted_facts is not None:
            self._insert_facts()
            self._current_extracted_facts = None
            self._save()
        else:
            logging.info("Nothing to commit.")
    
    def cancel(self):
        """
        Cancel the current extracted facts.
        
        Note:
            If no facts have been extracted, the function logs a message indicating that there is 
                nothing to revert.
        """	
        if self._current_extracted_facts is not None:
            self._current_extracted_facts = None
        else:
            logging.info("Nothing to revert.")

    def _insert_facts(self, facts_utterance = None):
        """
        Inserts a fact into the database.

        Parameters:
            facts_utterance (str, optional): The natural language utterance from which to extract facts. 
                Default is None.
        """
        # reuse the extracted facts, if any
        if self._current_extracted_facts is None:
            fact_tuples = self.extract_facts(facts_utterance)
        else:
            fact_tuples = self._current_extracted_facts
            
        for fact_tuple in fact_tuples:
            logging.info(f"Database has {len(self.database)} facts before insertion.")
            logging.info(f"Inserting fact: {fact_tuple}")
            
            df_to_add = pd.DataFrame([fact_tuple], columns=["Category", "Type", "People", "Key", "Value"])
            self.database = pd.concat([self.database, df_to_add], ignore_index=True)
            logging.info(f"Database has {len(self.database)} facts after insertion.")


    # --------------------------------------------------------------------------------
    # Following are the 'Search' workflow methods
    # --------------------------------------------------------------------------------
    def query(self, fact_query, categories=None, entry_types=None, people=None, show_none_if_no_query=False, verbose=False):
        """
        Queries the database for a fact.

        Parameters:
            fact_query (str): The specific fact query to search for in the database.
            categories (list, optional): A list of categories to filter the search results. 
                Default is None.
            entry_types (list, optional): A list of entry types to filter the search results. 
                Default is None.
            people (list, optional): A list of people associated with the facts to filter the search 
                results. Default is None.
            show_none_if_no_query (bool, optional): Flag to indicate whether to return an empty 
                result if no fact query is provided. If False, it returns the entire filtered database. 
                Default is False.
            verbose (bool, optional): Flag to enable verbose output for the intermediate steps of the 
                query process. Default is False.

        Returns:
            If a fact query is provided or `show_none_if_no_query` is True:
                It returns the search result as a filtered DataFrame based on the specified parameters 
                and the terms extracted and augmented from the fact query.
            If no fact query is provided and `show_none_if_no_query` is False:
                It returns the filtered database without performing any additional search or 
                term extraction.
        """
        if len(fact_query) > 0 or show_none_if_no_query:
            raw_original_terms = self._gpt3_complete(self._preprocessor.terms_extraction_prompt(fact_query))
            original_terms = self._postprocessor.extract_lines_from_result(raw_original_terms)
            if verbose:
                logging.info(f"Original Terms: {original_terms}")

            augmented_terms = []
            for original_term in original_terms:
                raw_augmented_terms = self._gpt3_complete(self._preprocessor.terms_augmentation_prompt(original_term))
                augmented_terms += self._postprocessor.extract_lines_from_result(raw_augmented_terms)
            if verbose:
                logging.info(f"Augmented Terms: {augmented_terms}")
            
            return self._search_dataframe(self._database_filtered_by(categories, entry_types, people),
                                        original_terms, augmented_terms)
        else:
            return self._database_filtered_by(categories, entry_types, people)

    def _search_dataframe(self, df, original_terms, augmented_terms):
        """
        Searches the specified database for the specified terms.

        Parameters:
            df (pandas.DataFrame): The database to search in.
            original_terms (list): The original terms extracted from the query.
            augmented_terms (list): The augmented terms extracted from the query.

        Returns:
            A new DataFrame containing the rows from the specified database (`df`) that 
            match any of the original or augmented terms.
        """
        df = df.fillna("") # for readability below
        all_terms = original_terms + augmented_terms

        df_results = None
        for column in df.columns:
            df_result = df[df[column].str.contains("|".join(all_terms), case=False).fillna(False)]
            if df_results is None:
                df_results = df_result
            else:
                df_results = pd.concat([df_results, df_result])
        
        return df_results


    def _database_filtered_by(self, categories=None, entry_types=None, people=None):
        """
        Filters the main database based on the specified categories, entry types, and people.

        Parameters:
            categories (list, optional): A list of categories to filter the database. Default is None.
            entry_types (list, optional): A list of entry types to filter the database. Default is None.
            people (list, optional): A list of people to filter the database. Default is None.

        Returns:
            A new DataFrame that contains the filtered rows based on the specified categories, 
            entry types, and people.
        """
        df = self.database

        def aux_filter(df, column, values):
            if values is not None and len(values) > 0:
                return df[self.database[column].str.lower().isin([v.lower() for v in values])]
            else:
                return df
        
        df = aux_filter(df, "Category", categories)
        df = aux_filter(df, "Type", entry_types)
        df = aux_filter(df, "People", people)
        return df
    
    def unique_categories_in_database(self):
        """
        Returns a list of unique categories present in the database.

        Returns:
            A list of unique categories present in the database.
        """
        return self.database["Category"].unique().tolist()
    
    def unique_entry_types_in_database(self):
        """
        Returns a list of unique entry types present in the database.

        Returns:
            A list of unique entry types present in the database.
        """
        return self.database["Type"].unique().tolist()
        
    def unique_people_in_database(self):
        """
        Returns a list of unique people present in the database.

        Returns:
            A list of unique people present in the database.
        """
        return self.database["People"].unique().tolist()

    # --------------------------------------------------------------------------------
    # Following are the methods for 'Categories' management
    # --------------------------------------------------------------------------------
    def allowed_categories(self):
        """
        Returns a list of allowed categories.
        
        Returns:
            A list of allowed categories.
        """
        return self._categories

    def update_categories(self, new_categories):
        """
        Updates the allowed categories with the specified new categories.
        
        Parameters:
            new_categories (list): The new categories to be set as the allowed categories.
        """
        self._categories = new_categories
        self._save()


    # --------------------------------------------------------------------------------
    # Following are the methods for GPT-3 API
    # --------------------------------------------------------------------------------
    def _gpt3_complete(self, prompt, echo=False):
        """
        Completes a prompt using the GPT-3 model.

        Parameters:
            prompt (str): The prompt to be completed.
            echo (bool, optional): Specifies whether to include the prompt in the completion text. 
                Default is False.

        Returns:
            The completion text generated by the GPT-3 model.
        """
        response = openai.Completion.create(
            engine=self.gpt3_parameters["engine"],
            prompt=prompt,
            temperature=self.gpt3_parameters["temperature"],
            max_tokens=self.gpt3_parameters["max_tokens"],
            top_p=self.gpt3_parameters["top_p"],
            frequency_penalty=self.gpt3_parameters["frequency_penalty"],
            presence_penalty=self.gpt3_parameters["presence_penalty"],
            stop=self.gpt3_parameters["stop"],
            echo=echo
        )
        completion = response['choices'][0]['text']
        return completion

    def set_openai_api_key(self, key):
        """
        Sets the OpenAI API key for authentication.

        Parameters:
            key (str): The OpenAI API key to be set for authentication.
        """
        openai.api_key = key    
    
    # --------------------------------------------------------------------------------
    # Following are the 'Data' utilities
    # --------------------------------------------------------------------------------
    def export_data_to_binary(self, df, file_type=None):
        """
        Exports a DataFrame to binary format based on the specified file type.

        Parameters:
            df (pandas.DataFrame): The DataFrame to be exported.
            file_type (str, optional): The file type for the export. Default is None.

        Returns:
            The binary representation of the exported data.
        """
        if file_type is None:
            file_type = "excel"
        
        if file_type == "excel":
            memory_output = io.BytesIO()
            with pd.ExcelWriter(memory_output) as writer:  
                df.to_excel(writer)
            return memory_output

        elif file_type == "csv":
            return df.to_csv().encode('utf-8')
        
        elif file_type == "tsv":
            return df.to_csv(sep='\t').encode('utf-8')
        
        else:
            raise ValueError("Invalid file type.")



# --------------------------------------------------------------------------------
# Class Preprocessor
# --------------------------------------------------------------------------------
class Preprocessor:
    """
    Preprocessor for the user input to GPT-3. Notably, includes the mechanisms to build prompts.
    """
    def extraction_prompt(self, x, categories):
        """
        Generates an extraction prompt for extracting pieces of personal information.

        Parameters:
            x (str): The input sentence or text.
            categories (list): A list of allowed categories.

        Returns:
            str: The generated extraction prompt.
        """
        prompt = \
f"""
You are tasked with extracting pieces of personal information from various inputs, such as phone numbers, email addresses, names, trivia, reminders, etc. Your goal is to extract and categorize these pieces of information into structured tuples.
Extract the information as tuples with the following format: (Category, Type, People, Key, Value). 
Assume everything mentioned refers to the same thing. 
The extracted information should be categorized according to the allowed categories and types specified below.

Constraints:
  - Allowed Categories: {', '.join(categories)}
  - Allowed Types: "List", "Email", "Phone", "Address", "Document", "Pendency", "Price", "Reminder", "Note", "Doubt", "Wish", "Other"
  - People contain the name or description of the people or organizations concerned, or is empty if no person or organization is mentioned.
  
Example input: "Mom's phone number is 555-555-5555"
Example output: ("Family", "Phone", "mom", "mom's number", "555-555-5555")

Example input: "email of the building administration = adm@example.com"
Example output: ("Work", "Email", "building administration", "email", "adm@example.com")

Example input: "Need to do: lab work, ultrasound, buy aspirin"
Example output: 
("Health", "List", "Self", "to do", "lab work")
("Health", "List", "Self", "to do", "ultrasound")
("Shopping", "List", "Self", "aspirin", "buy")	

Example input: event support: we failed :-(
Example output: 
("Other", "Note", "event support", "failed", "we failed :-(")

Example input: first aid kit in the reception
Example output:
("Home", "Note", "", "first aid kit", "reception")

Example input: december receipts for gym: yoga, ballet, ??
Example output:
("Finance", "Document", "gym", "december receipts", "yoga")
("Finance", "Document", "gym", "december receipts", "ballet")
("Finance", "Document", "gym", "december receipts", "??")

Input: {x}
Output: 
"""
        logging.info(f"GPT-3 Prompt: {prompt}")
        return prompt 

    def terms_extraction_prompt(self, query):
        """
        Generates a prompt for extracting main entities from a sentence.

        Parameters:
            query (str): The input sentence.

        Returns:
            str: The generated extraction prompt.
        """
        prompt = \
f"""
Extract the main entities (one per line, without bullets) in the following sentence: "{query}"
"""
        logging.info(f"GPT-3 Prompt: {prompt}")
        return prompt

    def terms_augmentation_prompt(self, term):
        """
        Generates a prompt for augmenting terms with synonyms.

        Parameters:
            term (str): The term for which synonyms are needed.

        Returns:
            str: The generated augmentation prompt.
        """
        prompt = \
f"""
List some synonyms for the following term: "{term}"
Synonyms (one synonym per line):
"""
        logging.info(f"GPT-3 Prompt: {prompt}")
        return prompt
    


# --------------------------------------------------------------------------------
# Class Postprocessor
# --------------------------------------------------------------------------------
class Postprocessor:
    """
    Postprocessor for the GPT-3 raw outputs.
    """
    def extract_lines_from_result(self, result):
        """
        Extracts the lines from the result string.

        Parameters:
            result (str): The result string from which to extract lines.

        Returns:
            list: A list of extracted lines, with leading and trailing whitespace and hyphens removed.
        """
        lines = [line.strip(' -*') for line in result.split('\n') if len(line) > 0]
        return lines

    def string_to_tuples(self, s):
        """"
        Converts a string that looks like a tuple to an actual Python tuple.

        Parameters:
            s (str): The string to convert.

        Returns:
            list: A list of Python tuples created from the input string.
        """
        return [eval(s.strip()) for s in self.extract_lines_from_result(s)]

    def extract_terms_from_all_results(self, results):
        """
        Extracts the terms from the result string.

        Parameters:
            results (list): A list of result strings from which to extract terms.

        Returns:
            list: A list of lists, where each inner list contains the extracted terms from a result string.
        """
        terms = []
        for result in results:
            terms.append(self.extract_lines_from_result(result))
        return terms