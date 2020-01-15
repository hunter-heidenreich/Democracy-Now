from glob import glob
from tqdm import tqdm

from database.models.bill import Bill
from database.models.representative import Representative
from database.models.session import Session
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

        self._data_type = [('votes', Vote), ('bills', Bill), ('session', Session), ('reps', Representative)]
        for typ, cls in self._data_type:
            self._load_data(typ, cls)

        logging.debug('DB::Loaded.')

    def _load_data(self, typ, cls):
        """
        Given a model save label and a model class,
        this function will load all the local data
        :param typ: The model save label
        :param cls: The model constructor
        """
        logging.debug('DB::Loading {}'.format(typ))
        self.data[typ] = [cls(filename=f) for f in tqdm(glob(self.DATA_DIR + '/{}/json/*.json'.format(typ)))]

    def query(self, group, query):
        """
        Queries the database

        :param group: The model type
        :param query: The dict of key values to search for that model type
        :return: List of models of specified type that fit the query criteria
        """
        res = self.data[group]
        for k, v in query.items():
            res = [r for r in res if r.search(k, v)]

            if not res:
                break

        return res

