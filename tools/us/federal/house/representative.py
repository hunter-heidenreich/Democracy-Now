import re
import json

from bs4 import BeautifulSoup
from tqdm import tqdm
from pprint import pprint

from utils import download_file, get_representative_urls


class Representative:
    ROOT_DIR = 'data/us/federal/house/reps/'

    def __init__(self, url='', filename=''):
        # The location of data sources
        # - url  -> original url scraped
        # - html -> cached html on file system
        # - json -> will link to JSON on file system
        self._sources = {}

        # Basics
        self._basics = {}

        # Overview panel
        self._overview = {}

        if url:
            self.load(url)
        elif filename:
            self.from_json(filename)

    def __repr__(self):
        return self._basics['name']

    def load(self, url, force_reload=False):
        cache = url.split('://')[-1].replace('/', '_')
        self._sources['url'] = url
        self._sources['html'] = self.ROOT_DIR + 'web/' + cache

        data = download_file(self._sources['url'], self._sources['html'],
                             force_reload)
        soup = BeautifulSoup(data, 'html.parser')

        details = soup.find('h1', attrs={'class': 'legDetail'})
        self._extract_basics(details)

        prof = soup.find('div', attrs={'class': 'overview-member-column-profile member_profile'})
        self._extract_overview(prof)

        self.to_json()

    def _extract_basics(self, details):
        """
        Extracts basic details

        :param details: BeautifulSoup details
        """
        fullname = next(details.strings).split()
        self._basics['title'] = fullname[0]
        self._basics['name'] = ' '.join(fullname[1:])

        sp = details.find('span', attrs={'class': 'birthdate'}).text.strip()
        self._basics['birth'] = int(sp[1:5])
        try:
            self._basics['death'] = int(sp[8:12])
        except ValueError:
            self._basics['death'] = None

        spans = list(details.children)
        last = spans[-1]
        self._basics['in congress'] = next(last.strings)

    def _extract_overview(self, prof):
        """
        Extracts the overview

        :param prof: The div containing the overview profile
        """
        pos, info = list(prof.find_all('table'))

        # Extract position information
        labels = [th.text.strip() for th in pos.find_all('th')]
        body = pos.find('tbody')

        self._overview['positions'] = []
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

            self._overview['positions'].append(p)

        # Extract other info
        self._overview['info'] = {}
        for tr in info.find_all('tr'):
            th = tr.find('th').text.strip()
            td = tr.find('td')

            if th == 'Website':
                self._overview['info']['website'] = td.find('a').get('href')
            elif th == 'Party':
                self._overview['info']['party'] = td.text.strip()
            elif th == 'Contact':
                self._overview['info']['contact'] = [
                    s.strip() for s in td.strings
                ]
            elif th == 'Party History  in Congress':
                self._overview['info']['party history'] = [
                    s.strip() for s in td.strings
                ]
            else:
                print('New Info!')
                import pdb
                pdb.set_trace()

    def to_json(self):
        """
        Dumps the Representative to a JSON readable format
        """
        filename = '{}.json'.format(self._basics['name'])
        self._sources['json'] = self.ROOT_DIR + 'json/' + filename
        json.dump({
            'sources': self._sources,
            'basics': self._basics,
            'overview': self._overview
        }, open(self.ROOT_DIR + 'json/' + filename, 'w+'))

    def from_json(self, filename):
        """
        Given a filename, reads a JSON formatted Representative
        into a Representative object

        :param filename: The location on the local disk - str
        """
        data = json.load(open(filename))

        self._sources = data['sources']
        self._basics = data['basics']
        self._overview = data['overview']

    def get_sources(self):
        return self._sources

    def get_overview(self):
        return self._overview

    def get_current_party(self):
        """
        Gets the current party affiliation of a representative
        """
        if 'party' in self._overview['info']:
            return self._overview['info']['party']
        elif 'party history' in self._overview['info']:
            for text in self._overview['info']['party history']:
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
        for p in self._overview['positions']:
            if not p['In Congress']['end']:
                return p['State']
        return None

    def get_district(self):
        """
        Returns the current district serving in
        """
        for p in self._overview['positions']:
            if not p['In Congress']['end']:
                try:
                    return p['District']
                except KeyError:
                    import pdb
                    pdb.set_trace()
        return None

    def print(self):
        """
        Pretty prints the representative
        """
        pprint(self._basics)
        pprint(self._sources)
        pprint(self._overview)

    def search(self, key, value):
        """
        Given a key/property and an intended value,
        returns True if this rep has the intended value
        :param key: A string property
        :param value: The value searched for
        :return: True or False if this rep is part of the search
        """

        if key == 'source':
            return value in self._sources.values()
        elif key == 'name':
            return value == self._basics['name']
        elif key == 'chamber':
            if value == 'House':
                return self._basics['title'] == 'Representative'
            elif value == 'Senate':
                return self._basics['title'] == 'Senator'
        elif key == 'alive':
            return not self._basics['death'] == value
        elif key == 'party':
            return value == self.get_current_party()
        elif key == 'state':
            return value == self.get_state()
        elif key == 'district':
            state, dist = value
            return state == self.get_state() and dist == self.get_district()
        else:
            print('Unknown property for representative. Returning False')

        return False


if __name__ == '__main__':
    new, old = get_representative_urls()
    for url in tqdm(new):
        Representative(url=url)
