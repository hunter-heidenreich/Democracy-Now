import requests
from bs4 import BeautifulSoup


class Bill:

    def __init__(self, url=None, filename=None):

        self._title = None
        self._summary = None

        if url:
            self.load_from_url(url)
        elif filename:
            pass
        else:
            raise ValueError('ValueError: Unspecified bill source.')

    def __repr__(self):
        if self._summary:
            return '{} ({}...)'.format(self._title, self._summary[:50])
        else:
            return self._title

    def load_from_url(self, url):
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        self._title = next(soup.find('h1', attrs={'class': 'legDetail'}).strings)
        try:
            self._summary = soup.find('div', attrs={'id': 'bill-summary'}).find_all('p')[-1].text
        except AttributeError:
            # This seems to occur when a summary has not be generated yet
            self._summary = None
