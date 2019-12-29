import datetime
import calendar
import json
from collections import defaultdict

import requests
from bs4 import BeautifulSoup


class Vote:

    """
    This class represents a vote (a roll call vote)
    for the House of Representatives
    """

    ROOT_DIR = 'data/us/federal/house/votes/'

    def __init__(self, url=None, filename=None):

        self._congress = {}
        self._votes = {}

        # The location of data sources
        # - url  -> original url scraped
        # - xml  -> cached html on file system
        # - json -> will link to JSON on file system
        self._sources = {}

        if url:
            self.load_from_url(url)
        elif filename:
            self.from_json(filename)
        else:
            raise ValueError('ValueError: Unspecified vote source.')

    def __repr__(self):
        return '{} of {}: {}-{} ({})'.format(self._votes['question'],
                                             self._congress['legis_num'],
                                             self._votes['totals']['totals']['Yea'],
                                             self._votes['totals']['totals']['Nay'],
                                             self._votes['result'])

    def load_from_url(self, url, force_reload=False):
        """
        Given a URL, this will generate the values
        for the Vote from the XML

        :param url: The URL where the data can be found -- str
        :param force_reload: When True, this will force a refresh of that XML
        """
        cache = url.split('://')[-1].replace('/', '_')

        self._sources['url'] = url
        self._sources['xml'] = self.ROOT_DIR + 'web/' + cache

        soup = BeautifulSoup(self._get_xml(force_reload), 'xml')

        self._extract_congressional_info(soup)
        self._extract_basic_vote(soup)
        self._process_datetime(soup)
        self._extract_totals(soup)
        self._extract_votes(soup)

        self.to_json()

    def _get_xml(self, force_reload):
        """
        Retrieves the XML, checking if the file is already
        available locally and abiding by whether or not a
        refresh has been requested.

        :return: The XML data - str
        """
        try:
            if force_reload:
                raise FileNotFoundError

            with open(self._sources['xml'], 'r+') as in_file:
                xml = in_file.read()
        except FileNotFoundError:
            xml = requests.get(self._sources['url']).text
            with open(self._sources['xml'], 'w+') as out_file:
                out_file.write(xml)

        return xml

    def _extract_congressional_info(self, soup):
        """
        Extracts the available congressional information

        :param soup: The entire xml as a BeautifulSoup
        """
        self._congress['majority'] = soup.find('majority').text
        self._congress['congress'] = soup.find('congress').text
        self._congress['session'] = soup.find('session').text
        self._congress['legis_num'] = soup.find('legis-num').text

        try:
            self._congress['chamber'] = soup.find('chamber').text
        except AttributeError:
            # Seems like there's at least 1 vote
            # where the chamber is listed as
            # a committee for some reason
            self._congress['chamber'] = soup.find('committee').text

    def _extract_basic_vote(self, soup):
        """
        Extracts the basic information from the vote

        :param soup: The entire XML as a soup object
        """
        self._votes['question'] = soup.find('vote-question').text
        self._votes['type'] = soup.find('vote-type').text
        self._votes['result'] = soup.find('vote-result').text
        self._votes['desc'] = soup.find('vote-desc').text

    def _extract_totals(self, soup):
        """
        Extracts the vote totals

        :param soup: The entire XML as a soup object
        """
        self._votes['totals'] = defaultdict(dict)
        for byparty in soup.find_all('totals-by-party'):
            self._votes['totals']['by_party'][byparty.find('party').text] = {
                'Yea': int(byparty.find('yea-total').text),
                'Nay': int(byparty.find('nay-total').text),
                'Present': int(byparty.find('present-total').text),
                'Not Voting': int(byparty.find('not-voting-total').text)
            }

        totals = soup.find('totals-by-vote')
        self._votes['totals']['totals'] = {
            'Yea': int(totals.find('yea-total').text),
            'Nay': int(totals.find('nay-total').text),
            'Present': int(totals.find('present-total').text),
            'Not Voting': int(totals.find('not-voting-total').text)
        }

    def _extract_votes(self, soup):
        """
        Extracts the vote

        :param soup: The entire XML as a soup object
        """
        self._votes['recorded'] = []
        for v in soup.find_all('recorded-vote'):
            leg = v.find('legislator')
            vot = v.find('vote')
            self._votes['recorded'].append({
                'party': leg.get('party'),
                'role': leg.get('role'),
                'state': leg.get('state'),
                'name': leg.text,
                'vote': vot.text
            })

    def _process_datetime(self, soup):
        """
        Extracts the time of the vote

        :param soup: The entire XML as a soup object
        """
        date = soup.find('action-date').text.split('-')
        conv = {v: k for k, v in enumerate(calendar.month_abbr)}
        date[1] = conv[date[1]]
        time = soup.find('action-time').get('time-etz').split(':')
        dt = datetime.datetime(int(date[2]), date[1], int(date[0]),
                               hour=int(time[0]), minute=int(time[1]))
        self._votes['datetime'] = dt.timestamp()

    def to_json(self):
        """
        Dumps the Bill to a JSON readable format
        """
        filename = 'house_{}_{}.json'.format(self._congress['congress'],
                                             self._congress['legis_num'].replace(' ', ''))
        self._sources['json'] = self.ROOT_DIR + 'json/' + filename
        json.dump({
            'congress': self._congress,
            'votes': self._votes,
            'sources': self._sources
        }, open(self.ROOT_DIR + 'json/' + filename, 'w+'))

    def from_json(self, filename):
        """
        Given a filename, reads a JSON formatted Bill
        into a Bill object

        :param filename: The location on the local disk - str
        """
        data = json.load(open(filename))

        self._congress = data['congress']
        self._votes = data['votes']
        self._sources = data['sources']


if __name__ == '__main__':
    from glob import glob
    from tqdm import tqdm

    for f in tqdm(glob('data/us/federal/house/votes/web/*')):
        url = 'https://' + f.split('/')[-1].replace('_', '/')
        v = Vote(url=url)
