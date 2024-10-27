from typing import Any, Dict, List, Optional
import snowflake
import pandas as pd
import requests
import snowflake.connector
import streamlit as st
from deep_translator import GoogleTranslator  # Translation library
from bs4 import BeautifulSoup

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600&display=swap" rel="stylesheet">
    <style>
    body {
        font-family: 'Roboto', sans-serif;
    }
    .stChatMessage {
        font-family: 'Roboto', sans-serif;
    }
    /* Hide Streamlit default menu, footer, and header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Optional: Customize background color */
     .reportview-container {
        background-color: #F7F7F7;  /* Set background color */
    }
    .stTextInput, .st-emotion-cache-1f3w014 {
        background-color: #F40000;  /* Input and button background */
        color: #FFFFFF;  
        border-radius: 70%;
       padding-left: 4px;            /* Text color */
    }
    .stMainBlockContainer {
      /*  background-color: #F7F7F7;  */
    }
    /* Assistant message container (aligned left) */
    .assistant-message-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-bottom: 15px;
    }
    /* Assistant header: icon and name */
    .assistant-header {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .assistant-icon {
        margin-right: 5px;
        font-size: 24px;
    }
    .assistant-name {
        font-weight: 600;
        font-size: 14px;
        color: #333333;
    }
    /* Assistant message styling */
    .assistant-message {
        background: #FFFFFF 0% 0% no-repeat padding-box;
        box-shadow: -1px 1px 10px #E2E2E229;
        border: 0.5px solid #dbd1d1;
        border-radius: 0px 10px 10px 10px;
        opacity: 1;
        padding: 10px;
        text-align: left;
        font: normal normal medium 14px/20px 'Poppins', sans-serif;
        letter-spacing: 0px;
        color: #333333;
        max-width: 80%;
        word-wrap: break-word;
    }
    /* User message container (aligned right) */
    .user-message-container {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        margin-bottom: 15px;
    }
    /* User header: name and icon */
    .user-header {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .user-name {
        font-weight: 600;
        font-size: 14px;
        color: #black;
        margin-right: 5px;
    }
    .user-icon {
        font-size: 24px;
    }
    /* User message styling */
    .user-message {
        background: #FFF8F8 0% 0% no-repeat padding-box;
        box-shadow: -1px 1px 10px #E2E2E229;
        border: 0.5px solid #FF9090;
        border-radius: 10px 10px 0px 10px;
        opacity: 1;
        padding: 10px;
        text-align: left;
        font: normal normal medium 14px/20px 'Poppins', sans-serif;
        letter-spacing: 0px;
        color: #F40000;
        max-width: 80%;
        word-wrap: break-word;
    }
     /* Custom style for the chat input area */
    .stChatInput {
        background: #FFFFFF 0% 0% no-repeat padding-box;
        opacity: 1;
    }
    /* Custom style for the submit button */
    .stChatInputSubmitButton {
        background: #F40000 0% 0% no-repeat padding-box;
        opacity: 1;
    }
     .stRadio{
        border: 2px solid #d71c1c;  /* Green border */
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .stRadio label {
        font-weight: bold;
        color: #eb1921;  /* Black text */
    }
    .stSidebar,.stSidebarCollapsedControl,
     {
       display:none;
    }
    .stExpander p 
    {
    fornt-weight:bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)



def load_svg(svg_filename):
    with open(svg_filename, "r") as file:
        return file.read()

# Load assistant and user icons from their respective SVG files
assistant_svg = load_svg("assets/chatbot.svg")
user_svg = load_svg("assets/user.svg")

icons = {
    "assistant": assistant_svg,  # Loaded chatbot SVG
    "user": user_svg             # Loaded user SVG
}


# Define the greeting message
# Define the greeting message in English and Spanish
# GREETING_MESSAGE_EN = {"role": "assistant", "content": "Hello! Welcome to QueryXpert AI. How can I assist you today?"}
# GREETING_MESSAGE_ES = {"role": "assistant", "content": "¡Hola! Bienvenido a QueryXpert AI. ¿En qué puedo ayudarte hoy?"}

GREETING_MESSAGE_EN =  "Hello! Welcome to QueryXpert AI. How can I assist you today?"
# GREETING_MESSAGE_ES = {"role": "assistant", "content": "¡Hola! Bienvenido a QueryXpert AI. ¿En qué puedo ayudarte hoy?"}

# Retrieve Snowflake credentials from secrets
HOST = st.secrets["SF_Dinesh2012"]["host"]
DATABASE = st.secrets["SF_Dinesh2012"]["database"]
SCHEMA = st.secrets["SF_Dinesh2012"]["schema"]
STAGE = st.secrets["SF_Dinesh2012"]["stage"]
FILE = st.secrets["SF_Dinesh2012"]["file"]

# Establish connection only if not already present in session state
if 'CONN' not in st.session_state or st.session_state.CONN is None:
    st.session_state.CONN = snowflake.connector.connect(
        user=st.secrets["SF_Dinesh2012"]["user"],
        password=st.secrets["SF_Dinesh2012"]["password"],
        account=st.secrets["SF_Dinesh2012"]["account"],
       # host=HOST,
       # port=443,
        warehouse=st.secrets["SF_Dinesh2012"]["warehouse"],
        role=st.secrets["SF_Dinesh2012"]["role"]
    )


def sanitize_chatbot_response(response):
    """
    Use BeautifulSoup to parse and clean the HTML response, ensuring
    that unmatched closing tags or extra tags are removed.
    """
    try:
        # Parse the response as HTML using BeautifulSoup
        soup = BeautifulSoup(response, "html.parser")
        
        # Extract text content if needed, removing any excessive HTML tags
        cleaned_response = soup.prettify()  # Optionally, can use soup.get_text() for plain text
        
        return cleaned_response
    except Exception as e:
        # If there's an error, return the raw response
        return response

def send_message(prompt: str) -> Dict[str, Any]:
    """Calls the REST API and returns the response."""
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "semantic_model_file": f"@{DATABASE}.{SCHEMA}.{STAGE}/{FILE}",
    }
    resp = requests.post(
        url=f"https://{HOST}/api/v2/cortex/analyst/message",
        json=request_body,
        headers={
            "Authorization": f'Snowflake Token="{st.session_state.CONN.rest.token}"',
            "Content-Type": "application/json",
        },
    )
    request_id = resp.headers.get("X-Snowflake-Request-Id")
    if resp.status_code < 400:
        return {**resp.json(), "request_id": request_id}  # type: ignore[arg-type]
    else:
        st.session_state.messages.pop()
        raise Exception(
            f"Failed request (id: {request_id}) with status {resp.status_code}: {resp.text}"
        )

if "icons" not in st.session_state:
    st.session_state.icons = {
        "assistant": assistant_svg,
        "user": user_svg
    }

def display_message_with_icon(role: str, message: str):
    if role == "assistant":
        # Assistant message container
        with st.container():
            st.markdown(f"""
                <div class="assistant-message-container">
                    <div class="assistant-header">
                        <span class="assistant-icon">{st.session_state.icons[role]}</span>
                        <span class="assistant-name">QueryXpert AI</span>
                    </div>
                    <div class="assistant-message">{message}</div>
                </div>
                """, unsafe_allow_html=True)
            st.session_state.messages.append(
                {"role": "assistant", "content": [{"type": "text", "text": message}]})
            
    else:
        # User message container
        with st.container():
            st.markdown(f"""
                <div class="user-message-container">
                    <div class="user-header">
                        <span class="user-name">You</span>
                        <span class="user-icon">{st.session_state.icons[role]}</span>
                    </div>
                    <div class="user-message">{message}</div>
                </div>
                """, unsafe_allow_html=True)

def process_message(prompt: str) -> None:
    """Processes a message and adds the response to the chat."""
    # st.session_state.messages.append(
    #     {"role": "user", "content": [{"type": "text", "text": prompt}]}
    # )
    # with st.chat_message("user"):
    #     st.markdown(prompt)

        # Define user and assistant icons
    user_icon = st.session_state.icons["user"]
    assistant_icon = st.session_state.icons["assistant"]
    
    # Create the HTML for the user message with icon
    user_message_html = f'''
                <div class="user-message-container">
                    <div class="user-header">
                        <span class="user-name">You</span>
                        <span class="user-icon">{user_icon}</span>
                    </div>
                    <div class="user-message">{prompt}</div>
                </div> '''


    # Append user message to session state and display it
    st.session_state.messages.append(
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    )
    st.markdown(user_message_html, unsafe_allow_html=True)
    # with st.chat_message("assistant"):

    with st.spinner("Generating response..."):
            response = send_message(prompt=prompt)
            content = response["message"]["content"]
            display_content(content=content)

    st.session_state.messages.append({"role": "assistant", "content": content})

# def process_message(prompt: str) -> None:
#     """Processes a message and adds the response to the chat with icons, using custom HTML formatting."""
    
#     # Define user and assistant icons
#     user_icon = st.session_state.icons["user"]
#     assistant_icon = st.session_state.icons["assistant"]
    
#     # Create the HTML for the user message with icon
#     user_message_html = f'''
#     <div style="display: flex; align-items: center; margin-bottom: 10px;">
#         <span class="user-icon" style="margin-right: 8px;">{user_icon}</span>
#         <div style="background-color: #e1f5fe; padding: 10px; border-radius: 10px; max-width: 80%;">
#             {prompt}
#         </div>
#     </div>
#     '''
    
#     # Append user message to session state and display it
#     st.session_state.messages.append(
#         {"role": "user", "content": [{"type": "text", "text": prompt}]}
#     )
#     st.markdown(user_message_html, unsafe_allow_html=True)
    
#     # Generate assistant's response and prepend icon
#     with st.spinner("Generating response..."):
#         response = send_message(prompt=prompt)
#         content = response["message"]["content"]
        
#         # Create the HTML for the assistant message with icon
#         # assistant_message_html = f'''
#         # <div style="display: flex; align-items: center; margin-bottom: 10px;">
#         #     <span class="assistant-icon" style="margin-right: 8px;">{assistant_icon}</span>
#         # '''
        
#         # Call display_content to process the content
#         processed_content = display_content(content)
        
#         # Continue building the assistant message HTML
#         # assistant_message_html += f'''
#         #     <div style="background-color: #f1f8e9; padding: 10px; border-radius: 10px; max-width: 80%;">
#         #         {processed_content}
#         #     </div>
#         # </div>
#         # '''
    
#     # Append assistant message to session state and display it
#     st.session_state.messages.append(
#         {"role": "assistant", "content": [{"type": "text", "text": content}]}
#     )
#     #st.markdown(assistant_message_html, unsafe_allow_html=True)


def display_content(content: list, message_index: int = None) -> None:
    """Displays a content item for a message."""
    message_index = message_index or len(st.session_state.messages)-1
    # st.write(len(st.session_state.messages))
    # st.write(message_index)
    # st.write(content)
    for item in content:
        if item["type"] == "text" :
            # Display the assistant's message with an icon
            # st.write(message_index) # 5
            # st.write(len(st.session_state.messages))  # 6
            if message_index < len(st.session_state.messages)-1 and st.session_state.messages[message_index]["role"] == "user":
               user_icon = st.session_state.icons["user"]
               #st.write(st.session_state.messages[message_index]["role"])
               user_message_html = f'''
                <div class="user-message-container">
                    <div class="user-header">
                        <span class="user-name">You</span>
                        <span class="user-icon">{user_icon}</span>
                    </div>
                    <div class="user-message">{item["text"]}</div>
                </div>                
                '''
               st.markdown(user_message_html, unsafe_allow_html=True)
            else: # st.session_state.messages[message_index]["role"] == "assistant" :
                
                sanitized_response = sanitize_chatbot_response(item["text"])
                # Display the user's message with an icon               
                assistant_icon = st.session_state.icons["assistant"]
                assistant_message_html = f'''
                  <div class="assistant-message-container">
                    <div class="assistant-header">
                        <span class="assistant-icon">{assistant_icon}</span>
                        <span class="assistant-name">QueryXpert AI</span>
                    </div>
                    <div class="assistant-message">{sanitized_response}</div>
                </div>

                '''
                st.markdown(assistant_message_html, unsafe_allow_html=True)

        elif item["type"] == "suggestions":
            #st.markdown("<h3 style='color: blue; font-weight: bold;font-size:14px;'>Suggestions</h3>", unsafe_allow_html=True)
            with st.expander("suggestions", expanded=True):
                for suggestion_index, suggestion in enumerate(item["suggestions"]):
                    if st.button(suggestion, key=f"{message_index}_{suggestion_index}"):
                        st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            with st.expander("SQL Query", expanded=False):
                st.code(item["statement"], language="sql")
            with st.expander("Results", expanded=True):
                with st.spinner("Running SQL..."):
                    df = pd.read_sql(item["statement"], st.session_state.CONN)

                    if len(df.index) > 1:
                        data_tab, line_tab, bar_tab = st.tabs(
                            ["Data", "Line Chart", "Bar Chart"]
                        )
                        data_tab.dataframe(df)

                        # Ensure you are only using numeric columns for plotting
                        numeric_columns = df.select_dtypes(include=["float", "int"]).columns
                        #date_columns = [col for col in df.columns if "date" in col.lower() or "month" in col.lower() or "year" in col.lower()]

                        if len(numeric_columns) > 0:
                            df = df.set_index(df.columns[0])  # Use first column as index

                            with line_tab:
                                st.line_chart(df[numeric_columns])  # Plot only numeric columns

                            with bar_tab:
                                st.bar_chart(df[numeric_columns])  # Plot only numeric columns
                        else:
                            st.warning("No numeric columns available for plotting.")
                    else:
                        st.dataframe(df)


# def display_content(content: list, message_index: int = None) -> None:
#     """Displays a content item for a message."""
#     message_index = message_index or len(st.session_state.messages)
#     for item in content:
#         if item["type"] == "text":
#             st.markdown(item["text"])
#         elif item["type"] == "suggestions":
#             with st.expander("Suggestions", expanded=True):
#                 for suggestion_index, suggestion in enumerate(item["suggestions"]):
#                     if st.button(suggestion, key=f"{message_index}_{suggestion_index}"):
#                         st.session_state.active_suggestion = suggestion
#         elif item["type"] == "sql":
#             with st.expander("SQL Query", expanded=False):
#                 st.code(item["statement"], language="sql")
#             with st.expander("Results", expanded=True):
#                 with st.spinner("Running SQL..."):
#                     df = pd.read_sql(item["statement"], st.session_state.CONN)
#                     #df = session.sql(item["statement"]).to_pandas()

#                     if len(df.index) > 1:
#                         data_tab, line_tab, bar_tab = st.tabs(
#                             ["Data", "Line Chart", "Bar Chart"]
#                         )
#                         data_tab.dataframe(df)

#                         # Ensure you are only using numeric columns for plotting
#                         numeric_columns = df.select_dtypes(include=["float", "int"]).columns

#                         if len(numeric_columns) > 0:
#                             df = df.set_index(df.columns[0])  # Use first column as index

#                             with line_tab:
#                                 st.line_chart(df[numeric_columns])  # Plot only numeric columns

#                             with bar_tab:
#                                 st.bar_chart(df[numeric_columns])  # Plot only numeric columns
#                         else:
#                             st.warning("No numeric columns available for plotting.")
#                     else:
#                         st.dataframe(df)


st.title("QueryXpert AI")
# st.markdown(f"Semantic Model: `{FILE}`")

if "messages" not in st.session_state:
    
    st.session_state.messages = []
    st.session_state.suggestions = []
    st.session_state.active_suggestion = None
    
    if 'GREETING_DISPLAYED' not in st.session_state:
     st.session_state.GREETING_DISPLAYED = False
   
# greeting_message = {
#     "type": "text",  # Ensure this matches the expected format in display_content
#     "content": GREETING_MESSAGE_EN["content"]  # Change based on language preference if needed
# }

if not st.session_state.GREETING_DISPLAYED:
    greeting_message = GREETING_MESSAGE_EN  # You can change this based on language preference
    #st.session_state.messages.insert(0, greeting_message)  # Insert at the start of messages
    st.session_state.messages.append({ "content": [{"type": "text", "text": greeting_message}]});
    st.session_state.GREETING_DISPLAYED = True

# Display all messages, including the greeting if it’s the first load
for message_index, message in enumerate(st.session_state.messages):
    #st.write(st.session_state.messages)
    display_content(content=message["content"], message_index=message_index)

# for message_index, message in enumerate(st.session_state.messages):
#     # Skip the greeting message if it has already been displayed
#     if not st.session_state.GREETING_DISPLAYED and message["content"] in [GREETING_MESSAGE_EN["content"], GREETING_MESSAGE_ES["content"]]:
#         # Set flag to true once the greeting message is displayed
#         greeting_displayed = True
#     # Display the content for other messages or the first greeting
#     display_content(content=message["content"], message_index=message_index)



if user_input := st.chat_input("What is your question?"):
    process_message(prompt=user_input)
  

if st.session_state.active_suggestion:
    process_message(prompt=st.session_state.active_suggestion)
    st.session_state.active_suggestion = None

