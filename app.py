import streamlit as st
import pickle
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# TMDB API Key (Replace with your API key)
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiZjQzZTQxNjIwNWM5MGJjM2Y0Y2ZjZWUxNzZkY2UxOSIsIm5iZiI6MTc0MDc0MjEwMy40NDk5OTk4LCJzdWIiOiI2N2MxOWRkNzEwZTc5YzM0MjRhMjZmM2QiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.OHAqk6zLrfSdpphsB0NsEtg7kYUWHMTYGCmnTkpIb3I"

# Set up requests session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
session.mount("https://", HTTPAdapter(max_retries=retries))

st.title("🎬 Movie Recommendation System")

# Load movie data
with open("movie_dict.pkl", "rb") as f:
    movie_data = pickle.load(f)

# Convert dict to DataFrame if needed
if isinstance(movie_data, dict):
    movies_df = pd.DataFrame.from_dict(movie_data)
else:
    movies_df = movie_data.copy()

# Ensure required columns exist
required_cols = ['title', 'sentiment_category']
missing = [col for col in required_cols if col not in movies_df.columns]
if missing:
    st.error(f"Missing columns in movies data: {missing}")
    st.stop()

# Set 'title' as index
movies_df.set_index('title', inplace=True)

# Load similarity matrix
with open("similarity.pkl", "rb") as f:
    similarity = pickle.load(f)

# TMDB headers for poster API
tmdb_headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "User-Agent": "*"
}

@st.cache_data
def fetch_poster(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}"
    try:
        resp = session.get(url, headers=tmdb_headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results")
        if results:
            poster_path = results[0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/original{poster_path}"
        return None
    except Exception as e:
        # Log error and return None
        print(f"Error fetching poster for {movie_title}: {e}")
        return None
    
def get_sentiment_value(title):
    val = movies_df.loc[title, "sentiment_category"]
    if isinstance(val, pd.Series):
        return val.iloc[0]
    return val

# User inputs
movie_name = st.selectbox("Choose a movie:", movies_df.index.tolist())
sentiment_filter = st.selectbox(
    "Filter recommendations by sentiment:",
    ["All", "Positive", "Negative", "Neutral"]
)
filter_lower = sentiment_filter.lower()

if movie_name:
    sel_sent = get_sentiment_value(movie_name)
    st.write(f"Recommendations for **{movie_name}** (Sentiment: {sel_sent})")

    # Build sorted similarity list
    idx = movies_df.index.get_loc(movie_name)
    sim_scores = list(enumerate(similarity[idx]))
    sim_sorted = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # First pass: apply sentiment filter
    recs = []
    for i, _ in sim_sorted:
        title = movies_df.index[i]
        if title == movie_name:
            continue
        if sentiment_filter == "All" or get_sentiment_value(title) == filter_lower:
            recs.append(title)
        if len(recs) >= 5:
            break

    # Fallback to fill up to 5
    if len(recs) < 5:
        for i, _ in sim_sorted:
            title = movies_df.index[i]
            if title == movie_name or title in recs:
                continue
            recs.append(title)
            if len(recs) >= 5:
                break

    # Display
    if recs:
        cols = st.columns(len(recs))
        for col, title in zip(cols, recs):
            poster = fetch_poster(title)
            caption = f"{title} ({get_sentiment_value(title)})"
            with col:
                if poster:
                    st.image(poster, caption=caption, use_container_width=True)
                else:
                    st.write(caption)
    else:
        st.write("No recommendations found.")

