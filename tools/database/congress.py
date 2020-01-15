from glob import glob
from tqdm import tqdm

from database.models.bill import Bill
from database.models.vote import Vote

import logging
logging.basicConfig(level=logging.DEBUG)


class CongressData:

    """
    Stores and manages data obtained from
    congress.gov
    """

    DATA_DIR = 'data/us/federal/house'

    def __init__(self):
        logging.debug('DB::Loading database.')

        self.data = {}
        self._data_type = [('votes', Vote), ('bills', Bill)]
        for typ, cls in self._data_type:
            self._load_data(typ, cls)

        logging.debug('DB::Loaded.')

    def _load_data(self, typ, cls):
        logging.debug('DB::Loading {}'.format(typ))
        self.data[typ] = [cls(filename=f) for f in tqdm(glob(self.DATA_DIR + '/{}/json/*.json'.format(typ)))]
