import asyncio
import re
from contextlib import closing

import click
from bs4 import BeautifulSoup, Comment, Tag
from requests import get
from requests.exceptions import RequestException

MENU_CHECK = ['sidebar', 'menu', 'dropdown']

@click.command()
@click.option('-o', '--output-file', help='Name and location of the file')
@click.argument('urls')
def scrape(urls, output_file=''):
    webscrape(urls, output_file=output_file)

def webscrape(*urls, output_file=''):
    """
    Gets all the text from a webpage.

    Parameters
    ----------
    urls : str
        Urls to scrape
    output_file : str, optional
        output file name/location, by default cwd
    """

    for url in urls:
        output_file = f'{url.split(".")[1]}.txt' 
        raw_html = _simple_get(url)

        try:
            soup = BeautifulSoup(raw_html, 'html.parser')
            soup = soup.body

            # Delete any comments
            for comments in soup.findAll(text=lambda text: isinstance(text, Comment)):
                comments.decompose()

            # kill all script and style elements
            for script in soup(["header", "fotter", "script", "style", "code"]):
                script.decompose()    # rip it out

            # Remove any menus from the html
            for div in soup.find_all('div'):
                if isinstance(div, Tag):
                    if div.attrs:
                        if 'class' in div.attrs:
                            for menu_item in MENU_CHECK:                        
                                if menu_item in " ".join(div.attrs['class']):
                                    div.decompose()
                                    break
            
            # Clean up text from raw html a little
            cleaned_content = list(map(lambda x: re.sub('\s+', ' ', x).strip(), soup.find_all(text=True)))
            
            return (" ".join(filter(lambda x: x != '', cleaned_content))).strip()

        except:
            return ""


def _simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if _is_good_response(resp):
                return resp.content 
            else:
                return None 

    except RequestException as e:
        _log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def _is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def _log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)
