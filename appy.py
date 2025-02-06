import streamlit as st
import sounddevice as sd
import numpy as np
import wavio
import speech_recognition as sr
from analysis import clean_text, tokenize_and_filter, analyze_emotions, sentiment_analysis, plot_emotions
from database import create_comments_table, insert_comment, create_users_table, insert_user, authenticate_user, \
    reset_password, check_user_exists
from datetime import datetime

# Create database tables if they don't exist
create_users_table()
create_comments_table()

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = "Login"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None


def record_audio(duration=5, samplerate=44100, filename="audio.wav"):
    """Records audio and saves it as a WAV file."""
    st.write("🎤 Recording...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=2, dtype=np.int16)
    sd.wait()
    wavio.write(filename, audio, samplerate, sampwidth=2)
    st.session_state.audio_file = filename
    st.write("✅ Recording finished!")


# Page content
if st.session_state.page == "Login":
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "Home"
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

    if st.button("Forgot Password?"):
        st.session_state.page = "Reset Password"
        st.experimental_rerun()

    if st.button("Register"):
        st.session_state.page = "Register"
        st.experimental_rerun()

elif st.session_state.page == "Home" and st.session_state.get('logged_in'):
    st.title(f"Welcome, {st.session_state.username}!")
    st.subheader("Leave your voice note to assess your stress levels")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("🎙️ Start Recording"):
            record_audio()

    with col2:
        if st.button("⏸️ Pause Recording"):
            st.session_state.recording = False
            st.write("⏸️ Recording paused.")

    with col3:
        if st.button("📤 Submit for Analysis"):
            if st.session_state.audio_file:
                recognizer = sr.Recognizer()
                with sr.AudioFile(st.session_state.audio_file) as source:
                    audio_data = recognizer.record(source)
                    try:
                        comment = recognizer.recognize_google(audio_data)
                        st.write("🎤 You said:", comment)

                        cleansed_text = clean_text(comment)
                        final_words = tokenize_and_filter(cleansed_text)
                        emotions = analyze_emotions(final_words)
                        sentiment = sentiment_analysis(cleansed_text)

                        st.write(f"📊 Sentiment: {sentiment.capitalize()}")
                        st.write("📈 Emotion Analysis:")
                        fig = plot_emotions(emotions)
                        st.pyplot(fig)

                        insert_comment("Anonymous", comment, sentiment, "Unknown", "Unknown", "Unknown", "Unknown")
                        st.success("✅ Voice note submitted successfully!")
                    except sr.UnknownValueError:
                        st.error("❌ Could not understand the audio.")
                    except sr.RequestError as e:
                        st.error(f"❌ Speech recognition service error: {e}")
            else:
                st.error("❌ No audio found. Please record first.")

elif st.session_state.page == "Reset Password":
    st.title("Reset Password")
    username = st.text_input("Username")
    new_password = st.text_input("New Password", type="password")

    if st.button("Reset Password"):
        if not username or not new_password:
            st.error("Please fill all fields.")
        else:
            reset_password(username, new_password)
            st.success("Password reset successfully! Please login.")
            st.session_state.page = "Login"
            st.experimental_rerun()

    if st.button("Back to Login"):
        st.session_state.page = "Login"
        st.experimental_rerun()
