import json

import requests
from bs4 import BeautifulSoup

import pdb


class Vote:

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
            xml = requests.get(url).text
            soup = BeautifulSoup(xml, 'xml')
            pdb.set_trace()
        elif filename:
            pass
        else:
            raise ValueError('ValueError: Unspecified vote source.')

