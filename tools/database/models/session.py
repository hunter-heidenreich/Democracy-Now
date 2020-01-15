import json
import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class Session:

    """
    A legislative session taken from the house clerk
    formatted as an XML
    """

    ROOT_URL = 'http://clerk.house.gov/floorsummary/'
    ROOT_DIR = 'data/us/federal/house/session/'

    def __init__(self, url='', filename='', force_reload=False):

        self._overview = {}

        self._sources = {
            'url': url,
            'xml': url
        }
        self._activities = []

        if url:
            self.load(force_reload=force_reload)
        elif filename:
            self.from_json(filename)

    def load(self, force_reload=False):
        """
        Loads from the URL
        :param force_reload: Whether or not to force a refresh
        """
        try:
            if force_reload:
                raise FileNotFoundError

            with open(self.ROOT_DIR + 'web/' + self._sources['xml'], 'r+') as infile:
                xml = infile.read()
        except FileNotFoundError:
            # TODO: Verify if this char issue is just an issue with 2019 data
            xml = requests.get(self.ROOT_URL + self._sources['url']).text[3:]

            with open(self.ROOT_DIR + 'web/' + self._sources['xml'], 'w+') as out_file:
                out_file.write(xml)

        soup = BeautifulSoup(xml, 'xml')

        self._overview = {
            'congress': soup.find('congress').text,
            'session': soup.find('session').text
        }

        for leg in soup.find_all('legislative_activity'):
            self._extract_leg_act(leg)

        self.to_json()

    def _extract_leg_act(self, leg):
        """
        Extracts the information from a legislative activity

        :param leg: The portion of the XML that's activity
        """
        date = leg.find('legislative_day').get('date')
        dt = datetime.datetime(int(date[0:4]), int(date[4:6]),
                               int(date[6:]))
        _overview = {
            'header': leg.find('legislative_header').text,
            'lang': leg.find('language').text,
            'time': dt.timestamp()
        }

        print('Legislative Action: {}'.format(dt))

        _floor_actions = []

        actions = leg.find('floor_actions')
        for action in tqdm(actions.find_all('floor_action')):
            d = self._extract_floor_act(action, date)
            _floor_actions.append(d)
        self._activities.append({
            'overview': _overview,
            'floor_actions': _floor_actions
        })

    def _extract_floor_act(self, action, date):
        """
        Extracts a floor action

        :param action: The XML containing it
        :param date: The date to prepend
        :return: The data as a dict
        """
        time = action.find('action_time').get('for-search').split('T')[
            -1].split(
            ':')
        time = datetime.datetime(int(date[0:4]), int(date[4:6]),
                                 int(date[6:]), hour=int(time[0]),
                                 minute=int(time[1]),
                                 second=int(time[2]))
        d = {'time': time.timestamp(),
             'unique_id': action.get('unique-id'),
             'act_id': action.get('act-id'),
             'desc': action.find('action_description').text.strip(),
             'item': None}

        if action.find('action_item'):
            a = action.find('action_description').find('a')
            d['item'] = {
                'title': action.find('action_item').text,
                'text': a.text if a else None,
                'link': a.get('href') if a else None,
                'type': a.get('rel') if a else None
            }

        return d

    def to_json(self):
        """
        Dumps the legislative session to a JSON file
        """
        filename = self._sources['xml'].replace('.xml', '.json')
        self._sources['json'] = self.ROOT_DIR + 'json/' + filename

        json.dump({
            'sources': self._sources,
            'overview': self._overview,
            'activities': self._activities
        }, open(self._sources['json'], 'w+'))

    def from_json(self, f):
        """
        Reads a session from a JSON to fill in its values
        :param f: The filename to load - str
        """
        data = json.load(open(f))
        self._sources = data['sources']
        self._overview = data['overview']
        self._activities = data['activities']

    def __repr__(self):
        return 'US House: {}'.format(self._overview)
