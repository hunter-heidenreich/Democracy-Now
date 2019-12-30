import json

import requests
from bs4 import BeautifulSoup

from datetime import datetime


class Bill:
    """
    Representation of a a bill, as adapted
    from the Congressional website.
    While currently fitted for the Federal
    House of Representatives in the USA
    this format may very well fit Senate bills as well.
    """

    ROOT_DIR = 'data/us/federal/house/bills/'
    ROOT_URL = 'https://www.congress.gov'

    def __init__(self, url=None, filename=None):

        self._title = None  # The title of the bill

        # The location of data sources
        # - url  -> original url scraped
        # - html -> cached html on file system
        # - json -> will link to JSON on file system
        self._sources = {}

        # Overview information available from the sources
        self._overview = {}

        # Progress of bill
        self._bill_progress = {}

        self._title_info = {}

        if url:
            self.load_from_url(url)
        elif filename:
            pass
        else:
            raise ValueError('ValueError: Unspecified bill source.')

    def __repr__(self):
        return self._title

    def load_from_url(self, url, force_reload=False):
        """
        Given a URL, this will generate the values
        for the Bill from the HTML

        :param url: The URL where the data can be found -- str
        :param force_reload: When True, this will force a refresh of that HTML
        """
        cache = url.split('://')[-1].replace('/', '_')

        self._sources['url'] = url
        self._sources['html'] = self.ROOT_DIR + 'web/' + cache

        soup = BeautifulSoup(self._get_html(force_reload), 'html.parser')

        self._title = next(
            soup.find('h1', attrs={'class': 'legDetail'}).strings)
        self._title = self._title[34:]
        self._title = self._title.split(' - ')[0]

        overview = soup.find('div', attrs={'class': 'overview'})
        self._extract_overview(overview)

        progress = soup.find('ol', attrs={'class': 'bill_progress'})
        self._extract_bill_progress(progress)

        titles = soup.find('div', attrs={'id': 'titles-content'})
        self._extract_title_info(titles)

        self.to_json()

    def _get_html(self, force_reload):
        """
        Retrieves the HTML, checking if the file is already
        available locally and abiding by whether or not a
        refresh has been requested.

        :return: The HTML data - str
        """
        try:
            if force_reload:
                raise FileNotFoundError

            with open(self._sources['html'], 'r+') as in_file:
                html = in_file.read()
        except FileNotFoundError:
            html = requests.get(url).text
            with open(self._sources['html'], 'w+') as out_file:
                out_file.write(html)

        return html

    def _extract_overview(self, overview):
        """
        Given a BeautifulSoup HTML overview extracted
        from a webpage of a Bill, this function will extract
        the available data

        :param overview: The overview box - BeautifulSoup
        """
        for i, tr in enumerate(overview.find_all('tr')):
            th = tr.find('th').text
            if th == 'Sponsor:':
                a = tr.find('a')
                self._overview['sponsor'] = {
                    'url': self.ROOT_URL + a.get('href'),
                    'name': a.text
                }
            elif th == 'Committees:':
                td = tr.find('td').text
                if 'House' in td:
                    houses = td.split(' | ')
                    house = houses.pop()
                    while 'House' not in house:
                        house = houses.pop()
                    committees = house.split('House - ')[-1].split(';')
                    self._overview['committees'] = \
                        list(map(lambda s: s.strip(), committees))
            elif th == 'Committee Reports:':
                a = tr.find('td').find('a')
                self._overview['committee_report'] = {
                    'url': self.ROOT_URL + a.get('href'),
                    'report': a.text
                }
            elif th == 'Latest Action:':
                temp = tr.find('td').text.strip()
                temp = temp.split('\xa0')[0].strip()
                temp = temp.split('(TXT | PDF)')[0].strip()
                self._overview['latest_action'] = temp

            elif th == 'Roll Call Votes:':
                tds = list(tr.find('td').strings)
                self._overview['roll call count'] = int(tds[-1].split(' ')[0])
            elif th == 'Committee Meetings:':
                self._overview['meetings'] = []
                for a in tr.find('td').find_all('a'):
                    t = a.text
                    if t == '(All Meetings)':
                        continue

                    check = int(t.split(' ')[-1].split(':')[0])
                    if check < 10:
                        chunks = t.split(' ')
                        t = chunks[0] + ' 0' + chunks[1]

                    dt = datetime.strptime(t, '%m/%d/%y %I:%M%p')
                    dt = dt.timestamp()
                    self._overview['meetings'].append({
                        'url': self.ROOT_URL + a.get('href'),
                        'datetime': dt
                    })
            elif th == 'Notes:':
                # TODO: Consider handling this differently
                # Right now, this seems to not occur for many bills
                # so it doesn't seem to relevant to write excessive code
                # for handling what's contained here,
                # other than grabbing the text
                self._overview['notes'] = tr.find('td').text
            else:
                print('New Overview in Bill Identified!')
                import pdb
                pdb.set_trace()

    def _extract_bill_progress(self, progress):
        """
        Extracts the information contained in the HTML progress bar

        :param progress: The HTML of the progress bar
        """
        # label to state
        states = {
            'passed': 1,
            'selected': 0
        }

        for li in progress.find_all('li'):
            text = next(li.strings)
            classes = li.get('class')

            if not classes:
                classes = []

            self._bill_progress[text] = -1
            for c in classes:
                if c in states:
                    self._bill_progress[text] = states[c]

    def _extract_title_info(self, titles):

        # Short title portion
        self._title_info['short'] = {}
        short = titles.find('div', attrs={'class': 'shortTitles'})
        try:
            t = None
            for i, child in enumerate(short.children):
                if i % 2 == 1:
                    if i == 3:
                        t = child.text
                    elif i == 5:
                        self._title_info['short'][t] = child.text
        except AttributeError:
            pass

        sub = titles.find('div', attrs={'class': 'titles-row'})

        hc = sub.find('div', attrs={'class': 'house-column'})
        if hc:
            h4s = list(hc.find_all('h4'))[1:]
            self._title_info['short']['house'] = {h4.text: h4.next_sibling.next_sibling.text.strip() for h4 in h4s}

        sc = sub.find('div', attrs={'class': 'senate-column'})
        if sc:
            h4s = list(sc.find_all('h4'))[1:]
            self._title_info['short']['senate'] = {h4.text: h4.next_sibling.next_sibling.text.strip() for h4 in h4s}

        self._title_info['official'] = {}
        official = titles.find('div', attrs={'class': 'officialTitles'})

        hc = official.find('div', attrs={'class': 'house-column'})
        if hc:
            h4s = list(hc.find_all('h4'))[1:]
            self._title_info['official']['house'] = {h4.text: h4.next_sibling.next_sibling.text.strip() for h4 in h4s}

        sc = official.find('div', attrs={'class': 'senate-column'})
        if sc:
            h4s = list(sc.find_all('h4'))[1:]
            self._title_info['official']['senate'] = {h4.text: h4.next_sibling.next_sibling.text.strip() for h4 in h4s}

    def to_json(self):
        """
        Dumps the Bill to a JSON readable format
        """
        filename = self._title.split(' - ')[0] + '.json'

        json.dump({
            'title': self._title,
            'sources': self._sources,
            'overview': self._overview,
            'progress': self._bill_progress,
            'title_info': self._title_info
        }, open(self.ROOT_DIR + 'json/' + filename, 'w+'))

    def from_json(self, filename):
        """
        Given a filename, reads a JSON formatted Bill
        into a Bill object

        :param filename: The location on the local disk - str
        """
        data = json.load(open(filename))
        self._title = data['title']
        self._sources = data['sources']
        self._overview = data['overview']
        self._bill_progress = data['progress']
        self._title_info = data['title_info']


if __name__ == '__main__':
    from glob import glob
    from tqdm import tqdm
    import os

    for f in tqdm(glob('data/us/federal/house/bills/web/*')):
        url = 'https://' + f.split('/')[-1].replace('_', '/')
        if 'all-info' not in url:
            os.remove(f)
            url += '/all-info'
        b = Bill(url=url)
