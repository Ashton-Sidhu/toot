Twitter-Filter
---
If you're like me and use Twitter to keep up with researchers, blog posts and members of the Data Science & ML community in general, you might find yourself liking tweets to read later or for when you need a post when you're working on a relevant problem.

Well then you'll also know, the number of likes start to grow quickly and searching/filtering through all the likes to find the relevant likes you need, when you need them, is a pain. Hence, the use case for this quick app. Due to the simplicity of this app, I decided to build it with quickly with Streamlit.

![image](https://user-images.githubusercontent.com/9558507/68728805-50f9c180-0596-11ea-9e1c-19df8aabf4a4.png)

Usage
---

You will need a Twitter API consumer key as well as Twitter App access token. You can get all of those here: https://developer.twitter.com/en/apply-for-access.html 

You can start it as a docker instance by running the following.

`docker build -t twitter-filt .`

`docker run -d -p 8501:8501 -e CONSUMER_KEY="your_twitter_consumer_key" -e CONSUMER_SECRET="your_twitter_consumer_secret" -e ACCESS_TOKEN="your_twitter_access_token" -e ACCESS_TOKEN_SECRET="your_access_token_secret" twitter-filt` and then going to http://localhost:8501.

or by adding your keys in the source code or as environment variables and running:

`streamlit run twitter-filt/twit-filt.py`

Coming Soon
---
I'll update this repo periodically and will add the following features:

- [ ] Topic Filtering
- [ ] Add account of tweet that is favourited
