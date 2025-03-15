import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests  # For fetching movie posters
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

# TMDb API Key (Replace with your API key)
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiZjQzZTQxNjIwNWM5MGJjM2Y0Y2ZjZWUxNzZkY2UxOSIsIm5iZiI6MTc0MDc0MjEwMy40NDk5OTk4LCJzdWIiOiI2N2MxOWRkNzEwZTc5YzM0MjRhMjZmM2QiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.OHAqk6zLrfSdpphsB0NsEtg7kYUWHMTYGCmnTkpIb3I"

st.title("🎬 Movie Recommendation System")

# Load movie data
with open("movies.pkl", "rb") as file:
    movie_dict = pickle.load(file)

movies_df = pd.DataFrame.from_dict(movie_dict)

# Load similarity matrix
with open("similarity.pkl", "rb") as file:
    similarity = pickle.load(file)

# Ensure movie titles are the index
if "title" in movies_df.columns:
    movies_df.set_index("title", inplace=True)

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiZjQzZTQxNjIwNWM5MGJjM2Y0Y2ZjZWUxNzZkY2UxOSIsIm5iZiI6MTc0MDc0MjEwMy40NDk5OTk4LCJzdWIiOiI2N2MxOWRkNzEwZTc5YzM0MjRhMjZmM2QiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.OHAqk6zLrfSdpphsB0NsEtg7kYUWHMTYGCmnTkpIb3I",
    "User-Agent": "*",
}

poster_cacheds={}

# Function to fetch movie poster from TMDb API
@st.cache_data
def fetch_poster(movie_title):
    # time.sleep(1)
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}"
    try:
        response = requests.get(url,headers=headers,timeout=5)
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            poster_path = data["results"][0]["poster_path"]
            return f"https://image.tmdb.org/t/p/original{poster_path}"
        else:
            return None
    except requests.exceptions.RequestException as e:
        print("Error fetching poster:", e)
        return None

# 🎬 **Dropdown List of All Movies**
movie_name = st.selectbox("Choose a movie:", movies_df.index.tolist())

if movie_name:
    st.write(f"Checking recommendations for: {movie_name}")

    # Get movie index
    movie_idx = movies_df.index.get_loc(movie_name)

    # ✅ Convert similarity scores to a NumPy array before sorting
    similarity_scores = np.array(list(enumerate(similarity[movie_idx])))

    # ✅ Ensure sorting works by explicitly specifying key
    sorted_movies = sorted(similarity_scores, key=lambda x: float(x[1]), reverse=True)[1:6]

    recommendations = [movies_df.index[int(i[0])] for i in sorted_movies]

    # Display Recommendations with Posters
    if recommendations:
        st.write("Recommended Movies:")
        
        cols = st.columns(5)  # Create 5 columns for displaying posters side by side
        
        for idx, movie in enumerate(recommendations):
            poster_url = fetch_poster(movie)
            
            with cols[idx]:  # Place each movie in a separate column
                if poster_url:
                    st.image(poster_url, caption=movie, use_container_width=True)
                else:
                    st.write(movie)  # Show title if poster is not available
    else:
        st.write("No recommendations found. Try another movie.")
