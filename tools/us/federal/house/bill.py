import requests
from bs4 import BeautifulSoup

from representative import Representative2


class Bill:

    ROOT_DIR = 'data/us/federal/house/bills/'

    def __init__(self, url=None, filename=None):

        self._title = None
        self._summary = None

        self._sponsor = None
        self._committees = None

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

        overview = soup.find('div', attrs={'class': 'overview'})
        for i, tr in enumerate(overview.find_all('tr')):
            th = tr.find('th').text

            if th == 'Sponsor:':
                url = 'https://www.congress.gov' + tr.find('a').get('href')
                self._sponsor = Representative2(url=url)
            elif th == 'Committees:':
                td = tr.find('td').text
                if 'House' in td:
                    houses = td.split(' | ')
                    house = houses.pop()
                    while 'House' not in house:
                        house = houses.pop()
                    committees = house.split('House - ')[-1].split(';')
                    self._committees = list(map(lambda s: s.strip(), committees))
            elif th == 'Committee Reports:':
                pass
            elif th == 'Latest Action:':
                pass
            elif th == 'Roll Call Votes:':
                pass
            elif th == 'Committee Meetings:':
                pass
            elif th == 'Notes:':
                pass
            else:
                print('New Overview in Bill Identified!')
                import pdb
                pdb.set_trace()


if __name__ == '__main__':
    from glob import glob
    from tqdm import tqdm

    for f in tqdm(glob('data/us/federal/house/bills/web/*')):
        short = f.split('/')[-1]
        Bill(url=short)
