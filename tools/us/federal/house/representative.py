from bs4 import BeautifulSoup

from utils import download_file


class Representative:
    ROOT_DIR = 'data/us/federal/house/reps/'

    def __init__(self, url=''):
        self._name = None

        # The location of data sources
        # - url  -> original url scraped
        # - html -> cached html on file system
        # - json -> will link to JSON on file system
        self._sources = {}

        self.load(url)

    def __repr__(self):
        return self._name

    def load(self, url, force_reload=False):
        cache = url.split('://')[-1].replace('/', '_')
        self._sources['url'] = url
        self._sources['html'] = self.ROOT_DIR + 'web/' + cache

        data = download_file(self._sources['url'], self._sources['html'],
                             force_reload)
        soup = BeautifulSoup(data, 'html.parser')

        details = list(soup.find('h1', attrs={'class': 'legDetail'}).strings)

        self._name = details[0]
