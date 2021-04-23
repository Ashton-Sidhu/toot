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

You will need an ElasticSearch instance with all your twitter data.

To edit the number of times between api requests to twitter, change the `REQUEST_TIME_LIMIT` variable (default is 60min).

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
