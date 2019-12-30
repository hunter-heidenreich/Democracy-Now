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
