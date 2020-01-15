import logging

from database.congress import CongressData


logging.basicConfig(level=logging.DEBUG)


def run():
    logging.info('Initiating server.')

    database = CongressData()


if __name__ == '__main__':
    run()
