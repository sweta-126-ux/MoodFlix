
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MoodFlixRecommender:
    def __init__(self, dataframe):
        self.data = dataframe.copy()

        # Clean missing values
        required_columns = [
            "title", "type", "genres",
            "overview", "language", "year"
        ]

        for column in required_columns:
            if column not in self.data.columns:
                raise ValueError(f"Missing required column: {column}")

        for column in ["title", "type", "genres", "overview", "language"]:
            self.data[column] = self.data[column].fillna("").astype(str)

        # Combine information about each movie or series
        self.data["combined_features"] = (
            self.data["title"] + " " +
            self.data["genres"].str.replace("|", " ", regex=False) + " " +
            self.data["overview"]
        )

        # Convert text into numerical TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=3000,
            ngram_range=(1, 2)
        )

        self.feature_matrix = self.vectorizer.fit_transform(
            self.data["combined_features"]
        )

    def recommend(
        self,
        mood_genres=None,
        content_type="Both",
        preferred_genre="Any Genre",
        language="Any Language",
        limit=10
    ):
        # Convert mood genres into a list
        if mood_genres is None:
            mood_genres = []

        if isinstance(mood_genres, str):
            mood_genres = [mood_genres]

        mood_genres = [genre.strip() for genre in mood_genres]

        # Create a search query from the selected mood
        mood_query = " ".join(mood_genres)

        if not mood_query:
            mood_query = "popular entertaining movies and television series"

        # Convert the mood query into a TF-IDF vector
        query_vector = self.vectorizer.transform([mood_query])

        # Calculate similarity between mood and every title
        similarity_scores = cosine_similarity(
            query_vector,
            self.feature_matrix
        ).flatten()

        results = self.data.copy()
        results["similarity_score"] = similarity_scores

        # Filter by content type
        if content_type != "Both":
            results = results[
                results["type"].str.lower() == content_type.lower()
            ]

        # Filter by preferred genre
        if preferred_genre != "Any Genre":
            results = results[
                results["genres"].str.contains(
                    preferred_genre,
                    case=False,
                    regex=False
                )
            ]

        # Filter by language
        if language != "Any Language":
            results = results[
                results["language"].str.lower() == language.lower()
            ]

        if results.empty:
            return results

        # Give an additional score to matching mood genres
        def calculate_genre_bonus(genres):
            available_genres = [
                genre.strip().lower()
                for genre in genres.split("|")
            ]

            matching_genres = [
                genre.lower()
                for genre in mood_genres
                if genre.lower() in available_genres
            ]

            if not mood_genres:
                return 0

            return len(matching_genres) / len(mood_genres)

        results["genre_match"] = results["genres"].apply(
            calculate_genre_bonus
        )

        # Combine text similarity and genre matching
        results["similarity_score"] = (
            results["similarity_score"] * 0.75 +
            results["genre_match"] * 0.25
        )

        # Sort by relevance
        results = results.sort_values(
            by="similarity_score",
            ascending=False
        )

        results = results.head(limit).copy()

        # Display score as a percentage
        results["similarity_score"] = (
            results["similarity_score"] * 100
        ).round(2)

        return results
