import datetime
import os
import re

import pandas as pd
import streamlit as st
import tweepy

CONSUMER_KEY = os.environ.get('CONSUMER_KEY', None)
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', None)
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', None)
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', None)
REQUEST_TIME_LIMIT = int(os.environ.get('REQUEST_TIME_LIMIT', 20)) # in minutes

if not CONSUMER_KEY and not CONSUMER_SECRET and not ACCESS_TOKEN and not ACCESS_TOKEN_SECRET:
    raise ValueError('Consumer and Access keys and secrets must be set as environment variables.')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

API = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

path = os.path.join(os.path.expanduser('~'), '.twitfilt')
if not os.path.exists(path):
    os.makedirs(path)

@st.cache(show_spinner=True)
def load_tweets(time):

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

def write_current_date(cur_time=None):

    if not cur_time:
        time = datetime.datetime.now()
    else:
        time = cur_time

    with open(os.path.join(path, 'request.lock'), 'w') as f:
        f.write(str(time))

    return time    

# This block uses a time lock to limit the requests when loading/ searching tweets
#    1. If this is first time use, write the current time to the lock file and load the tweets
#    2. Upon further use, if the time in lock file and the current time is greater than 15min (editable) then get the tweets with the current time
#    3. If it is < 15min get the tweets using the time from the lock file taking advantage of streamlit caching to not send an api request
if not os.path.exists(os.path.join(path, 'request.lock')):
    time = write_current_date()
    
    data = load_tweets(time)
else:
    with open(os.path.join(path, 'request.lock'), 'r') as f:
        r_time = f.read()

    time = datetime.datetime.strptime(r_time, '%Y-%m-%d %H:%M:%S.%f')
    cur_time = datetime.datetime.now()

    if ((cur_time - time).seconds / 60) > REQUEST_TIME_LIMIT:
        data = load_tweets(cur_time)
        write_current_date(cur_time)
    else:
        data = load_tweets(r_time)

all_favorites = [fav.text for fav in data]

st.title('My Likes')

search = st.text_input('Search:')

if not search:
    favorites = all_favorites
else:
    favorites = filter_tweets(all_favorites, search)

df = pd.DataFrame(favorites, columns=['Favorited Tweets'])
df['Favorited Tweets'] = list(map(highlight_urls, df['Favorited Tweets']))

st.markdown(df.to_html(escape=False), unsafe_allow_html=True)
