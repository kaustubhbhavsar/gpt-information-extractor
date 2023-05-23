<!-- PROJECT NAME -->

<br />
<div align="center">
  <h3 align="center">SLICEMATE</h3>
  <p align="center">
       Thoughts Transformed: Intelligent NLU Unleashed.
  </p>
</div>

<!-- ABOUT PROJECT -->
## What Is It?

<div align="center">

No more forms or button navigation—simply type your mind, and watch as this intelligent application classifies, segments, and archives everything from shopping lists to random ideas.
  
</div>

The purpose entails in the development of a sophisticated Natural Language Understanding (NLU) tool that aims to facilitate the swift extraction, storage, and retrieval of diverse personal information, encompassing shopping or to-do lists, phone numbers, email addresses, names, trivia, reminders, random ideas, and more. The impetus behind this undertaking lies in recognizing the challenges individuals encounter when seeking the appropriate form or navigating through various buttons for each information category. By leveraging this application, users can effortlessly articulate their thoughts via typing, secure in the knowledge that the tool adeptly classifies, segments, and archives the provided data.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- PROJECT SUMMARY -->
## Summary

Slicemate excels in performing two primary tasks:

*  Gathering facts from Natural Language and adding them to a database: GPT-3 can convert spoken or written sentences into well-organized pieces of information, which can then be stored in a database.
*  Searching the database using keywords: GPT-3 can help improve searches by including synonyms and related terms along with the original keywords. This makes the search results more comprehensive and accurate.

Included in the resources are two separate notebooks designed to facilitate prompt engineering studies for <a href='https://github.com/kaustubhbhavsar/gpt-information-extractor/blob/main/notebooks/prompt_engineering_fact_extraction.ipynb'>extracting facts</a> and <a href='https://github.com/kaustubhbhavsar/gpt-information-extractor/blob/main/notebooks/prompt_engineering_querying_facts.ipynb'>searching facts</a>, respectively. These notebooks provide a structured environment for exploring and refining prompt engineering techniques specific to each task.

Within the project files, you will find the <a href='https://github.com/kaustubhbhavsar/gpt-information-extractor/blob/main/src/app.py'>app.py</a> file, which serves as the Streamlit application. This file contains the necessary code to create the user interface and handle the interactions with the application. Additionally, the <a href='https://github.com/kaustubhbhavsar/gpt-information-extractor/blob/main/src/engine.py'>engine.py</a> file houses the main logic and functionalities of the application, providing the underlying implementation and data processing capabilities.

Displayed below are the accompanying screenshots of the Streamlit application, which provide a visual representation of the user interface for both extracting factual information and conducting fact-based searches.

EXTRACT FACTS             |  SEARCH FACTS
:-------------------------:|:-------------------------:
![Extract Facts](https://github.com/kaustubhbhavsar/gpt-information-extractor/blob/main/assets/add_facts.png) | ![Search Facts](https://github.com/kaustubhbhavsar/gpt-information-extractor/blob/main/assets/search_facts.png)


<p align="right">(<a href="#top">back to top</a>)</p>


<!-- Project Directory Structure -->
## Directory Structure
```
├── assets/                                        # assets such as images 
├── config/                                        # configuration files 
├── data/                                          # data files
├── notebooks/                                     # notebooks
├── src/                                           # main code files
    └── app.py                                     # streamlit app
    └── engine.py                                  # app logic
    └── logger.py                                  # logger file 
```

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- Tools and Libraries used -->
## Tools and Libraries

*   Language: <b>Python</b>
*   GPT: <b>OpenAI</b>
*   Web App: <b>Streamlit</b>
*   Other Prominent Libraries: <b>Pandas</b>

The additional libraries utilized, along with the precise versions of each library used, are specified in the <a href="requirements.txt">requirements.txt</a> file.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- Final Notes -->
## Final Notes

Please make sure that you have installed all the necessary dependencies and libraries. You can refer to the requirements.txt file to find a complete list of the required libraries and their versions. The codebase relies on Python version 3.8.16.

Prior to proceeding, please ensure that you possess the OpenAI API key. This key is essential for accessing and utilizing the OpenAI API services.

The codebase has been meticulously documented, incorporating comprehensive docstrings and comments. Please review these annotations, as they provide valuable insights into the functionality and operation of the code.

<p align="right">(<a href="#top">back to top</a>)</p>
