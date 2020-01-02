from collections import defaultdict

from tqdm import tqdm

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

        # Search {object} by {property} for {value}
        self._search_by = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

        # congresses = list(range(109, 117))
        # sessions = list(range(1, 3))
        # floors = ['HDoc-{}-{}-FloorProceedings.xml'.format(congress, sess) for
        #           congress in congresses for sess in sessions]
        #
        # for floor in floors:
        #     self.get_floor(floor)

        self.read_files()

    def get_floor(self, floor='HDoc-116-1-FloorProceedings.xml',
                  force_reload=True):
        """
        Retrieves a congressional XML file

        :param floor: The name of the file
        :param force_reload: Whether or not to refresh the file
        """
        self._sessions.append(Session(url=floor, force_reload=force_reload))

    def read_files(self):
        """
        Reads JSON paths of Reps, Bills, and Votes
        """
        print('Loading sessions.')
        ses_paths = get_jsons(Session.ROOT_DIR)
        self._sessions = [Session(filename=p) for p in tqdm(ses_paths)]

        print('Loading reps.')
        rep_paths = get_jsons(Representative.ROOT_DIR)
        self._reps = [Representative(filename=p) for p in tqdm(rep_paths)]

        print('Loading bills.')
        bill_paths = get_jsons(Bill.ROOT_DIR)
        self._bills = [Bill(filename=p) for p in tqdm(bill_paths)]

        print('Loading votes.')
        vote_paths = get_jsons(Vote.ROOT_DIR)
        self._votes = [Vote(filename=p) for p in tqdm(vote_paths)]

    def search(self, group, key, value):
        if value in self._search_by[group][key]:
            return self._search_by[group][key][value]
        else:
            if group == 'reps':
                self._search_by[group][key][value] = \
                    set(filter(lambda r: r.search(key, value), self._reps))
                return self._search_by[group][key][value]
            elif group == 'bills':
                self._search_by[group][key][value] = \
                    set(filter(lambda r: r.search(key, value), self._bills))
                return self._search_by[group][key][value]
            else:
                print('Invalid search group: {}'.format(group))


if __name__ == '__main__':
    house = USHouse()

    import pdb
    pdb.set_trace()
