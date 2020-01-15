from glob import glob
from tqdm import tqdm

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
        self.data = {
            'bills': [f for f in glob(self.DATA_DIR + '/bills/json/*.json')],
            'reps': [f for f in glob(self.DATA_DIR + '/reps/json/*.json')],
            'sessions': [f for f in glob(self.DATA_DIR + '/session/json/*.json')],
            'votes': [f for f in glob(self.DATA_DIR + '/votes/json/*.json')]
        }
        logging.debug('DB::Loaded.')
