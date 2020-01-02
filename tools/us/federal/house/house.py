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
        self._search_by = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

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
        rep_paths = get_jsons(Representative.ROOT_DIR)
        self._reps = [Representative(filename=p) for p in rep_paths]

        bill_paths = get_jsons(Bill.ROOT_DIR)
        self._bills = [Bill(filename=p) for p in bill_paths]

        vote_paths = get_jsons(Vote.ROOT_DIR)
        self._votes = [Vote(filename=p) for p in vote_paths]

    def search(self, group, key, value):
        if value in self._search_by[group][key]:
            return self._search_by[group][key][value]
        else:
            if group == 'reps':
                self._search_by[group][key][value] = \
                    set(filter(lambda r: r.search(key, value), self._reps))
                return self._search_by[group][key][value]
            else:
                print('Invalid search group: {}'.format(group))


if __name__ == '__main__':
    congresses = list(range(109, 117))
    sessions = list(range(1, 3))
    floors = ['HDoc-{}-{}-FloorProceedings.xml'.format(congress, sess) for congress in congresses for sess in sessions]

    house = USHouse()
    # for floor in floors[:-1]:
    #     house.get_floor(floor=floor)
    # house.get_floor(floor=floors[-1], force_reload=True)
    house.read_files()

    import pdb
    pdb.set_trace()
