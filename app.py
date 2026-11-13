
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.mood_engine import get_mood_profile
from src.recommender import MoodFlixRecommender

# ---------------- PAGE CONFIG ----------------

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "movies.csv"
CSS_PATH = BASE_DIR / "assets" / "style.css"

st.set_page_config(
    page_title="MoodFlix | Discover Your Next Favourite",
    page_icon="🎬",
    layout="wide"
)

if CSS_PATH.exists():
    st.markdown(
        f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )

# ---------------- DATA LOADING ----------------

@st.cache_resource
def load_recommender(path):
    data = pd.read_csv(path)

    required = [
        "title", "type", "genres",
        "overview", "language", "year"
    ]

    missing = [column for column in required if column not in data.columns]

    if missing:
        raise ValueError(f"Missing dataset columns: {missing}")

    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    return data, MoodFlixRecommender(data)

try:
    data, recommender = load_recommender(str(DATA_PATH))
except Exception as error:
    st.error(f"Could not load MoodFlix dataset: {error}")
    st.stop()

# ---------------- SESSION STATE ----------------

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

# ---------------- HEADER ----------------

st.markdown(
    """
    <div style="text-align:center; padding:25px 0 10px;">
        <h1 style="font-size:3.2rem; letter-spacing:3px;">
            MOOD<span style="color:#A53B57;">FLIX</span>
        </h1>
        <p style="color:#D6B37F; font-size:1.1rem;">
            Your mood. Your movies. Your universe.
        </p>
        <p style="color:#aaa;">
            Discover stories that match how you feel.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown("## 🎬 Your Movie Space")

    st.write("Find something worth watching.")

    selected_mood = st.selectbox(
        "How are you feeling?",
        [
            "Happy", "Sad", "Romantic", "Angry",
            "Bored", "Curious", "Relaxed", "Adventurous"
        ]
    )

    content_type = st.radio(
        "What would you like?",
        ["Both", "Movie", "TV Series"]
    )

    all_genres = sorted({
        genre.strip()
        for value in data["genres"].dropna()
        for genre in str(value).split("|")
        if genre.strip()
    })

    all_languages = sorted({
        language.strip()
        for language in data["language"].dropna()
        if language.strip()
    })

    preferred_genre = st.selectbox(
        "Preferred genre",
        ["Any Genre"] + all_genres
    )

    language = st.selectbox(
        "Preferred language",
        ["Any Language"] + all_languages
    )

    valid_years = data["year"].dropna()

    if not valid_years.empty:
        min_year = int(valid_years.min())
        max_year = int(valid_years.max())

        year_range = st.slider(
            "Release year",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
    else:
        year_range = None

    min_match = st.slider(
        "Minimum mood match (%)",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )

    st.caption("Recommendations are generated using TF-IDF and cosine similarity.")

# ---------------- RECOMMENDATIONS ----------------

st.markdown("## ✨ Discover Your Next Watch")

st.write(
    f"Let's find something for your **{selected_mood.lower()}** mood."
)

if st.button("Find My Recommendations ✨", use_container_width=True):

    mood_genres = get_mood_profile(selected_mood)

    results = recommender.recommend(
        mood_genres=mood_genres,
        content_type=content_type,
        preferred_genre=preferred_genre,
        language=language,
        limit=len(data)
    )

    if year_range is not None:
        results = results[
            results["year"].between(year_range[0], year_range[1])
        ]

    results = results[
        results["similarity_score"] >= min_match
    ]

    st.session_state.recommendations = results.reset_index(drop=True)

# ---------------- DISPLAY RESULTS ----------------

results = st.session_state.recommendations

if results is not None:

    if results.empty:
        st.warning(
            "No titles match these filters. Try lowering the minimum match "
            "or changing your preferences."
        )

    else:
        st.success(f"Found {len(results)} recommendations for you!")

        for index, movie in results.iterrows():

            title = str(movie["title"])
            genres = str(movie["genres"])
            overview = str(movie["overview"])
            score = float(movie["similarity_score"])

            mood_genres = get_mood_profile(selected_mood)

            if isinstance(mood_genres, str):
                mood_genres = [mood_genres]

            matched_genres = [
                genre.strip()
                for genre in genres.split("|")
                if genre.strip().lower() in [
                    item.lower() for item in mood_genres
                ]
            ]

            with st.container(border=True):

                left, right = st.columns([4, 1])

                with left:
                    st.subheader(f"{index + 1}. {title}")

                    st.caption(
                        f"{movie['type']}  •  "
                        f"{movie['year']:.0f}" if pd.notna(movie["year"])
                        else str(movie["type"])
                    )

                    st.write(f"**Genres:** {genres}")
                    st.write(f"**Language:** {movie['language']}")

                    st.write(overview)

                    if matched_genres:
                        st.info(
                            "Why this matches your mood: "
                            + ", ".join(matched_genres)
                            + " matches your selected mood."
                        )
                    else:
                        st.info(
                            "Why this matches your mood: "
                            "Its description and content features are "
                            "similar to your selected mood."
                        )

                with right:
                    st.metric("Mood Match", f"{score:.1f}%")

                    if title in st.session_state.watchlist:
                        st.button(
                            "❤️ Saved",
                            key=f"saved_{index}",
                            disabled=True
                        )
                    else:
                        if st.button(
                            "♡ Watchlist",
                            key=f"save_{index}"
                        ):
                            st.session_state.watchlist.append(title)
                            st.rerun()

# ---------------- WATCHLIST ----------------

st.divider()

st.markdown("## ❤️ My Watchlist")

st.write("Your personally saved movies and series.")

if not st.session_state.watchlist:
    st.info("Your watchlist is empty. Save a recommendation to see it here.")

else:
    for title in list(st.session_state.watchlist):

        matching = data[data["title"] == title]

        if not matching.empty:
            movie = matching.iloc[0]

            with st.container(border=True):
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(f"**{title}**")
                    st.caption(
                        f"{movie['type']} • {movie['genres']}"
                    )

                with col2:
                    if st.button(
                        "Remove",
                        key=f"remove_{title}"
                    ):
                        st.session_state.watchlist.remove(title)
                        st.rerun()

# ---------------- FOOTER ----------------

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#888; padding:15px;">
        <p>MOODFLIX • Powered by Machine Learning</p>
        <p>Your next favourite story is waiting.</p>
    </div>
    """,
    unsafe_allow_html=True
)