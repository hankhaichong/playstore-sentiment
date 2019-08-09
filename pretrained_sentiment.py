import os
import pandas as pd
import numpy as np
from tqdm import tqdm

from nltk.sentiment.vader import SentimentIntensityAnalyzer
import flair
from textblob import TextBlob
from stanfordnlp.server import CoreNLPClient
from stanfordnlp.server.client import TimeoutException

os.environ["CORENLP_HOME"] = '/Users/hchong/stanfordnlp_resources/stanford-corenlp-full-2018-10-05/'

def get_vader_sentiment_df(doc_list):

    sid = SentimentIntensityAnalyzer()

    doc_vader_sentiment_dict = dict(
        (
            x, sid.polarity_scores(x)
        ) for x in tqdm(doc_list, desc='Getting Vader Sentiment...')
    )


    return pd.DataFrame.from_dict(doc_vader_sentiment_dict, orient='Index').reset_index().rename(columns={
            'index': 'review_text',
            'neg': 'vader_neg',
            'neu': 'vader_neu',
            'pos': 'vader_pos',
            'compound': 'vader_score'
        })

def flair_get_sentiment(sent, model):

    s = flair.data.Sentence(sent)
    model.predict(s)
    sent_dict = s.labels[0].to_dict()
    sent_dict.update({
        'review_text': sent
    })
    return sent_dict

def get_flair_sentiment_df(doc_list):

    flair_sentiment_model = flair.models.TextClassifier.load('en-sentiment')
    flair_sentiment_df = pd.DataFrame(
        [flair_get_sentiment(x, flair_sentiment_model) for x in tqdm(doc_list, desc='Getting Flair Sentiment...')]
    )
    flair_sentiment_df['sentiment'] = flair_sentiment_df.apply(
        lambda x: x['confidence'] if x['value'] == 'POSITIVE' else x['confidence'] * -1,
        axis=1
    )

    return flair_sentiment_df.rename(
        columns={
            'confidence': 'flair_confidence',
            'value': 'flair_value',
            'sentiment': 'flair_sentiment'
        }
    )


get_textblob_sentiment = lambda x: [x.polarity, x.subjectivity]

def get_textblob_sentiment_full(sent):

    return [sent] + get_textblob_sentiment(
        TextBlob(
            sent
        ).sentiment
    )

get_textblob_sentiment_df = lambda doc_list: pd.DataFrame(
    [get_textblob_sentiment_full(x) for x in tqdm(doc_list, desc='Getting TextBlob Sentiment...')],
    columns=['review_text', 'textblob_polarity', 'textblob_subjectivity']
)

def serve_stanfordnlp_client():

    return CoreNLPClient(
        endpoint='http://localhost:9000',
        timeout=30000,
        threads=4,
        annotators='sentiment',
        memory='8G'
    )


def stanfordnlp_sentiment(sent, nlp_client):
    try:
        result = nlp_client.annotate(sent, properties={
            'annotators': 'sentiment',
            'outputFormat': 'json',
            'timeout': 5000,
        })

        return sent, np.array([int(s['sentimentValue']) for s in result["sentences"]]).mean()

    except TimeoutException:
        return sent, None

def get_stanfordnlp_sentiment_df(doc_list):
    
    nlp_client = serve_stanfordnlp_client()
    
    df = pd.DataFrame(
        [stanfordnlp_sentiment(x, nlp_client) for x in tqdm(doc_list, desc='Getting StanfordNLP Sentiment...')],
        columns=['review_text', 'stanford_sentiment']
    )
    
    nlp_client.stop()
    
    return df