import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv('.env')
from mongo_auth import Authenticate
from utils import *
import webbrowser
import numpy as np
import pandas as pd
import openai
import json
from langchain import PromptTemplate
from langchain import PromptTemplate, LLMChain
from serpapi import GoogleSearch
from langchain.chat_models import ChatOpenAI
import re
from typing import Any
from crossref.restful import Works

# Set Streamlit page configuration
st.set_page_config(page_title="SaaS", page_icon=":house", layout="centered", initial_sidebar_state="auto", menu_items=None)

#Serpapi search
def get_google_results(query, year):
  params = {
    "q":query,
    "engine": "google_scholar",
    "hl": "en",
    "num": "10",
    "as_ylo": year,
    "api_key": os.getenv("SERPAPI_API_KEY")
  }

  search = GoogleSearch(params)
  results = search.get_dict()
  organic_results = results["organic_results"]
  with open('index.json', 'w') as f:
      # write the JSON-formatted organic_results variable to the file
      json_results = json.dump(organic_results, f)
  return json_results

# Extract the fields of interest from each item in the list
def get_results(data):
  results = []
  for item in data:
      position = item['position']
      snippet = item['snippet']
      link = item['link']
      results.append({'position': position, 'snippet': snippet, 'link': link})
  return results

def remove_newlines(text):
    """
    Removes newline characters and empty lines from a string input and returns a continuous string.
    """
    return ' '.join(line.strip() for line in str(text).splitlines() if line.strip())

def display_article_info(output):
    references = re.findall(r'\[(\d+)\]\((.*?)\)', output)

    works = Works()

    for ref in references:
        number, link = ref

        match = re.search(r'(10\.\d{4,9}\/[-._;()\/:A-Z0-9]+)', link, re.IGNORECASE)
        
        if match:  # Check if a match was found
            doi = match.group(1)

            metadata = works.doi(doi)

            if metadata and metadata.get('author'):
                author_names = [f"{author['given']} {author['family']}" for author in metadata['author']]
                authors = ", ".join(author_names)
            else:
                authors = 'Unknown'

            if metadata and 'title' in metadata and len(metadata['title']) > 0:
                title = metadata['title'][0]
            else:
                title = 'Unknown'
        
            # Extract the year from the 'published-print' or 'published-online' field
            if metadata and 'published-print' in metadata:
                year = metadata['published-print']['date-parts'][0][0]
            elif metadata and 'published-online' in metadata:
                year = metadata['published-online']['date-parts'][0][0]
            else:
                year = 'Unknown'

            st.write(f"Number: {number}")
            st.write(f"Year: {year}")
            st.write(f"Title: {title}")
            st.write(f"Author: {authors}")
            st.write(f"DOI/Link: {link}")
        else:
            st.write(f"Number: {number}")
            st.write(f"Reference Link: {link}")
            st.write("DOI not found")
#AI
#def claude_ai(data: Any, query: str) -> str:
   # anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
   # response = anthropic.completions.create(
     #   prompt=f"""{HUMAN_PROMPT}:Using the provided web search from {data}, write a comprehensive reply to the given question: {query}. 
     #                               Make sure to cite results using [[Position](Link)] notation after the reference. No not use more than one notation per reference. 
      #                              If the provided search results refer to multiple subjects with the same name, write separate answers for each subject.
      #                              
      #                              {AI_PROMPT}:""",
       # model="claude-2.0",
       # max_tokens_to_sample='2800',
   # )
    #return response.completion

def openai_ai_4(data: Any, query: str) -> str:
    prompt = PromptTemplate(
                input_variables=["results", "query"], 
                template="""Using the provided web search from {results}, write a comprehensive reply to the given question: {query}. 
                Make sure to cite results using [[Position](Link)] notation after the reference. No not use more than one notation per reference. 
                If the provided search results refer to multiple subjects with the same name, write separate answers for each subject.
                """)
    llm_chain = LLMChain(prompt=prompt, llm=ChatOpenAI(temperature=0, model_name="gpt-4", request_timeout=120), verbose=False)
    output = llm_chain.predict(results=get_results(data), query=query)
    return output

#clean-up
def delete_file(filename: str) -> None:
    try:
        os.remove(filename)
    except FileNotFoundError:
        st.write(f"{filename} not found.")


# Display the main title
st.markdown("# Soroush's App")

# Initialize the authenticator
st.session_state['authenticator'] = Authenticate("coolcookiesd267", "keyd3214", 60)

# Set default session state values if not already set
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'verified' not in st.session_state:
    st.session_state['verified'] = None

# Handle login if not authenticated and not verified
if not st.session_state['authentication_status'] and not st.session_state['verified']:
    st.session_state['authenticator'].login('Login', 'main')
