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
        self._search_by['rep']['party'] = defaultdict(set)
        self._search_by['rep']['state'] = defaultdict(set)

        for rep in self._reps:
            self._search_by['rep']['url'][rep.get_sources()['url']] = rep
            self._search_by['rep']['party'][rep.get_current_party()].add(rep)

            pos = rep.get_states()
            for p in pos:
                self._search_by['rep']['state'][p].add(rep)

        # Simple bill lookups
        self._search_by['bill']['sponsor url'] = defaultdict(set)
        self._search_by['bill']['sponsor'] = defaultdict(set)
        self._search_by['bill']['progress'] = defaultdict(set)
        self._search_by['bill']['congress'] = defaultdict(set)
        self._search_by['bill']['chamber'] = defaultdict(set)
        self._search_by['bill']['subject - main'] = defaultdict(set)
        self._search_by['bill']['subject - all'] = defaultdict(set)

        for bill in self._bills:
            self._search_by['bill']['sponsor url'][bill.get_overview()['sponsor']['url']].add(bill)
            self._search_by['bill']['sponsor'][self._search_by['rep']['url'][bill.get_overview()['sponsor']['url']]].add(bill)
            self._search_by['bill']['progress'][bill.get_progress()].add(bill)
            self._search_by['bill']['congress'][bill.get_congress()].add(bill)

            title = bill.get_overview()['sponsor']['title']
            if title == 'Rep.':
                title = 'House'
            elif title == 'Sen.':
                title = 'Senate'

            self._search_by['bill']['chamber'][title].add(bill)

            subjects = bill.get_subjects()
            if 'main' in subjects:
                self._search_by['bill']['subject - main'][subjects['main']['title']].add(bill)
                self._search_by['bill']['subject - all'][subjects['main']['title']].add(bill)
            for sub in subjects['others']:
                self._search_by['bill']['subject - all'][sub['title']].add(bill)

        # Complex Bill lookups
        self._search_by['bill']['party'] = defaultdict(set)
        self._search_by['bill']['state'] = defaultdict(set)
        for rep, bs in self._search_by['bill']['sponsor'].items():
            party = rep.get_current_party()
            self._search_by['bill']['party'][party] |= set(bs)

            for s in rep.get_states():
                self._search_by['bill']['state'][s] |= set(bs)

    def count_bills_by(self, show=False):
        bill = self._search_by['bill']
        bill = {prop: {k: len(v) for k, v in se.items()} for prop, se in bill.items()}

        if show:
            pprint(bill)
        else:
            return bill


if __name__ == '__main__':
    house = USHouse()
    house.read_files()
    house.generate_search_by()
    cnts = house.count_bills_by()

    import pdb
    pdb.set_trace()
