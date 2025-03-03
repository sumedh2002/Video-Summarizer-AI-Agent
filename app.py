import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
import google.generativeai as genai
import os
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from youtube_transcript_api import YouTubeTranscriptApi
import re

load_dotenv()

# Load API key
API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

st.set_page_config(
    page_title="Video Summarizer AI-Agent",
    page_icon="🎥",
    layout="wide"
)

st.title("Web Video Summarizer AI Agent")
st.header("Find, Analyze, and Summarize Any Video from the Web")

# Initialize AI agent
def initialize_agent():
    return Agent(
        name="web_video_summarizer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        markdown=True
    )

multimodal_Agent = initialize_agent()

# Function to search for YouTube videos
def search_videos(query, max_results=3):
    with DDGS() as ddgs:
        search_results = list(ddgs.text(f"{query} site:youtube.com", max_results=max_results))
    return search_results

# Extract YouTube Video ID
def extract_youtube_id(url):
    match = re.search(r"v=([A-Za-z0-9_-]+)", url)
    if match:
        return match.group(1)
    return None

# User Input: Search for Video
search_query = st.text_input(
    "Enter a topic to find relevant videos:",
    placeholder="E.g., Latest AI advancements, Quantum Computing explained"
)

if st.button("🔍 Search and Summarize"):
    if not search_query:
        st.warning("Please enter a topic to search for videos.")
    else:
        try:
            with st.spinner("Searching for relevant videos..."):
                search_results = search_videos(search_query, max_results=3)
                if not search_results:
                    st.error("No relevant videos found.")
                else:
                    video_links = [result["href"] for result in search_results if "youtube.com/watch" in result["href"]]
                    
                    if not video_links:
                        st.error("No valid YouTube videos found.")
                    else:
                        st.subheader("Top Video Found:")
                        video_url = video_links[0]  # Taking the first result
                        st.video(video_url)

                        # Extract YouTube Video ID
                        video_id = extract_youtube_id(video_url)
                        if video_id:
                            with st.spinner("Fetching transcript..."):
                                try:
                                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                                    transcript_text = " ".join([entry["text"] for entry in transcript])

                                    st.subheader("AI-Generated Summary:")
                                    with st.spinner("Summarizing video content..."):
                                        analysis_prompt = f"""
                                        Summarize the following YouTube video transcript in an informative, structured, and user-friendly way:
                                        {transcript_text}
                                        """
                                        response = multimodal_Agent.run(analysis_prompt)
                                        st.markdown(response.content)
                                except Exception as e:
                                    st.error(f"Could not fetch transcript: {e}")
                        else:
                            st.error("Failed to extract video ID from URL.")
        except Exception as error:
            st.error(f"An error occurred: {error}")
