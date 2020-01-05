import re
import json
import datetime
import requests

from glob import glob
from bs4 import BeautifulSoup
from tqdm import tqdm
from pprint import pprint

import us
import pylcs

from utils import download_file, get_representative_urls
from bill import Bill


class Representative:
    ROOT_DIR = 'data/us/federal/house/reps/'
    ROOT_URL = 'https://www.congress.gov/'

    def __init__(self, url='', filename=''):
        # The location of data sources
        # - url  -> original url scraped
        # - html -> cached html on file system
        # - json -> will link to JSON on file system
        self.sources = {}

        # Basics
        self.basics = {}

        # Overview panel
        self.overview = {}

        if url:
            self.load(url)
        elif filename:
            self.from_json(filename)

    def __repr__(self):
        return '{} {} - {} ({}-{})'.format(self.basics['title'],
                                           self.basics['name'],
                                           self.get_current_party(),
                                           self.get_state(),
                                           self.get_district())

    def load(self, url, force_reload=False):
        cache = url.split('://')[-1].replace('/', '_')
        self.sources['url'] = url
        self.sources['html'] = self.ROOT_DIR + 'web/' + cache

        data = download_file(self.sources['url'], self.sources['html'],
                             force_reload)
        soup = BeautifulSoup(data, 'html.parser')

        details = soup.find('h1', attrs={'class': 'legDetail'})
        self._extractbasics(details)

        prof = soup.find('div', attrs={'class': 'overview-member-column-profile member_profile'})
        self._extract_overview(prof)

        pic = soup.find('div', attrs={'class': 'overview-member-column-picture'})
        try:
            self.sources['img'] = self.ROOT_URL + pic.find('img').get('src')
        except AttributeError:
            self.sources['img'] = None

        self.to_json()

    def _extractbasics(self, details):
        """
        Extracts basic details

        :param details: BeautifulSoup details
        """
        fullname = next(details.strings).split()
        self.basics['title'] = fullname[0]
        self.basics['name'] = ' '.join(fullname[1:])

        sp = details.find('span', attrs={'class': 'birthdate'}).text.strip()
        self.basics['birth'] = int(sp[1:5])
        try:
            self.basics['death'] = int(sp[8:12])
        except ValueError:
            self.basics['death'] = None

        spans = list(details.children)
        last = spans[-1]
        self.basics['in congress'] = next(last.strings)

    def _extract_overview(self, prof):
        """
        Extracts the overview

        :param prof: The div containing the overview profile
        """
        pos, info = list(prof.find_all('table'))

        # Extract position information
        labels = [th.text.strip() for th in pos.find_all('th')]
        body = pos.find('tbody')

        self.overview['positions'] = []
        for tr in body.find_all('tr'):
            p = {}
            for lab, td in zip(labels, tr.find_all('td')):
                p[lab] = td.text.strip()

            # Handle extracting total congressional position timing
            text = p['In Congress']
            chamber, rest = text.split(': ')
            cong, years = rest.split()

            congs = list(map(lambda s: int(s[:-2]),
                             re.findall('\d*[a-z]{2}', cong)))

            years = years[1:-1]
            try:
                start, end = years.split('-')
            except ValueError:
                start = years
                end = years

            d = {
                'chamber': chamber,
                'start': int(start),
                'end': None if 'Present' == end else int(end),
                'congresses': list(range(congs[0], congs[1] + 1)) if len(
                    congs) == 2 else [congs[0]]
            }

            p['In Congress'] = d

            self.overview['positions'].append(p)

        # Extract other info
        self.overview['info'] = {}
        for tr in info.find_all('tr'):
            th = tr.find('th').text.strip()
            td = tr.find('td')

            if th == 'Website':
                self.overview['info']['website'] = td.find('a').get('href')
            elif th == 'Party':
                self.overview['info']['party'] = td.text.strip()
            elif th == 'Contact':
                self.overview['info']['contact'] = [
                    s.strip() for s in td.strings
                ]
            elif th == 'Party History  in Congress':
                self.overview['info']['party history'] = [
                    s.strip() for s in td.strings
                ]
            else:
                print('New Info!')
                import pdb
                pdb.set_trace()

    def download_all_bills(self):
        pg = 1
        urls = set()

        lns = -1
        while len(urls) % 100 == 0 and lns != len(urls):
            lns = len(urls)
            html = requests.get(
                self.sources['url'] + '?page={}'.format(pg)).text
            soup = BeautifulSoup(html, 'html.parser')

            for sp in soup.find_all('span', attrs={'class': 'result-heading'}):
                url = sp.find('a').get('href')
                url = url.split('?')[0] + '/all-info'
                urls.add(url)

            pg += 1

        old_urls = set()
        for f in tqdm(glob('data/us/federal/house/bills/json/*.json')):
            data = json.load(open(f))

            if 'all-info' not in data['sources']['url']:
                old_urls.add(data['sources']['url'] + '/all-info')
            else:
                old_urls.add(data['sources']['url'])

        new_urls = urls - old_urls
        for u in tqdm(new_urls):
            Bill(url=u)

    def refresh(self, force_reload=False):
        """
        A soft refresh

        :param force_reload: Whether or not to perform a hard refresh
        """
        self.load(self.sources['url'], force_reload=force_reload)

    def to_json(self):
        """
        Dumps the Representative to a JSON readable format
        """
        filename = '{}.json'.format(self.basics['name'])
        self.sources['json'] = self.ROOT_DIR + 'json/' + filename
        json.dump({
            'sources': self.sources,
            'basics': self.basics,
            'overview': self.overview
        }, open(self.ROOT_DIR + 'json/' + filename, 'w+'))

    def from_json(self, filename):
        """
        Given a filename, reads a JSON formatted Representative
        into a Representative object

        :param filename: The location on the local disk - str
        """
        data = json.load(open(filename))

        self.sources = data['sources']
        self.basics = data['basics']
        self.overview = data['overview']

    def get_sources(self):
        return self.sources

    def get_overview(self):
        return self.overview

    def get_current_party(self):
        """
        Gets the current party affiliation of a representative
        """
        if 'party' in self.overview['info']:
            return self.overview['info']['party']
        elif 'party history' in self.overview['info']:
            for text in self.overview['info']['party history']:
                pa, time = text.split()
                if 'Present' in time:
                    return pa
            return None
        else:
            import pdb
            pdb.set_trace()

    def get_state(self):
        """
        Returns the current state serving in
        """
        for p in self.overview['positions']:
            if not p['In Congress']['end']:
                return p['State']
        return None

    def get_district(self):
        """
        Returns the current district serving in
        """
        for p in self.overview['positions']:
            if not p['In Congress']['end']:
                try:
                    return p['District']
                except KeyError:
                    return None
        return None

    def get_active(self):
        """
        Returns true if active
        """
        for p in self.overview['positions']:
            if not p['In Congress']['end']:
                return True

        return False

    def get_age(self):
        """
        Returns the age of the representative
        """
        if self.basics['death']:
            return self.basics['death'] - self.basics['birth']
        else:
            return datetime.datetime.now().year - self.basics['birth']

    def get_service(self):
        """
        Returns the # of years served
        """
        yrs = 0
        for pos in self.overview['positions']:
            pos = pos['In Congress']
            if pos['end']:
                yrs += pos['end'] - pos['start']
            else:
                yrs += datetime.datetime.now().year - pos['start']

        return yrs

    def print(self):
        """
        Pretty prints the representative
        """
        pprint(self.basics)
        pprint(self.sources)
        pprint(self.overview)

    def search(self, key, value):
        """
        Given a key/property and an intended value,
        returns True if this rep has the intended value
        :param key: A string property
        :param value: The value searched for
        :return: True or False if this rep is part of the search
        """

        if key == 'source':
            return value in self.sources.values()
        elif key == 'name':
            v = value.lower()
            v = ''.join([let for let in v if 'a' <= let <= 'z'])
            name = self.basics['name'].lower()
            name = ''.join([let for let in name if 'a' <= let <= 'z'])
            lcs = pylcs.lcs(v, name)
            return lcs == len(v)
        elif key == 'chamber':
            if value == 'House':
                return self.basics['title'] == 'Representative'
            elif value == 'Senate':
                return self.basics['title'] == 'Senator'
        elif key == 'alive':
            return not self.basics['death'] == value
        elif key == 'party':
            return value == self.get_current_party()
        elif key == 'state':
            state = us.states.lookup(value).name
            return state == self.get_state()
        elif key == 'district':
            state, dist = value
            state = us.states.lookup(state).name
            return state == self.get_state() and dist == self.get_district()
        elif key == 'active':
            return value == self.get_active()
        else:
            print('Unknown property for representative. Returning False')

        return False


if __name__ == '__main__':
    new, old = get_representative_urls()
    for url in tqdm(new):
        Representative(url=url)

    for url in tqdm(old):
        Representative(url=url).refresh()
