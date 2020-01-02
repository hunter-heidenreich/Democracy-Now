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

    :return: Two sets of URLs, un-downloaded and downloaded
    """
    old_urls = set()
    for f in tqdm(glob('data/us/federal/house/reps/json/*.json')):
        data = json.load(open(f))
        old_urls.add(data['sources']['url'])

    new_urls = set()
    for f in tqdm(glob('data/us/federal/house/bills/json/*.json')):
        data = json.load(open(f))
        new_urls.add(data['overview']['sponsor']['url'])
        for co in data['cosponsors']:
            if 'congress.gov' not in co['cosponsors']['url']:
                new_urls.add('https://www.congress.gov' + co['cosponsors']['url'])

    new_urls -= old_urls
    return new_urls, old_urls


def get_bill_urls():
    """
    Gets the URLs for all the bills
    from the already generated data

    :return: Two sets of URLs, un-downloaded and downloaded
    """
    new_urls = set()
    old_urls = set()
    for f in tqdm(glob('data/us/federal/house/bills/json/*.json')):
        data = json.load(open(f))

        if 'all-info' not in data['sources']['url']:
            old_urls.add(data['sources']['url'] + '/all-info')
        else:
            old_urls.add(data['sources']['url'])
        if data['related_bills']:
            for b in data['related_bills']:
                if 'all-info' not in b['bill']['url']:
                    new_urls.add(b['bill']['url'] + '/all-info')
                else:
                    new_urls.add(b['bill']['url'])

    for f in tqdm(glob('data/us/federal/house/session/json/*.json')):
        data = json.load(open(f))

        for act in data['activities']:
            for fl in act['floor_actions']:
                if fl['item']:
                    if fl['item']['type'] == 'bill':
                        b = fl['item']['link']
                        if 'congress.gov' in b:
                            if 'all-info' not in b:
                                new_urls.add(b + '/all-info')
                            else:
                                new_urls.add(b)

    new_urls -= old_urls
    return new_urls, old_urls


def get_jsons(path, pattern='json/*.json'):
    """
    Given a path, extracts all the JSON files
    :param path: The path to the JSONs
    :param pattern: The pattern to glob
    :return: The list of JSON paths
    """
    return list(glob(path + pattern))
