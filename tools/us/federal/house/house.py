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

    def get_floor(self, floor='HDoc-116-1-FloorProceedings.xml'):
        self._sessions.append(Session(source=floor))

    def read_files(self):
        rep_paths = get_jsons(Representative.ROOT_DIR)
        self._reps = [Representative(filename=p) for p in rep_paths]

        bill_paths = get_jsons(Bill.ROOT_DIR)
        self._bills = [Bill(filename=p) for p in bill_paths]

        vote_paths = get_jsons(Vote.ROOT_DIR)
        self._votes = [Vote(filename=p) for p in vote_paths]

        import pdb
        pdb.set_trace()


if __name__ == '__main__':
    house = USHouse()
    # house.get_floor()
    house.read_files()
