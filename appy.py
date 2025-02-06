import streamlit as st
import speech_recognition as sr
from analysis import clean_text, tokenize_and_filter, analyze_emotions, sentiment_analysis, plot_emotions
from database import create_comments_table, insert_comment, create_users_table, insert_user, authenticate_user, reset_password, check_user_exists

# Create the database tables if they don't exist
create_users_table()
create_comments_table()

# Initialize the session state variables if not already present
if 'page' not in st.session_state:
    st.session_state.page = "Login"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .stTextInput input {
        border-radius: 5px;
        padding: 10px;
        font-size: 16px;
    }
    .stTitle {
        font-size: 36px;
        font-weight: bold;
        color: #2E86C1;
    }
    .stSubheader {
        font-size: 24px;
        color: #2E86C1;
    }
    .stMarkdown {
        font-size: 18px;
    }
    .stError {
        color: #E74C3C;
    }
    .stSuccess {
        color: #28B463;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Horizontal navigation bar
if st.session_state.logged_in:
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] > div:first-child {
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    nav_options = st.columns([1, 1])
    with nav_options[0]:
        if st.button("🏠 Home", key="nav_home"):
            st.session_state.page = "Home"
    with nav_options[1]:
        if st.button("ℹ️ About Us", key="nav_about"):
            st.session_state.page = "About Us"
else:
    if st.session_state.page not in ["Login", "Register", "Reset Password"]:
        nav_options = st.columns([1, 1])
        with nav_options[0]:
            if st.button("🔑 Login", key="nav_login"):
                st.session_state.page = "Login"
        with nav_options[1]:
            if st.button("📝 Register", key="nav_register"):
                st.session_state.page = "Register"

# Page Content
if st.session_state.page == "Login":
    st.markdown("<div class='stTitle'>Login</div>", unsafe_allow_html=True)
    username = st.text_input('Username', placeholder="Enter your username")
    password = st.text_input('Password', type='password', placeholder="Enter your password")

    if st.button("Login", key="login_button"):
        if not username or not password:
            st.error("Please provide both username and password.")
        else:
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "Home"
                st.rerun()  # Updated to st.rerun()
            else:
                st.error("Invalid username or password")

    if st.button("Forgot Password?", key="forgot_password_button"):
        st.session_state.page = "Reset Password"
        st.rerun()  # Updated to st.rerun()

    if st.button("Register", key="login_register_button"):
        st.session_state.page = "Register"
        st.rerun()  # Updated to st.rerun()

elif st.session_state.page == "Register":
    st.markdown("<div class='stTitle'>Register</div>", unsafe_allow_html=True)
    username = st.text_input('Username', placeholder="Enter your username")
    password = st.text_input('Password', type='password', placeholder="Enter your password")
    email = st.text_input('Email', placeholder="Enter your email")

    if st.button("Register", key="register_button"):
        if not username or not password or not email:
            st.error("Please fill out all fields.")
        else:
            if check_user_exists(username):
                st.error("Username already exists. Please choose a different username.")
            else:
                insert_user(username, password, email)
                st.success("User registered successfully! Please login.")
                st.session_state.page = "Login"
                st.rerun()  # Updated to st.rerun()

    if st.button("Back to Login", key="register_back_button"):
        st.session_state.page = "Login"
        st.rerun()  # Updated to st.rerun()

elif st.session_state.page == "Reset Password":
    st.markdown("<div class='stTitle'>Reset Password</div>", unsafe_allow_html=True)
    username = st.text_input('Username', placeholder="Enter your username")
    new_password = st.text_input('New Password', type='password', placeholder="Enter your new password")

    if st.button("Reset Password", key="reset_password_button"):
        if not username or not new_password:
            st.error("Please provide both username and new password.")
        else:
            reset_password(username, new_password)
            st.success("Password reset successfully! Please login.")
            st.session_state.page = "Login"
            st.rerun()  # Updated to st.rerun()

    if st.button("Back to Login", key="reset_back_button"):
        st.session_state.page = "Login"
        st.rerun()  # Updated to st.rerun()

elif st.session_state.page == "Home" and st.session_state.get('logged_in'):
    st.markdown(f"<div class='stTitle'>Welcome, {st.session_state.username}!</div>", unsafe_allow_html=True)
    st.markdown("<div class='stSubheader'>Leave your voice note to assess your stress levels</div>", unsafe_allow_html=True)

    # Voice Recording Section
    st.markdown("### 🎤 Record Your Voice Note")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🎙️ Start Recording", key="start_recording_button"):
            st.session_state.recording = True
            st.session_state.audio_data = None
            st.write("🎤 Recording started... Speak now!")
    with col2:
        if st.button("⏸️ Pause Recording", key="pause_recording_button"):
            st.session_state.recording = False
            st.write("⏸️ Recording paused.")
    with col3:
        if st.button("📤 Submit for Analysis", key="submit_button"):
            if st.session_state.audio_data:
                recognizer = sr.Recognizer()
                try:
                    comment = recognizer.recognize_google(st.session_state.audio_data)
                    st.write("🎤 You said:", comment)

                    # Perform analysis
                    cleansed_text = clean_text(comment)
                    final_words = tokenize_and_filter(cleansed_text)
                    emotions = analyze_emotions(final_words)
                    sentiment = sentiment_analysis(cleansed_text)

                    # Display results
                    st.write(f"📊 Sentiment: {sentiment.capitalize()}")
                    st.write("📈 Emotion Analysis:")
                    fig = plot_emotions(emotions)
                    st.pyplot(fig)

                    # Save to database
                    insert_comment("Anonymous", comment, sentiment, "Unknown", "Unknown", "Unknown", "Unknown")
                    st.success("✅ Voice note submitted successfully!")

                except sr.UnknownValueError:
                    st.error("❌ Google Speech Recognition could not understand the audio.")
                except sr.RequestError as e:
                    st.error(f"❌ Could not request results from Google Speech Recognition service; {e}")
            else:
                st.error("❌ No audio data found. Please record your voice first.")

    # Audio Recording Logic
    if st.session_state.recording:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.session_state.audio_data = recognizer.listen(source)

elif st.session_state.page == "About Us" and st.session_state.get('logged_in'):
    st.markdown("<div class='stTitle'>About Us</div>", unsafe_allow_html=True)
    st.write("""
    ### 🌾 Farmer Stress Assessment Tool
    This tool is designed to help farmers assess their stress levels by analyzing their voice notes. 
    By recording and analyzing your voice, we can provide insights into your emotional state and suggest ways to manage stress.
    """)