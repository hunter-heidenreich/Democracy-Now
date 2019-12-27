import datetime
import calendar

import requests
from bs4 import BeautifulSoup


class Vote:

    ROOT_DIR = 'data/us/federal/house/votes/'

    def __init__(self, url=None, filename=None):

        self._majority = None
        self._congress = None
        self._session = None
        self._chamber = None

        self._legis_num = None

        self._vote_question = None
        self._vote_type = None
        self._vote_result = None
        self._vote_desc = None

        self._datetime = None

        self._vote_totals = {
            'Yea': 0,
            'Nay': 0,
            'Present': 0,
            'Not Voting': 0
        }

        self._party_vote_totals = {}

        self._recorded_votes = []

        if url:
            self.load_from_url(url)
        elif filename:
            pass
        else:
            raise ValueError('ValueError: Unspecified vote source.')

    def __repr__(self):
        return '{} of {}: {}-{} ({})'.format(self._vote_question,
                                             self._legis_num,
                                             self._vote_totals['Yea'],
                                             self._vote_totals['Nay'],
                                             self._vote_result)

    def load_from_url(self, url, force_reload=False):
        cache = url.split('://')[-1].replace('/', '_')
        try:
            if force_reload:
                raise FileNotFoundError

            with open(self.ROOT_DIR + 'web/' + cache, 'r+') as in_file:
                xml = in_file.read()
        except FileNotFoundError:
            xml = requests.get(url).text
            with open(self.ROOT_DIR + 'web/' + cache, 'w+') as out_file:
                out_file.write(xml)

        soup = BeautifulSoup(xml, 'xml')

        self._majority = soup.find('majority').text
        self._congress = soup.find('congress').text
        self._session = soup.find('session').text
        try:
            self._chamber = soup.find('chamber').text
        except AttributeError:
            # Seems like there's at least 1 vote
            # where the chamber is listed as
            # a committee for some reason
            self._chamber = soup.find('committee').text

        self._legis_num = soup.find('legis-num').text

        self._vote_question = soup.find('vote-question').text
        self._vote_type = soup.find('vote-type').text
        self._vote_result = soup.find('vote-result').text
        self._vote_desc = soup.find('vote-desc').text

        date = soup.find('action-date').text.split('-')
        conv = {v: k for k, v in enumerate(calendar.month_abbr)}
        date[1] = conv[date[1]]
        time = soup.find('action-time').get('time-etz').split(':')

        self._datetime = datetime.datetime(int(date[2]),
                                           date[1],
                                           int(date[0]),
                                           hour=int(time[0]),
                                           minute=int(time[1]))

        for byparty in soup.find_all('totals-by-party'):
            self._party_vote_totals[byparty.find('party').text] = {
                'Yea': int(byparty.find('yea-total').text),
                'Nay': int(byparty.find('nay-total').text),
                'Present': int(byparty.find('present-total').text),
                'Not Voting': int(byparty.find('not-voting-total').text)
            }

        totals = soup.find('totals-by-vote')
        self._vote_totals = {
            'Yea': int(totals.find('yea-total').text),
            'Nay': int(totals.find('nay-total').text),
            'Present': int(totals.find('present-total').text),
            'Not Voting': int(totals.find('not-voting-total').text)
        }

        for v in soup.find_all('recorded-vote'):
            leg = v.find('legislator')
            vot = v.find('vote')
            self._recorded_votes.append({
                'party': leg.get('party'),
                'role': leg.get('role'),
                'state': leg.get('state'),
                'name': leg.text,
                'vote': vot.text
            })
