import itertools
import os
import pickle
import re

from collections import Counter
from pathlib import Path

import gensim
import pandas as pd
import streamlit as st
from nltk.corpus import stopwords
from pandasticsearch import DataFrame
from sklearn.feature_extraction.text import CountVectorizer

##################################################################
######################## PARAMETERS ##############################
##################################################################

__version__ = "1.1.0"

##################################################################
##################################################################
##################################################################

path = os.path.join(os.path.expanduser("~"), ".twitfilt")
if not os.path.exists(path):
    os.makedirs(path)

tags_lock = os.path.join(path, "tags.lock")
stopwords = stopwords.words("english")
stopwords.extend(Path("toot/stopwords.txt").read_text().split("\n"))


def load_tweets():
    """
    Load tweets from twitter using Tweepy API.
    """

    df = DataFrame.from_es(url="http://dev.lan:9200", index="tweet-index", compat=7)

    return df.limit(10_000).to_pandas()


@st.cache(show_spinner=True)
def filter_tweets(df: pd.DataFrame, word: str):
    """
    Filter tweets based on search term provided in search bar.
    """

    return df[
        df["Favorited Tweets"].str.lower().str.contains(word.lower())
    ].reset_index()


def highlight_urls(data):
    """
    Add html tags to highlight urls making them clickable in streamlit table.
    """

    r = re.compile("https?:\/\/[a-zA-Z0-9\.\/]*")

    transformed_text = []
    for text in data:
        # st.write(text)
        links = r.findall(text)

        for link in links:
            text = text.replace(link, '<a href="{0}">{0}</a>'.format(link))

        transformed_text.append(text)

    pd.Series(transformed_text)

    return pd.Series(transformed_text)


def insert_newlines(data):
    """
    Render new lines in the table by replacing '\n' with <br>.
    """

    transformed_text = [text.replace("\n", "<br>") for text in data]

    return pd.Series(transformed_text)


def generate_tags(data):
    """
    Generates the tags based on the tweets and then assigns topics to each tweet.
    """

    all_keywords = []

    cv = CountVectorizer(
        strip_accents="unicode",
        stop_words=list(stopwords),
        ngram_range=(1, 2),
        token_pattern=r"[a-zA-Z]\w+",
    )
    text_transformer = cv.build_analyzer()

    transformed_text = [text_transformer(text) for text in data if text is not None]

    id2word = gensim.corpora.Dictionary(transformed_text)
    corpus = [id2word.doc2bow(text) for text in transformed_text]

    lda_model = gensim.models.LdaModel(
        corpus=corpus,
        id2word=id2word,
        num_topics=4,
        random_state=42,
        iterations=100,
        passes=10,
        alpha="auto",
        update_every=1,
        minimum_probability=0.02,
    )

    all_keywords = get_topic_per_docs(data, corpus, lda_model)

    return all_keywords


def get_topic_per_docs(data, corpus, ldamodel):
    """
    Assign topics to each tweet.
    """

    keywords = []

    for i, row in enumerate(ldamodel[corpus]):

        row = sorted(row, key=lambda x: (x[1]), reverse=True)

        for j, (topic_num, prop_topic) in enumerate(row):
            if j == 0:
                wp = ldamodel.show_topic(topic_num)
                topic_keywords = " ".join([word for word, prop in wp])
                keywords.append(topic_keywords)
                break
            else:
                break

    return keywords


def get_top_words(keywords):
    """
    Orders the topics from most common to least common for displaying.
    """

    keywords = itertools.chain.from_iterable(map(str.split, keywords))
    top_words = list(Counter(keywords))

    return top_words


def filter_tags(df: pd.DataFrame, options: list):
    """
    Filters tweets based on the tag(s) selected.
    """

    tweet_filter_list = []

    r = re.compile(f'({"|".join(options)})', re.IGNORECASE)

    for keyword in df["keywords"]:

        if r.search(keyword):
            tweet_filter_list.append(True)
        else:
            tweet_filter_list.append(False)

    return df[tweet_filter_list].reset_index()


def save_tags(full_text):
    """
    Saves the tags to a lock file as a caching mechanism.
    """

    tags = generate_tags(full_text)

    with open(tags_lock, "wb") as f:
        pickle.dump(tags, f)

    return tags


def main():

    tags = []
    options = None

    data = load_tweets()

    data["Favorited Tweets"] = (
        "<strong><em>@"
        + data["user"]
        + "</strong></em> - "
        + data["tweet"]
        + " <br><br> "
        + data["tweet_url"]
    )

    full_text = data["tweet"].tolist()

    st.title(f"My Likes - v{__version__}")

    search = st.text_input("Search:")

    if st.button("Generate Tags"):
        save_tags(full_text)

    # If the tag lock exists, the tags have already been created
    # If any new  tweets have been favorited, regen the tags
    # Retrieve the tags
    if os.path.exists(tags_lock):

        with open(tags_lock, "rb") as f:
            tags = pickle.load(f)

        if len(tags) != len(full_text):
            tags = save_tags(full_text)

        top_words = get_top_words(tags)

        options = st.multiselect("Search based on keywords: ", options=top_words)

    # If the user has generated tags, add a hidden column of those tags
    # Otherwise just use the Favorite Tweet column
    if tags:
        data["keywords"] = tags

    if search:
        data = filter_tweets(data, search)
    elif options:
        data = filter_tags(data, options)

    data["Favorited Tweets"] = (
        data["Favorited Tweets"].pipe(highlight_urls).pipe(insert_newlines)
    )

    st.markdown(
        data["Favorited Tweets"].to_frame().to_html(escape=False),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
