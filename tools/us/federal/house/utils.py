import json
from glob import glob

from tqdm import tqdm

import requests


def download_file(url, file, force_reload=False):
    """
    Downloads data from the web,
    caching it locally.

    :param url: The url to retrieve - str
    :param file: The local file path - str
    :param force_reload: Whether to enforce a data refresh - bool
                         (default: False)
    :return: The data downloaded
    """
    try:
        if force_reload:
            raise FileNotFoundError

        with open(file, 'r+') as in_file:
            data = in_file.read()
    except FileNotFoundError:
        data = requests.get(url).text
        with open(file, 'w+') as out_file:
            out_file.write(data)

    return data


def get_representative_urls():
    """
    Gets the URLs of all the representatives
    from the data already generated

    :return: The URLs - set
    """
    urls = set()
    for f in tqdm(glob('data/us/federal/house/bills/json/*.json')):
        data = json.load(open(f))
        urls.add(data['overview']['sponsor']['url'])
        for co in data['cosponsors']:
            urls.add(co['cosponsors']['url'])

    return urls


def get_bill_urls():
    """
    Gets the URLs for all the bills
    from the already generated data

    :return: The URLs - set
    """
    urls = set()
    for f in tqdm(glob('data/us/federal/house/bills/json/*.json')):
        data = json.load(open(f))

        if 'all-info' not in data['sources']['url']:
            urls.add(data['sources']['url'] + '/all-info')
        else:
            urls.add(data['sources']['url'])
        if data['related_bills']:
            for b in data['related_bills']:
                if 'all-info' not in b:
                    urls.add(b['bill']['url'] + '/all-info')
                else:
                    urls.add(b['bill']['url'])
    return urls


def get_jsons(path, pattern='json/*.json'):
    """
    Given a path, extracts all the JSON files
    :param path: The path to the JSONs
    :param pattern: The pattern to glob
    :return: The list of JSON paths
    """
    return list(glob(path + pattern))
