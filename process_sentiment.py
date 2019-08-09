import pandas as pd
from datetime import datetime
import re
import sys

from pretrained_sentiment import (
    get_vader_sentiment_df,
    get_flair_sentiment_df,
    get_textblob_sentiment_df,
    get_stanfordnlp_sentiment_df
)

def main(argv):

    review_filename = argv[0]
    save_filename = review_filename[:-4] + '_process_' + re.sub('-', '', str(datetime.utcnow().date())) + '.csv'
    df = pd.read_csv(
        review_filename,
        keep_default_na=False
    )
    doc_list = list(
        set(
            review_df[
                review_df.review_text != ''
            ].review_text.tolist()
        )
    )
    vader_sentiment_df = get_vader_sentiment_df(doc_list)
    flair_sentiment_df = get_flair_sentiment_df(doc_list)
    textblob_sentiment_df = get_textblob_sentiment_df(doc_list)
    stanfordnlp_sentiment_df = get_stanfordnlp_sentiment_df(doc_list)

    df.merge(
        vader_sentiment_df, how='left'
    ).merge(
        flair_sentiment_df, how='left'
    ).merge(
        textblob_sentiment_df, how='left'
    ).merge(
        stanfordnlp_sentiment_df, how='left'
    ).to_csv(save_filename, index=False)


if __name__ == "__main__":
    main(sys.argv[1:])