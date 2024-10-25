from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import snowflake.connector
import streamlit as st


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
        font: normal normal 600 14px/20px 'Poppins', sans-serif;
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
    .stSidebar,.stSidebarCollapsedControl {
       display:none;
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
GREETING_MESSAGE_EN = {"role": "assistant", "content": "Hello! Welcome to Informa AI. How can I assist you today?"}
GREETING_MESSAGE_ES = {"role": "assistant", "content": "¡Hola! Bienvenido a Informa AI. ¿En qué puedo ayudarte hoy?"}

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
                        <span class="assistant-name">Informa AI</span>
                    </div>
                    <div class="assistant-message">{message}</div>
                </div>
                """, unsafe_allow_html=True)
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
    st.session_state.messages.append(
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    )
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            response = send_message(prompt=prompt)
            content = response["message"]["content"]
            display_content(content=content)
    st.session_state.messages.append({"role": "assistant", "content": content})


def display_content(content: list, message_index: int = None) -> None:
    """Displays a content item for a message."""
    message_index = message_index or len(st.session_state.messages)
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            with st.expander("Suggestions", expanded=True):
                for suggestion_index, suggestion in enumerate(item["suggestions"]):
                    if st.button(suggestion, key=f"{message_index}_{suggestion_index}"):
                        st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            with st.expander("SQL Query", expanded=False):
                st.code(item["statement"], language="sql")
            with st.expander("Results", expanded=True):
                with st.spinner("Running SQL..."):
                    df = pd.read_sql(item["statement"], st.session_state.CONN)
                    #df = session.sql(item["statement"]).to_pandas()

                    if len(df.index) > 1:
                        data_tab, line_tab, bar_tab = st.tabs(
                            ["Data", "Line Chart", "Bar Chart"]
                        )
                        data_tab.dataframe(df)

                        # Ensure you are only using numeric columns for plotting
                        numeric_columns = df.select_dtypes(include=["float", "int"]).columns

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


st.title("QueryXpert AI")
# st.markdown(f"Semantic Model: `{FILE}`")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.suggestions = []
    st.session_state.active_suggestion = None

for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        display_content(content=message["content"], message_index=message_index)

if user_input := st.chat_input("What is your question?"):
    process_message(prompt=user_input)

if st.session_state.active_suggestion:
    process_message(prompt=st.session_state.active_suggestion)
    st.session_state.active_suggestion = None

##########OLD code with 2 click issue on suggestions #######
# def process_message(prompt: str) -> None:
#     """Processes a message and adds the response to the chat."""
#     st.session_state.messages.append(
#         {"role": "user", "content": [{"type": "text", "text": prompt}]}
#     )
#     with st.chat_message("user"):
#         st.markdown(prompt)
#     with st.chat_message("assistant"):
#         with st.spinner("Generating response..."):
#             response = send_message(prompt=prompt)
#             request_id = response["request_id"]
#             content = response["message"]["content"]
#             st.session_state.messages.append(
#                 {**response['message'], "request_id": request_id}
#             )
#             display_content(content=content, request_id=request_id)  # type: ignore[arg-type]


# # Modify `process_message` to use only the custom icons for user and assistant
# # def process_message(prompt: str) -> None:
# #     """Processes a message and adds the response to the chat."""
# #     # Add user message
# #     st.session_state.messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
# #     display_message_with_icon("user", prompt)  # Display user message with icon

# #     # Add assistant message with spinner
# #     with st.spinner("Generating response..."):
# #         response = send_message(prompt=prompt)
# #         content = response["message"]["content"]
# #         request_id = response["request_id"]
        
# #         # Add assistant response to session and display
# #         st.session_state.messages.append({**response['message'], "request_id": request_id})
# #         for item in content:
# #             if item["type"] == "text":
# #                 display_message_with_icon("assistant", item["text"])
# #         display_content(content=content, request_id=request_id)

# def display_content(
#     content: List[Dict[str, str]],
#     request_id: Optional[str] = None,
#     message_index: Optional[int] = None,
# ) -> None:
#     """Displays a content item for a message."""
#     message_index = message_index or len(st.session_state.messages)
#     if request_id:
#         with st.expander("Request ID", expanded=False):
#             st.markdown(request_id)
#     for item in content:
#         if item["type"] == "text":
#             st.markdown(item["text"])
#         elif item["type"] == "suggestions":
#             with st.expander("Suggestions", expanded=True):
#                 for suggestion_index, suggestion in enumerate(item["suggestions"]):
#                     if st.button(suggestion, key=f"{message_index}_{suggestion_index}"):
#                         st.session_state.active_suggestion = suggestion
#         elif item["type"] == "sql":
#             display_sql(item["statement"])


# @st.cache_data
# def display_sql(sql: str) -> None:
#     with st.expander("SQL Query", expanded=False):
#         st.code(sql, language="sql")
#     with st.expander("Results", expanded=True):
#         with st.spinner("Running SQL..."):
#             df = pd.read_sql(sql, st.session_state.CONN)
#             if len(df.index) > 1:
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
#             else:
#                         st.dataframe(df)


# def show_conversation_history() -> None:
#     for message_index, message in enumerate(st.session_state.messages):
#         chat_role = "assistant" if message["role"] == "analyst" else "user"
#         with st.chat_message(chat_role):
#             display_content(
#                 content=message["content"],
#                 request_id=message.get("request_id"),
#                 message_index=message_index,
#             )

# # def show_conversation_history() -> None:
# #     for message_index, message in enumerate(st.session_state.messages):
# #         chat_role = "assistant" if message["role"] == "analyst" else "user"
# #        # display_message_with_icon(chat_role, message["content"][0]["text"])
# #     with st.chat_message(chat_role):
# #         display_content(
# #             content=message["content"],
# #             request_id=message.get("request_id"),
# #             message_index=message_index,
# #         )

# # def show_conversation_history() -> None:
# #     for message_index, message in enumerate(st.session_state.messages):
# #         chat_role = "assistant" if message["role"] == "analyst" else "user"
# #         with st.chat_message(chat_role):
# #             display_content(
# #                 content=message["content"],
# #                 request_id=message.get("request_id"),
# #                 message_index=message_index,
# #             )


# def reset() -> None:
#     st.session_state.messages = []
#     st.session_state.suggestions = []
#     st.session_state.active_suggestion = None


# st.title("QueryXpert AI")
# # st.markdown(f"Semantic Model: `{FILE}`")

# if "messages" not in st.session_state:
#     reset()

# # with st.sidebar:
# #     if st.button("Reset conversation"):
# #         reset()

# show_conversation_history()

# if user_input := st.chat_input("What is your question?"):
#     process_message(prompt=user_input)

# if st.session_state.active_suggestion:
#     process_message(prompt=st.session_state.active_suggestion)
#     st.session_state.active_suggestion = None  # Clear after processing