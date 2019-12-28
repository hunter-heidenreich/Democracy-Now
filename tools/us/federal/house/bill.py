import requests
from bs4 import BeautifulSoup

from datetime import datetime

from representative import Representative2


class Bill:

    ROOT_DIR = 'data/us/federal/house/bills/'

    def __init__(self, url=None, filename=None):

        self._title = None
        self._summary = None

        self._sponsor = None
        self._committees = None
        self._committee_report = None

        self._latest_action = None

        self._num_rollcall_votes = 0

        self._meetings = []

        self._notes = None

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
                a = tr.find('td').find('a')
                self._committee_report = {
                    'url': 'https://www.congress.gov' + a.get('href'),
                    'report': a.text
                }
            elif th == 'Latest Action:':
                # TODO: Do we want to handle the extra text?
                self._latest_action = tr.find('td').text
            elif th == 'Roll Call Votes:':
                tds = list(tr.find('td').strings)
                self._num_rollcall_votes = int(tds[-1].split(' ')[0])
            elif th == 'Committee Meetings:':
                for a in tr.find('td').find_all('a'):
                    t = a.text
                    if t == '(All Meetings)':
                        continue

                    check = int(t.split(' ')[-1].split(':')[0])
                    if check < 10:
                        chunks = t.split(' ')
                        t = chunks[0] + ' 0' + chunks[1]

                    self._meetings.append({
                        'url': 'https://www.congress.gov' + a.get('href'),
                        'datetime': datetime.strptime(t, '%m/%d/%y %I:%M%p')
                    })
            elif th == 'Notes:':
                # TODO: Consider handling this differently
                # Right now, this seems to not occur for many bills
                # so it doesn't seem to relevant to write excessive code
                # for handling what's contained here,
                # other than grabbing the text
                self._notes = tr.find('td').text
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