if 'summarized_text' not in st.session_state:
    st.session_state['summarized_text'] = ''
if 'translation' not in st.session_state:
    st.session_state['translation'] = ''
# Handle actions for verified and authenticated users
if st.session_state['verified'] and st.session_state["authentication_status"]:
    st.session_state['authenticator'].logout('Logout', 'sidebar', key='123')

    openai.api_key = os.environ["OPENAI_API_KEY"]

    client = openai.Client(api_key=os.environ["OPENAI_API_KEY"])
    # Check if the user's email is subscribed
    st.session_state['subscribed'] = is_email_subscribed(st.session_state['email'])
    
    # Display subscription status
    if st.session_state.get('subscribed'):
        st.write('You are subscribed!')
    else:
        st.write('You are not subscribed!')



    st.title("SARA")
    st.write("Scholarly Academic Research Assistant")
    st.subheader("Overview")
    st.write("SARA is designed to assist you with academic research by searching for scholarly literature on Google Scholar and answering your research questions. It leverages advanced AI models to provide you with comprehensive, evidence-based answers.")
    #st.divider()
    st.subheader("Steps to Use the Program")
    st.write("""
    - **1. Choose Year Range:**
    There will be a numeric input field asking you to indicate the year from which you'd like the literature to be included. Choose the year range accordingly.
    - **2. Write Your Research Question:**
    You'll see a text box asking you to write your research question or query. Please enter it there.
    - **3. Submit Your Query:**
    After entering your research question, press the "Submit" button to start the search. It will take up to 5 seconds for the program to initiate. 
    - **4. Review Results:**
    Wait for the results to load. This may take a few seconds. Once loaded, you will see a comprehensive answer to your research question, along with references in the notation form [Position].
    - **5. Double-Check References:**
    Always double-check the references provided by SARA for accuracy and relevance to your research question. Never assume the generated references are 100% accurate or relevant.
    - **6. Review References Section:**
    Scroll down to see the "References" section that contains detailed information on each reference used in the answer.
    - **7. Save Information:**
    Make sure to save or copy any relevant information, as the chat history may not be saved for future sessions.
    """)
    st.divider()
    st.subheader("Please provide the following information:")
    year = st.number_input("Please indicate the year from which you want the literature to be included", min_value=1990, step=1, value=2022)
    #ai = st.radio("Please choose your AI model", ['Claude API', 'GPT-4 API'])
    ai = 'GPT-4 API'
    st.divider()
    query = st.text_area("Please write your research question/quarry in the text box.")
    if ai == 'Claude API':
        if st.text_area is not None:
            if st.button("Submit", type="primary"):
                get_google_results(query, year)
                with st.spinner('Wait for it...'):
                    #open json for langchain
                    with open('index.json', 'r') as f:
                        data = json.load(f)
                    #st.markdown(openai_ai(data, query))
                    #output = (claude_ai(data, query))
                    #st.markdown(output)
                    # Convert the output string to a dictionary
                    st.divider()
                    st.subheader("References:")
                    #display_article_info(output)
                    delete_file("index.json")

    else:
        if st.text_area is not None:
            if st.button("Submit", type="primary"):
                if not st.session_state.get('subscribed'):
                    st.error('Please subscribe to use this tool!')
                    st.link_button('Subscribe', os.getenv('STRIPE_PAYMENT_URL'))
                    #webbrowser.open_new_tab()
                else:
                    get_google_results(query, year)
                    with st.spinner('Wait for it...'):
                        #open json for langchain
                        with open('index.json', 'r') as f:
                            data = json.load(f)
                        #st.markdown(openai_ai(data, query))
                        output = (openai_ai_4(data, query))
                        st.markdown(output)
                        # Convert the output string to a dictionary
                        st.divider()
                        st.subheader("References:")
                        display_article_info(output)
                        delete_file("index.json")
    
            st.write(st.session_state['translation'])

# Handle actions for users with correct password but unverified email
elif st.session_state["authentication_status"] == True:
    st.error('Your password was correct, but your email has not been not verified. Check your email for a verification link. After you verify your email, refresh this page to login.')
    
    # Add a button to resend the email verification
    if st.session_state.get('email'):
        if st.button(f"Resend Email Verification to {st.session_state['email']}"):
            resend_verification(st.session_state['email'])

# Handle actions for users with incorrect login credentials
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect or does not exist. Reset login credential or register below.')
    forgot_password()
    register_new_user()

# Handle actions for new users or users with no authentication status
elif st.session_state["authentication_status"] == None:
    st.warning("New to Soroush'SaaS? Register below.")
    register_new_user()
