from bs4 import BeautifulSoup
import requests

from collections import defaultdict
from glob import glob

import pdb

from representative import Representative


class USHouse:

    ROOT_URL = 'https://www.house.gov/'

    def __init__(self, load=True):
        self._reps = []

        self._by_state = defaultdict(list)
        self._by_committee = defaultdict(list)
        self._by_party = defaultdict(list)
        self._by_name = {}

        if load:
            self.load_reps()
        else:
            self.download_reps()

        self.load_by_state()
        self.load_by_committee()
        self.load_by_party()
        self.load_by_name()

    def load_reps(self):
        for f in glob(Representative.ROOT_DIR + '*.json'):
            self._reps.append(Representative(filename=f))

    def load_by_state(self):
        for rep in self._reps:
            self._by_state[rep.state].append(rep)

    def load_by_committee(self):
        for rep in self._reps:
            for comm in rep.committees:
                self._by_committee[comm].append(rep)

    def load_by_party(self):
        for rep in self._reps:
            self._by_party[rep.party].append(rep)

    def load_by_name(self):
        for rep in self._reps:
            self._by_name[rep.name] = rep

    def download_reps(self):
        target_url = self.ROOT_URL + 'representatives'
        soup = BeautifulSoup(requests.get(target_url).text, features='html.parser')
        tables = soup.find_all('table', class_='table')

        current_state = None
        for table in tables:
            for i, c in enumerate(table.children):
                if i == 1:
                    current_state = c.text.strip()
                elif i == 5:
                    for tr in c.find_all('tr'):
                        r = Representative()
                        try:
                            r.load_from_html(tr, current_state)
                            r.save()
                            self._reps.append(r)
                        except AttributeError:
                            pass

    def lookup_rep(self, name):
        try:
            return self._by_name[name]
        except KeyError:
            return None


if __name__ == '__main__':
    house = USHouse(load=True)
    pdb.set_trace()
