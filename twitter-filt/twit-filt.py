import os
import re

import pandas as pd
import streamlit as st
import tweepy

CONSUMER_KEY = os.environ.get('CONSUMER_KEY', None)
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', None)
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', None)
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', None)

if not CONSUMER_KEY and not CONSUMER_SECRET and not ACCESS_TOKEN and not ACCESS_TOKEN_SECRET:
    raise ValueError('Consumer and Access keys and secrets must be set as environment variables.')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

API = tweepy.API(auth)

def get_data():

    return list(tweepy.Cursor(API.favorites).items())

def filter_tweets(tweets: list, word: str):

    r = re.compile(word, re.IGNORECASE)

    return list(filter(r.search, tweets))

def highlight_urls(text):

    r = re.compile('https?:\/\/[A-Za-z0-9]*\.[a-z]*\/[A-Za-z0-9]*')
    links = r.findall(text)

    for link in links:
        text = text.replace(link, '<a href="{0}">{0}</a>'.format(link))

    return text

st.title('My Likes')

all_favorites = [fav.text for fav in get_data()]

search = st.text_input('Search:')

if not search:
    favorites = all_favorites
else:
    favorites = filter_tweets(all_favorites, search)

df = pd.DataFrame(favorites, columns=['Favorited Tweets'])
df['Favorited Tweets'] = list(map(highlight_urls, df['Favorited Tweets']))

st.markdown(df.to_html(escape=False), unsafe_allow_html=True)
