import getpass
import json
import os
from typing import Union
from urllib.parse import urlparse

import click
from telethon import TelegramClient
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.tl.types import DocumentAttributeFilename
from telethon.tl.functions.channels import InviteToChannelRequest

# from telegram_cloud_storage.configuration import SESSION_FILE
# from telegram_cloud_storage.exceptions import TelegramProxyError, TelegramUploadNoSpaceError
# from telegram_cloud_storage.utils import phone_match, async_to_sync, empty_disk_space, split_big_file, directory_mode, \
#     MAX_FILE_SIZE, clear_directory, join_big_file, get_parts_filenames
from configuration import SESSION_FILE
from exceptions import TelegramProxyError, TelegramUploadNoSpaceError
from utils import phone_match, async_to_sync, empty_disk_space, split_big_file, directory_mode, \
    MAX_FILE_SIZE, clear_directory, join_big_file, get_parts_filenames

PROXY_ENVIRONMENT_VARIABLE_NAMES = [
    'TELEGRAM_UPLOAD_PROXY',
    'HTTPS_PROXY',
    'HTTP_PROXY',
]


def get_proxy_environment_variable():
    for env_name in PROXY_ENVIRONMENT_VARIABLE_NAMES:
        if env_name in os.environ:
            return os.environ[env_name]


def parse_proxy_string(proxy: Union[str, None]):
    if not proxy:
        return None
    proxy_parsed = urlparse(proxy)
    if not proxy_parsed.scheme or not proxy_parsed.hostname or not proxy_parsed.port:
        raise TelegramProxyError('Malformed proxy address: {}'.format(proxy))
    if proxy_parsed.scheme == 'mtproxy':
        return 'mtproxy', proxy_parsed.hostname, proxy_parsed.port, proxy_parsed.username
    try:
        import socks
    except ImportError:
        raise TelegramProxyError('pysocks module is required for use HTTP/socks proxies. '
                                 'Install it using: pip install pysocks')
    proxy_type = {
        'http': socks.HTTP,
        'socks4': socks.SOCKS4,
        'socks5': socks.SOCKS5,
    }.get(proxy_parsed.scheme)
    if proxy_type is None:
        raise TelegramProxyError('Unsupported proxy type: {}'.format(proxy_parsed.scheme))
    return (proxy_type, proxy_parsed.hostname, proxy_parsed.port, True,
            proxy_parsed.username, proxy_parsed.password)


class Client(TelegramClient):
    def __init__(self, config_file, proxy=None, **kwargs):
        with open(config_file) as f:
            config = json.load(f)
        proxy = proxy if proxy is not None else get_proxy_environment_variable()
        proxy = parse_proxy_string(proxy)
        if proxy and proxy[0] == 'mtproxy':
            proxy = proxy[1:]
            kwargs['connection'] = ConnectionTcpMTProxyRandomizedIntermediate
        super().__init__(config.get('session', SESSION_FILE), config['api_id'], config['api_hash'],
                         proxy=proxy, **kwargs)

    def start(
            self,
            phone=lambda: click.prompt('Please enter your phone', type=phone_match),
            password=lambda: getpass.getpass('Please enter your password: '),
            *,
            bot_token=None, force_sms=False, code_callback=None,
            first_name=lambda: getpass.getpass('Please enter your first name: '),
            last_name=lambda: getpass.getpass('Please enter your last name: '),
            max_attempts=3):
        return super().start(phone=phone, password=password, bot_token=bot_token, force_sms=force_sms,
                             first_name=first_name, last_name=last_name, max_attempts=max_attempts)

    def stop(self):
        """ Ends session.
        """
        os.remove(os.path.expanduser('~/.config/telegram-upload.session'))
        self.disconnect()

    def upload_files(self, dialog, filenames):
        """ Loads a list of files into a specific dialog.
        """
        new_paths = []
        for file in filenames:
            if os.path.exists(file):
                # if the file exceeds the maximum size, then it is split
                if os.path.getsize(file) > MAX_FILE_SIZE:
                    path = split_big_file(file)
                    new_paths.append(path)

                    new_files = directory_mode(path)

                    for parse_file in new_files:
                        # if the loaded file is already in the dialog, then it is deleted and a new one is loaded
                        id_message = self.find_message(dialog, os.path.basename(parse_file))
                        if id_message is not None:
                            async_to_sync(self.delete_messages(dialog, id_message))
                        async_to_sync(self.send_file(dialog, parse_file))

                    clear_directory(path)
                else:
                    self.send_file(dialog, file)

        if len(filenames) == 1:
            print("File {} were sent successfully!".format(', '.join(filenames)))
        else:
            print("Files {} were sent successfully!".format(', '.join(filenames)))
        return new_paths

    def find_files(self, dialog):
        """ Finds all messages that contain documents.
        """
        for message in self.iter_messages(dialog):
            if message.document:
                yield message
            else:
                break

    def find_message(self, dialog, file):
        """ Finds a message in which a specific file was sent by its name.
        """
        for message in self.iter_messages(dialog):
            if message.document:
                filename_attr = next(filter(lambda x: isinstance(x, DocumentAttributeFilename),
                                            message.document.attributes), None)
                filename = filename_attr.file_name if filename_attr else 'Unknown'
                if filename == file or filename == "fs_manifest_" + file.split('.')[0] + ".csv":
                    return message
        return None

    def download_files(self, messages, directories, dialog):
        """ Carries out loading of documents from the dialogue for certain messages.
        """
        messages = reversed(list(messages))

        for message in messages:
            filename_attr = next(filter(lambda x: isinstance(x, DocumentAttributeFilename),
                                        message.document.attributes), None)
            filename = filename_attr.file_name if filename_attr else 'Unknown'
            # before loading, we check the availability of the required disk space
            if not empty_disk_space(directories, message.document.size):
                raise TelegramUploadNoSpaceError('There is no disk space to download "{}".'.format(filename))

            for directory in directories:
                path = os.path.join(directory, filename)
                if "fs_manifest" in filename:
                    self.download_big_file(messages, message, filename, dialog, directory)
                else:
                    async_to_sync(self.download_media(message=message, file=path))
        print("All files have been downloaded successfully!")

    def download_big_file(self, messages, message, filename, dialog, directory):
        """ Download big file.
            If the file that is being downloaded is large (split into several), a search is performed and
            all its pieces are downloaded for their further join into one file.
        """
        # path to a temporary directory for storing chunks of a large file
        big_file_dir = "{}\\{}".format(os.path.dirname(os.path.abspath(__file__)), "download")
        if not os.path.exists(big_file_dir):
            os.mkdir(big_file_dir)

        big_file_path = os.path.join(big_file_dir, filename)
        async_to_sync(self.download_media(message=message, file=big_file_path))

        # big_files.append(path)
        parts_files = get_parts_filenames(big_file_path)

        for file in parts_files:
            id_message = self.find_message(dialog, file)
            if id_message not in messages:
                # check free space on dick
                if not empty_disk_space([directory], message.document.size):
                    os.remove(big_file_path)
                    raise TelegramUploadNoSpaceError(
                        'There is no disk space to download.')
                big_file_path = os.path.join(big_file_dir, file)
                async_to_sync(self.download_media(message=id_message, file=big_file_path))

        join_big_file(big_file_dir, os.path.join(big_file_dir, filename), directory)

    def invite_users(self, channel_id, users):
        """ Invite a new user to the dialogue.
        """
        async_to_sync(self(InviteToChannelRequest(channel_id, users)))
        print("The invitation has been sent!")
