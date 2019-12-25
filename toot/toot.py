import datetime
import itertools
import os
import pickle
import re
from collections import Counter
from pathlib import Path

import gensim
import pandas as pd
import streamlit as st
import tweepy
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer

CONSUMER_KEY = os.environ.get('CONSUMER_KEY', None)
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', None)
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', None)
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', None)
REQUEST_TIME_LIMIT = int(os.environ.get('REQUEST_TIME_LIMIT', 60)) # in minutes

if not CONSUMER_KEY and not CONSUMER_SECRET and not ACCESS_TOKEN and not ACCESS_TOKEN_SECRET:
    raise ValueError('Consumer and Access keys and secrets must be set as environment variables.')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

API = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

path = os.path.join(os.path.expanduser('~'), '.twitfilt')
if not os.path.exists(path):
    os.makedirs(path)

requst_lock = os.path.join(path, 'request.lock')
tags_lock = os.path.join(path, 'tags.lock')
stopwords = stopwords.words('english')
stopwords.extend(Path('stopwords.txt').read_text().split('\n'))

@st.cache(show_spinner=True)
def load_tweets(time):

    return list(tweepy.Cursor(API.favorites, tweet_mode='extended').items())

def filter_tweets(df: pd.DataFrame, word: str):

    tweets = df['Favorited Tweets']

    r = re.compile(word, re.IGNORECASE)
    tweet_filter_list = []

    for tweet in tweets:
        if r.search(tweet):
            tweet_filter_list.append(True)
        else:
            tweet_filter_list.append(False)

    return df[tweet_filter_list].reset_index()

def highlight_urls(data):

    r = re.compile('https?:\/\/[A-Za-z0-9]*\.[a-z]*\/[A-Za-z0-9]*')

    transformed_text = []
    for text in data:
        links = r.findall(text)

        for link in links:
            text = text.replace(link, '<a href="{0}">{0}</a>'.format(link))

        transformed_text.append(text)
    
    pd.Series(transformed_text)
        
    return pd.Series(transformed_text)

def insert_newlines(data):

    transformed_text = [text.replace('\n', '<br>') for text in data]

    return pd.Series(transformed_text)

def write_current_date(cur_time=None):

    if not cur_time:
        time = datetime.datetime.now()
    else:
        time = cur_time

    with open(requst_lock, 'w') as f:
        f.write(str(time))

    return time

def generate_keywords(data):

    all_keywords = []

    cv = CountVectorizer(strip_accents='unicode', stop_words=list(stopwords), ngram_range=(1,2), token_pattern=r'[a-zA-Z]\w+')
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
        alpha='auto',
        update_every=1,
        minimum_probability=0.02,
        )

    all_keywords = get_topic_per_docs(data, corpus, lda_model)

    return all_keywords

def get_topic_per_docs(data, corpus, ldamodel):

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

    keywords = itertools.chain.from_iterable(map(str.split, keywords))
    top_words = list(Counter(keywords))

    return top_words

def filter_tags(df: pd.DataFrame, options: list):

    tweet_filter_list = []

    r = re.compile(f'({"|".join(options)})', re.IGNORECASE)

    for keyword in df['keywords']:

        if r.search(keyword):
            tweet_filter_list.append(True)
        else:
            tweet_filter_list.append(False)

    return df[tweet_filter_list]


def main():

    tags = []
    options = None

    # This block uses a time lock to limit the requests when loading/ searching tweets
    #    1. If this is first time use, write the current time to the lock file and load the tweets
    #    2. Upon further use, if the time in lock file and the current time is greater than 15min (editable) then get the tweets with the current time
    #    3. If it is < 20min get the tweets using the time from the lock file taking advantage of streamlit caching to not send an api request
    if not os.path.exists(requst_lock):
        time = write_current_date()
        data = load_tweets(time)
    else:
        with open(requst_lock, 'r') as f:
            r_time = f.read()

        time = datetime.datetime.strptime(r_time, '%Y-%m-%d %H:%M:%S.%f')
        cur_time = datetime.datetime.now()

        if ((cur_time - time).seconds / 60) > REQUEST_TIME_LIMIT:
            data = load_tweets(str(cur_time))
            write_current_date(cur_time)
        else:
            data = load_tweets(str(time))

    all_favorites = [f'<strong><em>@{fav.user.name}</strong></em> - {fav.full_text}' for fav in data]
    full_text = [fav.full_text for fav in data]

    st.title('My Likes')

    search = st.text_input('Search:')

    if st.button('Generate Tags'):
        tags = generate_keywords(full_text)

        with open(tags_lock, 'wb') as f:
            pickle.dump(tags, f)

    if os.path.exists(tags_lock):

        with open(tags_lock, 'rb') as f:
            tags = pickle.load(f)

        top_words = get_top_words(tags)

    options = st.multiselect(
        'Search based on keywords: ',
        options=top_words
        )

    if tags:
        df = pd.DataFrame({'Favorited Tweets': all_favorites, 'keywords': tags})
    else:
        df = pd.DataFrame({'Favorited Tweets': all_favorites})

    if search:
        df = filter_tweets(df, search)
    elif options:
        df = filter_tags(df, options)

    df['Favorited Tweets'] = df['Favorited Tweets'] \
                                .pipe(highlight_urls) \
                                .pipe(insert_newlines)

    st.markdown(df['Favorited Tweets'].to_frame().to_html(escape=False), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
