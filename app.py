# Importing necessary libraries
from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# Setting up the Streamlit page configuration
st.set_page_config(page_title="HR Chat", page_icon="👩🏻‍💼")   # https://emojidb.org/
st.title("This is my HR Chatbot")

# Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# Helper function to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# Setup stage for collecting user details
if not st.session_state.setup_complete:

    # Personal Information Section
    st.subheader('Personal information', divider='rainbow')

    if "name" not in st.session_state:
        st.session_state.name = ""
    if "experience" not in st.session_state:
        st.session_state.experience = ""
    if "skills" not in st.session_state:
        st.session_state.skills = ""

    # Input fields for collecting user's personal information
    st.session_state.name = st.text_input(label="Name", value=st.session_state.name, max_chars=50, placeholder="Enter your name")
    st.session_state.experience= st.text_area(label="Expirience", value=st.session_state.experience, height=200, max_chars=None, placeholder="Describe your experience")
    st.session_state.skills = st.text_area(label="Skills", value=st.session_state.skills, height=None, max_chars=200, placeholder="List your skills")

    # Test labels for personal information
    #st.write(f"**Your Name**: {st.session_state.name}")
    #st.write(f"**Your Experience**: {st.session_state.experience}")
    #st.write(f"**Your Skills**: {st.session_state.skills}")

    # Company and Position Section
    st.subheader('Company and Position', divider = 'rainbow')

    # Initialize session state for company and position information and setting default values
    if "level" not in st.session_state:
        st.session_state.level = "Senior"
    if "position" not in st.session_state:
        st.session_state.position = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state.company = "AIS"

    # Field for selecting the job level, position and company
    # job --> left / position --> right
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio(
            "Choose a level",
            key="visibility",
            options=["Executive", "Manager", "Team Lead", "Junior", "Mid-level", "Senior"],
        )
    with col2:
        st.session_state.position = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data engineer", "AI/ML Engineer", "BI Analyst", "Financial Analyst")
        )
    # conpany
    st.session_state.company = st.selectbox(
        "Choose a company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify", "Bangchak", "AIS")
    )

    # Test labels for company and position information
    st.write(f"**Your company and position**: {st.session_state.level} {st.session_state.position} at {st.session_state.company}")

    # A button to complete the setup stage and start the interview
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup completed. Starting interview...")

# Interview Stage
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    # Display a welcome message and prompt the user to introduce themselves
    st.info(
    """
    Start by introducing yourself.
    """,
    icon = "👋"
    )

    # Initializing the OpenAI client using the API key from Streamlit's secrets
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Setting up the OpenAI model in session state if it is not already defined
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"

    # Feed information in a system prompt
    system_prompt = f""""
    You are an HR executive that interviews an interviewee called {st.session_state.name}
    with expirience {st.session_state.experience} and skills {st.session_state.skills}.
    You should interview him for the position {st.session_state.level} {st.session_state.position} 
    at the company {st.session_state.company}
    """

    # Initializing the 'messages' list and assigning the system prompt
    if not st.session_state.messages:
        st.session_state.messages = [{"role":"system", "content": system_prompt}]

    # Looping through the 'messages' list to display each message except system messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle user input and OpenAI response
    if st.session_state.user_message_count < 5:
    # Input field for the user to send a new message
        if prompt := st.chat_input("Type your question.", max_chars=200):
            # Appending the user's input to the 'messages' list in session state
            st.session_state.messages.append({"role":"user", "content":prompt})
            # Display the user's message in a chat bubble
            with st.chat_message("user"):
                st.markdown(prompt)

            # Assistant's response
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    # Feed all messages in the model
                    stream = client.chat.completions.create(
                        model = st.session_state.openai_model,
                        messages = [{"role":m["role"], "content":m["content"]} for m in st.session_state.messages],
                        stream = True,   # This line enables streaming for real-time response
                        )
                    # Display the assistant's response as it streams
                    response = st.write_stream(stream)
                # Append the assistant's full response to the 'messages' list
                st.session_state.messages.append({"role":"assistant", "content":response})

            st.session_state.user_message_count += 1
    
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

# Show "Get Feedback" 
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            { "role": "system",
                "content":
                    """
                    You are a helpful tool that provides feedback on an interviewee performance.
                    Before the Feedback give a score of 1 to 10.
                    Follow this format:
                    Overall Score: //Your score \n
                    Feedback: //Here you put your feedback
                    Give only the feedback do not ask any additional questions.
                    """
            },
            { "role": "user",
                "content": f"""This is the interview you need to evaluate. Keep in mind that you are only a tool.
                    And you shouldn't engage in any converstation: {conversation_history}"""
            }
        ]
    )

    # Response a feedback
    st.write(feedback_completion.choices[0].message.content)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")






