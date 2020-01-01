Toot
---
If you're like me and use Twitter to keep up with researchers, blog posts and members of the Data Science & ML community in general, you might find yourself liking tweets to read later or for when you need a post when you're working on a relevant problem.

Well then you'll also know, the number of likes start to grow quickly and searching/filtering through all the likes to find the relevant likes you need, when you need them, is a pain. Hence, the use case for this quick app. Due to the simplicity of this app, I decided to build it with quickly with Streamlit.

![image](https://user-images.githubusercontent.com/9558507/71452195-7874aa00-2750-11ea-81f8-51153e593eb3.png)

Features
--------

- Generate topics from tweets
- Filter based on tweet topic
- Regex search
- Click directly on links to blogs, links, pdfs, etc.

Usage
---

You will need a Twitter API consumer key as well as Twitter App access token. You can get all of those here: https://developer.twitter.com/en/apply-for-access.html

To edit the number of times between api requests to twitter, change the `REQUEST_TIME_LIMIT` variable (default is 60min).

### DockerHub

You can pull a stock image from Docker Hub by running the following:

`docker pull bigsidhu/toot`

```bash
docker run -d --name `container_name` -p 8501:8501 \
-e CONSUMER_KEY=`your_twitter_consumer_key` \
-e CONSUMER_SECRET=`your_twitter_consumer_secret` \
-e ACCESS_TOKEN=`your_twitter_access_token` \
-e ACCESS_TOKEN_SECRET=`your_access_token_secret` \
-e REQUEST_TIME_LIMIT="30" bigsidhu/toot
```

### Docker
You can start it as a docker instance by running the following:

`docker build -t toot .`

```bash
docker run -d --name `container_name` -p 8501:8501 \
-e CONSUMER_KEY=`your_twitter_consumer_key` \
-e CONSUMER_SECRET=`your_twitter_consumer_secret` \
-e ACCESS_TOKEN=`your_twitter_access_token` \
-e ACCESS_TOKEN_SECRET=`your_access_token_secret` \
-e REQUEST_TIME_LIMIT="30" toot
```

### Locally
Add your twitter api keys in the source code or as environment variables and running:

```bash
pip install -r requirements.txt
streamlit run toot/toot.py
```

To background the process `nohup streamlit run toot/toot.py &` or a schtask on Windows.

Then access it by going to http://localhost:8501.

Coming Soon
---
I'll update this repo periodically and will add the following features:

- [x] Reduced loading time
- [x] Topic Filtering
- [x] Add account of tweet that is favourited
- [x] Image on Dockerhub
