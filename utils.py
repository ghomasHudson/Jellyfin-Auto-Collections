'''Handy utility functions for other scripts'''
import requests
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]


def get_library_id(library_name, headers=None):
    '''Get the library named library_name'''
    r = requests.get(f'{server_url}/Users/{user_id}/Views',headers=headers)
    r.raise_for_status()
    libraries = r.json().get('Items')
    library_id = [ x.get('Id') for x in libraries
                    if x.get('Name') == library_name]
    if library_id:
        library_id = library_id[0]
    return library_id


def request_repeat_get(url, headers=None, params=None):
    '''Do a GET request, repeat if err'''
    while True:
        try:
            res = requests.get(url, headers=headers, params=params)
            return res
        except:
            pass


def request_repeat_post(url, headers=None, params=None):
    '''Do a POST request, repeat if err'''
    while True:
        try:
            res = requests.post(url, headers=headers, params=params)
            return res
        except:
            pass
