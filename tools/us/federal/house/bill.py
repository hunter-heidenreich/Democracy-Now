import requests
from bs4 import BeautifulSoup


class Bill:

    ROOT_DIR = 'data/us/federal/house/bills/'

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

    def load_from_url(self, url, force_reload=False):
        cache = url.split('://')[-1].replace('/', '_')
        try:
            if force_reload:
                raise FileNotFoundError

            with open(self.ROOT_DIR + 'web/' + cache, 'r+') as in_file:
                html = in_file.read()
        except FileNotFoundError:
            html = requests.get(url).text
            with open(self.ROOT_DIR + 'web/' + cache, 'w+') as out_file:
                out_file.write(html)

        soup = BeautifulSoup(html, 'html.parser')

        self._title = next(soup.find('h1', attrs={'class': 'legDetail'}).strings)
        try:
            self._summary = soup.find('div', attrs={'id': 'bill-summary'}).find_all('p')[-1].text
        except AttributeError:
            # This seems to occur when a summary has not be generated yet
            self._summary = None
