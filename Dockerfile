FROM python:3.7

RUN mkdir src/
COPY . src/
WORKDIR src/
RUN pip3 install -r requirements.txt

EXPOSE 8501

CMD streamlit run twitter-filt/twit-filt.py
