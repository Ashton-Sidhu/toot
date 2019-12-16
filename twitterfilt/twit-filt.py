import datetime
import itertools
import os
import re
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import gensim
import nltk
import pandas as pd
import streamlit as st
import tweepy
from sklearn.feature_extraction.text import CountVectorizer

from webscrape import webscrape

# CONSUMER_KEY = os.environ.get('CONSUMER_KEY', None)
# CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', None)
# ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', None)
# ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', None)
CONSUMER_KEY = 't0jLnSa3TOzrafAPV0STFqz8v'
CONSUMER_SECRET = 'hPI00BnWzqUa07EAIvWmJCyxHiJerr17yuJjPrWpluy6PsKzgu'
ACCESS_TOKEN = '1082768738892554242-NyIKUDstlQ6p6Jz7p5MKFkCv1XalnK'
ACCESS_TOKEN_SECRET = '3UI5SG1qUP3ItujmAWF875AsuzNPmFd24zEGFp4ROY9Rx'
REQUEST_TIME_LIMIT = int(os.environ.get('REQUEST_TIME_LIMIT', 60*50)) # in minutes

if not CONSUMER_KEY and not CONSUMER_SECRET and not ACCESS_TOKEN and not ACCESS_TOKEN_SECRET:
    raise ValueError('Consumer and Access keys and secrets must be set as environment variables.')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

API = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

path = os.path.join(os.path.expanduser('~'), '.twitfilt')
if not os.path.exists(path):
    os.makedirs(path)

tags = []
requst_lock = os.path.join(path, 'request.lock')
tags_lock = os.path.join(path, 'tags.lock')

@st.cache(show_spinner=True)
def load_tweets(time):

    return list(tweepy.Cursor(API.favorites, tweet_mode='extended').items())

def filter_tweets(df: pd.DataFrame, word: str):

    tweets = df['Favorited Tweets']

    r = re.compile(word, re.IGNORECASE)

    return df[filter(r.search, tweets)]

def highlight_urls(data):

    r = re.compile('https?:\/\/[A-Za-z0-9]*\.[a-z]*\/[A-Za-z0-9]*')

    transformed_text = []
    for text in data:
        links = r.findall(text)

        for link in links:
            text = text.replace(link, '<a href="{0}">{0}</a>'.format(link))

        transformed_text.append(text)
        
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

def get_url_text(data):
    
    r = re.compile('https?:\/\/[A-Za-z0-9]*\.[a-z]*\/[A-Za-z0-9]*')

    webpage_data = []
    with st.spinner('Scraping twitter data..'):
        for ind,text in enumerate(data):
            links = r.findall(text)

            with Pool(5) as p:
                webpage_text = p.map(webscrape, links)

            #webpage_text = [webscrape(link) for link in links]
            webpage_data.append(webpage_text)

            if ind % 10 == 0:
                print(f'Completed {(ind+1)}/{len(data)} ..')

    return webpage_data

def generate_keywords(data):

    web_data = list(itertools.chain.from_iterable(get_url_text(data)))
    all_keywords = []

    cv = CountVectorizer(strip_accents='unicode', stop_words='english', ngram_range=(1,2))
    text_transformer = cv.build_analyzer()

    transformed_text = [text_transformer(text) for text in web_data if text is not None]

    id2word = gensim.corpora.Dictionary(transformed_text)
    corpus = [id2word.doc2bow(text) for text in transformed_text]

    lda_model = gensim.models.LdaModel(
        corpus=corpus,
        id2word=id2word,
        num_topics=7,
        random_state=42,
        chunksize=20,
        passes=5,
        alpha='auto',
        update_every=0,
        minimum_probability=0.1
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
    top_words = Counter(keywords).most_common(15)
    top_words = [word[0] for word in top_words]

    return top_words

def filter_tags(df: pd.DataFrame, options: list):

    tweet_filter_list = []
    for option in options:

        r = re.compile(option, re.IGNORECASE)

        for keyword in df['keywords']:

            if r.search(keyword):
                tweet_filter_list.append(True)
                break

    return df[tweet_filter_list]

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

st.title('My Likes')

search = st.text_input('Search:')

if st.button('Generate Tags'):
    tags = generate_keywords(all_favorites)

    with open(tags_lock, 'w') as f:
        f.writelines(tags)

if os.path.exists(tags_lock):

    tags = Path(tags_lock).read_text().split('\n')
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

st.markdown(df['Favorited Tweets'].to_html(escape=False), unsafe_allow_html=True)
