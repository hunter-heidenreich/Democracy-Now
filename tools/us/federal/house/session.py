import datetime

import requests
from bs4 import BeautifulSoup

from tqdm import tqdm

from vote import Vote
from bill import Bill


class ActionItem:

    def __init__(self, title, item):
        self._title = title

        self._text = None
        self._link = None
        self._type = None
        self._data = None

        if item:
            self._text = item.text
            self._link = item.get('href')
            self._type = item.get('rel')

            if self._type == 'vote':
                self._data = Vote(url=self._link)
            elif self._type == 'bill':
                self._data = Bill(url=self._link)

    def __repr__(self):
        if self._type:
            return '{} ({}) {}'.format(self._title, self._type, self._data)
        else:
            return self._title

    @property
    def item_type(self):
        return self._type


class FloorAction:

    def __init__(self, data):

        time = data.find('action_time').get('for-search').split('T')[-1].split(':')
        self._time = datetime.time(hour=int(time[0]),
                                   minute=int(time[1]),
                                   second=int(time[2]))
        self._unique_id = data.get('unique-id')
        self._act_id = data.get('act-id')
        self._description = data.find('action_description').text.strip()

        self._item = None
        if data.find('action_item'):
            self._item = ActionItem(data.find('action_item').text,
                                    data.find('action_description').find('a'))

    def __repr__(self):
        if self._item:
            return 'Floor Action (ID {}, {}) -- {}'.format(self._act_id,
                                                           self._time,
                                                           self._item)
        return 'Floor Action (ID {}, {})'.format(self._act_id, self._time)

    @property
    def action_type(self):
        if self._item:
            return self._item.item_type
        else:
            return None


class LegislativeActivity:

    def __init__(self, data):

        self._header = data.find('legislative_header').text
        self._lang = data.find('language').text

        date = data.find('legislative_day').get('date')
        self._date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:]))

        print('Legislative Action: {}'.format(self._date))

        self._floor_actions = []

        actions = data.find('floor_actions')
        for action in tqdm(actions.find_all('floor_action')):
            self._floor_actions.append(FloorAction(action))

    def __repr__(self):
        return 'Legislative Activity: {}'.format(self._date) + '\n' \
               + self.get_votes_as_text() + '\n' + self.get_bills_as_text()

    def get_votes(self):
        return [act for act in self._floor_actions if
                act.action_type == 'vote']

    def get_votes_as_text(self):
        return '\n'.join(['Votes: '] + ['\t' + v.__repr__() for v in self.get_votes()])

    def get_bills(self):
        return [act for act in self._floor_actions if
                act.action_type == 'bill']

    def get_bills_as_text(self):
        return '\n'.join(
            ['Bills: '] + ['\t' + b.__repr__() for b in self.get_bills()])

    def get_types(self):
        return set([act.action_type for act in self._floor_actions])


class Session:

    ROOT_URL = 'http://clerk.house.gov/floorsummary/'
    ROOT_DIR = 'data/us/federal/house/session/'

    def __init__(self, source='', force_reload=False):

        self._congress = None
        self._session = None
        self._source = source
        self._activities = []

        self.load(force_reload=force_reload)

    def load(self, force_reload=False):
        try:
            if force_reload:
                raise FileNotFoundError

            with open(self.ROOT_DIR + 'web/' + self._source, 'r+') as infile:
                xml = infile.read()
        except FileNotFoundError:
            # TODO: Verify if this char issue is just an issue with 2019 data
            xml = requests.get(self.ROOT_URL + self._source).text[3:]

            with open(self.ROOT_DIR + 'web/' + self._source, 'w+') as out_file:
                out_file.write(xml)

        soup = BeautifulSoup(xml, 'xml')

        self._congress = soup.find('congress').text
        self._session = soup.find('session').text

        for leg in soup.find_all('legislative_activity'):
            self._activities.append(LegislativeActivity(leg))

    def __repr__(self):
        return 'US House #{} - Session {}'.format(self._congress,
                                                  self._session)
