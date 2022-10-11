import json
import os

import click

CONFIG_FILE = os.path.expanduser('~/.config/telegram-upload.json')
SESSION_FILE = os.path.expanduser('~/.config/telegram-upload')


def default_config():
    if os.path.lexists(CONFIG_FILE):
        return CONFIG_FILE
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    # click.echo('Create an App in API development tools on the https://my.telegram.org.')
    # api_id = click.prompt('Please enter api_id', type=int)
    # api_hash = click.prompt('Now enter api_hash')
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'api_id': 6511861, 'api_hash': '8f8e4986cae66a1d2ce5f5573eda9fd0', 'channels': [], }, f)
    return CONFIG_FILE


def add_storage(channel_name, channel_id, path):
    """ Writes information about the new storage to the configuration file.
    """
    with open(CONFIG_FILE) as f:
        data = json.load(f)

        if not os.path.exists(path):
            os.mkdir(path)

        data['channels'].append({'channel_name': channel_name, 'channel_id': [channel_id], 'channel_path': [path]})

        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(data, outfile)
        print("The new channel '{}' has been successfully added!".format(channel_name))


def new_directories(directories, channel_id):
    """ Writes information about the new directory or directories for the storage to the configuration file.
    """
    with open(CONFIG_FILE) as f:
        data = json.load(f)

        for channel in data['channels']:
            if channel['channel_id'] == channel_id:
                for directory in directories:
                    if not os.path.exists(directory):
                        os.mkdir(directory)
                    channel['channel_path'].append(directory)
                with open(CONFIG_FILE, 'w') as outfile:
                    json.dump(data, outfile)
                print("The new directories has been successfully added to channel '{}'!".format(channel['channel_name']))
                break


def new_channels(channels, channel_id):
    """ Writes information about the new channel or channels for the storage to the configuration file.
    """
    with open(CONFIG_FILE) as f:
        data = json.load(f)

        for channel in data['channels']:
            if channel['channel_id'] == channel_id:
                for ID in channels:
                    channel['channel_id'].append(ID)
                with open(CONFIG_FILE, 'w') as outfile:
                    json.dump(data, outfile)
                print("The new channels has been successfully added to channel '{}'!".format(channel['channel_name']))
                break


def delete_storage(name):
    """ Deletes information about the storage.
    """
    with open(CONFIG_FILE) as f:
        data = json.load(f)

        for channel in data['channels']:
            if channel['channel_name'] == name:

                print(channel)
                print("The new channels has been successfully added to channel '{}'!".format(channel['channel_name']))
                break
