import json
import requests
from bs4 import BeautifulSoup


class Representative2:
    ROOT_DIR = 'data/us/federal/house/reps/'

    def __init__(self, url=''):
        self._name = None

        self.load(url)

    def __repr__(self):
        return self._name

    def load(self, url, force_reload=False):
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

        details = list(soup.find('h1', attrs={'class': 'legDetail'}).strings)

        self._name = details[0]


class Representative:

    ROOT_DIR = 'data/us/federal/house/reps/'

    def __init__(self, filename=None):
        # Name
        self._last_name = None
        self._first_name = None
        self._site = None

        # Location
        self._state = None
        self._district = None

        self._party = None

        # Contact
        self._office_room = None
        self._phone = None

        # Committees
        self._committees = []

        if filename:
            self.load(filename)

    def load_from_html(self, html_tr, state):
        self._state = state

        tds = list(html_tr.find_all('td'))

        self._district = tds[0].text.strip()

        name_link = tds[1].find('a')
        self._site = name_link.get('href')
        name = name_link.text.split(',')

        self._last_name = name[0].strip()
        self._first_name = name[1].strip()

        self._party = tds[2].text.strip()
        self._office_room = tds[3].text.strip()
        self._phone = tds[4].text.strip()

        for li in tds[5].find_all('li'):
            self._committees.append(li.text.strip())
        self._committees.sort()

    def __repr__(self):
        return self._first_name + ' ' + self._last_name + \
               ' ({}\'s {})\n'.format(self._state, self._district) + \
               '\tParty: {}\n'.format(self._party) + \
               '\tOffice: {}\n'.format(self._office_room) + \
               '\tNumber: {}\n'.format(self._phone) + \
               '\tWebsite: {}\n'.format(self._site) + \
               '\tCommittees: {}'.format(', '.join(self._committees))

    def save(self):
        json.dump({
            'first_name': self._first_name,
            'last_name': self._last_name,
            'state': self._state,
            'site': self._site,
            'district': self._district,
            'party': self._party,
            'office': self._office_room,
            'phone': self._phone,
            'committees': self._committees
        }, open(self.ROOT_DIR +
                '{}_{}.json'.format(self._last_name, self._first_name), 'w+'))

    def load(self, filename):
        data = json.load(open(filename))

        self._first_name = data['first_name']
        self._last_name = data['last_name']
        self._state = data['state']
        self._site = data['site']
        self._district = data['district']
        self._party = data['party']
        self._office_room = data['office']
        self._phone = data['phone']
        self._committees = data['committees']

    @property
    def state(self):
        return self._state

    @property
    def committees(self):
        return self._committees

    @property
    def party(self):
        return self._party

    @property
    def name(self):
        return self._first_name + ' ' + self._last_name
