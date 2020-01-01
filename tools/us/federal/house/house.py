from collections import defaultdict

from pprint import pprint

from session import Session
from bill import Bill
from representative import Representative
from vote import Vote

from utils import get_jsons


class USHouse:

    """
    Driver for the US House of Representatives
    """

    ROOT_DIR = 'data/us/federal/house/'

    def __init__(self):
        self._sessions = []

        self._reps = []
        self._bills = []
        self._votes = []

        # Search {object} by {property}
        self._search_by = defaultdict(lambda: defaultdict(dict))

    def get_floor(self, floor='HDoc-116-1-FloorProceedings.xml'):
        """
        Retrieves a congressional XML file

        :param floor: The name of the file
        """
        self._sessions.append(Session(source=floor))

    def read_files(self):
        """
        Reads JSON paths of Reps, Bills, and Votes
        """
        rep_paths = get_jsons(Representative.ROOT_DIR)
        self._reps = [Representative(filename=p) for p in rep_paths]

        bill_paths = get_jsons(Bill.ROOT_DIR)
        self._bills = [Bill(filename=p) for p in bill_paths]

        vote_paths = get_jsons(Vote.ROOT_DIR)
        self._votes = [Vote(filename=p) for p in vote_paths]

    def generate_search_by(self):
        """
        Generates the dictionary to search for a given class
        of object by their URL
        """
        # Representative lookup
        self._search_by['rep']['party'] = defaultdict(list)
        self._search_by['rep']['state'] = defaultdict(list)

        for rep in self._reps:
            self._search_by['rep']['url'][rep.get_sources()['url']] = rep
            self._search_by['rep']['party'][rep.get_current_party()].append(rep)

            pos = rep.get_states()
            for p in pos:
                self._search_by['rep']['state'][p].append(rep)

        self._search_by['bill']['sponsor url'] = defaultdict(list)
        for bill in self._bills:
            self._search_by['bill']['sponsor url'][bill.get_overview()['sponsor']['url']].append(bill)

    def count_bills_by(self, show=False):
        bills_by = defaultdict(lambda: defaultdict(int))

        # Bills by Party
        for r, bs in self._search_by['bill']['sponsor url'].items():
            party = self._search_by['rep']['url'][r].get_current_party()
            bills_by['party'][party] += len(bs)

        # Bills by State
        for r, bs in self._search_by['bill']['sponsor url'].items():
            states = self._search_by['rep']['url'][r].get_states()

            for s in states:
                bills_by['state'][s] += len(bs)

        # Bills by Progress
        for bill in self._bills:
            bills_by['progress'][bill.get_progress()] += 1

        # Bills by Subject
        for bill in self._bills:
            subjects = bill.get_subjects()
            if 'main' in subjects:
                bills_by['subject - main'][subjects['main']['title']] += 1
                bills_by['subject - all'][subjects['main']['title']] += 1
            for sub in subjects['others']:
                bills_by['subject - all'][sub['title']] += 1

        if show:
            pprint(bills_by)
        else:
            return bills_by


if __name__ == '__main__':
    house = USHouse()
    house.read_files()
    house.generate_search_by()
    house.count_bills_by(show=True)
