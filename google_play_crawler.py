from selenium import webdriver
import selenium.webdriver.chrome.service as service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
import time
from bs4 import BeautifulSoup
import pandas as pd
from dateutil import parser, rrule
from datetime import datetime, timedelta
import sys
import re
from tqdm import tqdm

SCROLL_PAUSE_TIME = 0.5

def extract_reviews(soup_input):
    review_dict = {
        'reviewer_name': soup_input.find('span', class_='X43Kjb').get_text(),
        'num_stars': int(soup_input.find('div', class_='pf5lIe').contents[0]['aria-label'][6:7]),
        'review_date': parser.parse(soup_input.find('span', class_='p2TkOb').get_text()),
        'num_useful': int(soup_input.find('div', class_='jUL89d y92BAb').contents[0])
    }
    if soup_input.find('span', jsname='fbQN7e').get_text() == '':
        review_text = soup_input.find('span', jsname='bN97Pc').get_text()
    else:
        review_text = soup_input.find('span', jsname='fbQN7e').get_text()
    
    review_dict.update(
        {'review_text': review_text}
    )
    
    return review_dict

def review_save(review_list, filename):

    review_df = pd.DataFrame(review_list)
    review_df['review_week'] = review_df.review_date - pd.to_timedelta(review_df['review_date'].dt.dayofweek, unit='d')
    review_df['review_month'] = review_df.review_date.apply(
        lambda x: x.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    )

    review_df.to_csv(filename)

def main(argv):
    
    crawling_start = time.time()
    app_id = argv[0]
    file_app_name = argv[1]
    url = f"https://play.google.com/store/apps/details?id={app_id}&showAllReviews=true"
    
    # setting up selenium driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_service = service.Service('/Users/hchong/Downloads/chromedriver')
    chrome_service.start()
    capabilities = DesiredCapabilities.CHROME.copy()
    driver = webdriver.Remote(chrome_service.service_url, capabilities, options=chrome_options)
    driver.get(url)
    
    # expanding to get all reviews
    # Get scroll height
    scrolling_start = time.time()
    last_height = driver.execute_script("return document.body.scrollHeight")
    i = 0
    j = 0
    while True:
        i += 1
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if i % 50 == 0:
            print(f"Iteration {i}: Page height is {new_height}")
        if new_height == last_height:
            j += 1
            try:
                driver.execute_script(
                    "arguments[0].click();",
                    driver.find_element_by_xpath("//*[contains(@class,'U26fgb O0WRkf oG5Srb C0oVfc n9lfJ')]")
                )
            except:
                next
        else:
            j = 0
        if j == 10:  # if the height did not change for 10 iterations, quit
            break
        last_height = new_height
    print(f'Scrolling till the end took {str(timedelta(seconds=round(time.time() - scrolling_start)))}.')
    
    # finding elements of reviews and parsing html    
    review_elem_list = driver.find_elements_by_xpath("//*[@jsname='fk8dgd']//div[@class='d15Mdf bAhLNe']")
    review_list_soup = []
    problem = []
    for i,x in enumerate(tqdm(review_elem_list, desc='Extracting review soup...')):
        try:
            review_list_soup.append(
                BeautifulSoup(x.get_attribute('outerHTML'), 'html.parser')
            )
        except Exception as e:
            print(e)
            problem.append(
                (i,x)
            )
            
    # extracting reviews from the parsed html
    review_list = []
    for i,x in enumerate(tqdm(review_list_soup, desc='Extracting reviews...')):
        try:
            review_list.append(extract_reviews(x))
        except Exception as e:
            print(e)
            next
            
    filename = f"/Users/hchong/Documents/crawler/{file_app_name}_review_{re.sub('-', '', str(datetime.utcnow().date()))}.csv"
    review_save(review_list, filename)
    print(f'Crawling took {str(timedelta(seconds=round(time.time() - crawling_start)))}.')
    
    
if __name__ == "__main__":
    main(sys.argv[1:])