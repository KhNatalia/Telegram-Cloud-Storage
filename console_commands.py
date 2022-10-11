import json
import os.path
import click
from telethon.tl.types import DocumentAttributeFilename

# from telegram_cloud_storage.client import Client
# import telegram_cloud_storage.configuration as conf
# from telegram_cloud_storage.exceptions import catch
# from telegram_cloud_storage.utils import separate_string, directory_mode
from client import Client
import configuration as conf
from exceptions import catch
from utils import separate_string, directory_mode


def find_storage(config):
    """ Find the storage ID and directories by his name.
    """
    with open(config) as f:
        config = json.load(f)

        if len(config['channels']) == 0:
            print("You have no storage! Please add new storage using the function 'new_cloud_storage'!")
            return None, None, None
        elif len(config['channels']) == 1:
            return config['channels'][0]['channel_id'], config['channels'][0]['channel_path'], \
                   config['channels'][0]['channel_name']
        else:
            for channel in config['channels']:
                print(channel['channel_name'])
            dialog = click.prompt("Choose a suitable storage and write its name")

            for channel in config['channels']:
                if channel['channel_name'] == dialog:
                    return channel['channel_id'], channel['channel_path'], channel['channel_name']
        print("Ooops! No channel with that name!")
        return None, None, None


def find_channel_id(client, name):
    """ Find the channel ID by his name.
    """
    for dialog in client.iter_dialogs():
        if dialog.name == name:
            return dialog.id

    print("Sorry! Channel not found!")
    return False


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
def log_in(config, proxy):
    """Performs user authorization in the Telegram messenger using api_id, api_hash,
    phone number and special code.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
def log_out(config, proxy):
    """Logs out the user from the Telegram messenger.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()
    if client.is_connected():
        client.disconnect()
        client.stop()
    print("Logout successfully")


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-c', '--channel_name', default=None,
              help='The name of the channel (dialogue) that will be used as cloud storage.')
@click.option('-d', '--directory', default=None,
              help='The path to directory that will be used for cloud storage.')
def create_cloud_storage(config, proxy, channel_name, directory):
    """ Create new cloud storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    print("Please create a channel to be used as cloud storage and write its name below.")
    channel_id = None

    while channel_id is None:
        if channel_name is None:
            channel_name = click.prompt("Enter channel name")

        channel_id = find_channel_id(client, channel_name)

        if channel_id:
            if directory is None:
                directory = click.prompt("Enter the path directory")

            if not os.path.exists(directory):
                os.mkdir(directory)

            conf.add_storage(channel_name, channel_id, directory)


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
def delete_cloud_storage(config, proxy, storage_name):
    """ Delete cloud storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    channel_id, path, storage_name = find_storage(conf.CONFIG_FILE)
    is_delete = ''

    while is_delete != 'Y' or is_delete != 'N':
        is_delete = click.prompt("If you want to delete storage '{}' enter Y, else N".format(storage_name))
        if is_delete == 'Y':
            conf.delete_storage(storage_name)
        elif is_delete == 'N':
            print("Your storage wasn't deleted!")


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-u', '--users', default=None,
              help='Comma-separated list of user(s) name(s) to be added to the cloud storage (dialog).')
def add_users(config, proxy, users):
    """Adds the new user to the storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    channel_id, path, storage_name = find_storage(conf.CONFIG_FILE)
    if channel_id is not None:
        if users is None:
            users = click.prompt("Enter the user(s) name(s) separated by commas")
        users = separate_string(users)

        if len(users) != 0:
            for ID in channel_id:
                client.invite_users(ID, users)


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-d', '--directories', default=None,
              help='Comma-separated list of path to directories that will be new repositories.')
def add_new_directories(config, proxy, directories):
    """ Adds the new directory or directories for an existing storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    channel_id, path, storage_name = find_storage(conf.CONFIG_FILE)
    if channel_id is not None:
        if directories is None:
            directories = click.prompt("Please, enter new directory or directories separated by commas")
        directories = separate_string(directories)

        if len(directories) != 0:
            for ID in channel_id:
                for direct in directories:
                    if not os.path.exists(direct):
                        os.mkdir(direct)
                conf.new_directories(directories, ID)
            print("Directories have been added successfully!")


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-n', '--names', default=None,
              help='Comma-separated list of dialog names that will be new repositories.')
def add_new_channels(config, proxy, names):
    """ Adds the new channel or channels for an existing storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    channel_id, path, storage_name = find_storage(conf.CONFIG_FILE)
    if channel_id is not None:
        if names is None:
            names = click.prompt("Please, enter new channel(s) name(s) separated by commas")
        names = separate_string(names)

        channels = []
        for name in names:
            new_channel_id = find_channel_id(client, name)
            if channel_id:
                channels.append(new_channel_id)

        if len(channels) != 0:
            for ID in channel_id:
                conf.new_channels(channels, ID)


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-filenames', default=None, help='Enter filenames that you want upload separated by commas')
def upload(config, proxy, filenames):
    """ Upload files into the cloud storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    if filenames is None:
        filenames = click.prompt("Enter filenames separated by commas")
    filenames = separate_string(filenames)
    files = []

    for file in filenames:
        if os.path.exists(file):
            if os.path.isfile(file):
                files.append(file)
            else:
                dir_files = directory_mode(file)
                for dir_file in dir_files:
                    files.append(dir_file)
        else:
            print("Ooops! File '{}' does not exist!".format(file))

    if len(files) > 0:
        channel_id, directories, storage_name = find_storage(conf.CONFIG_FILE)
        if channel_id is not None:
            for ID in channel_id:
                client.upload_files(ID, files)

            messages = []
            for file in files:
                id_message = client.find_message(channel_id[0], os.path.basename(file))
                if id_message is not None:
                    messages.append(id_message)

            client.download_files(messages, directories, channel_id[0])
    else:
        print("Ooops! No file for sending!")


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
def download(config, proxy):
    """ Download files from the cloud storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    channel_id, directories, storage_name = find_storage(conf.CONFIG_FILE)
    if channel_id is not None:
        files = client.find_files(channel_id[0])
        client.download_files(files, directories, channel_id[0])


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-id_message', default=None, help='Enter the message id.')
@click.option('-filename', default=None, help='Enter the file name.')
def download_file(config, proxy, id_message, filename):
    """ Download file by the message ID from the cloud storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    if filename is None and id_message is None:
        filename = click.prompt("Enter the file name that you want to download")

    channel_id, directories, storage_name = find_storage(conf.CONFIG_FILE)
    if channel_id is not None:
        if id_message is None:
            id_message = client.find_message(channel_id[0], filename)
        if id_message is not None:
            client.download_files([id_message], directories, channel_id[0])
        else:
            print("Sorry! File was not found!")


@click.command()
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(conf.CONFIG_FILE))
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
def get_list_files(config, proxy):
    """ Download file by the message ID from the cloud storage.
    """
    client = Client(config or conf.default_config(), proxy=proxy)
    client.start()

    channel_id, directories, storage_name = find_storage(conf.CONFIG_FILE)

    filenames = []
    if channel_id is not None:
        messages = client.find_files(channel_id[0])
        for message in messages:
            filename_attr = next(filter(lambda x: isinstance(x, DocumentAttributeFilename),
                                        message.document.attributes), None)
            filenames.append(filename_attr.file_name if filename_attr else 'Unknown')

    if len(filenames) > 0:
        big_files = []
        for i in range(len(filenames)):
            if "fs_manifest" in filenames[i]:
                big_files.append(i)

        for index in big_files:
            name = filenames[index][12:].split('.')[0]
            parse_files = [x for x in filenames if name + "_" in x]
            name = name + '.' + parse_files[0].split('.')[1]

            filenames[index] = name

            parse_files = set(parse_files)
            filenames = [o for o in filenames if o not in parse_files]

        print("All files in the cloud storage:")
        for file in filenames:
            print(file)


@click.command()
def help_func():
    print("Function list")
    print("-----------------------------------------")
    print("Logs into the telegram account:      login")
    print("Logs out of the telegram account:    logout")
    print("Create new cloud storage:            new_cloud_storage")
    print("Delete storage:                      delete_cloud_storage")
    print("Add new user(s) to the storage:      add_user")
    print("Add new directories to the storage:  add_directories")
    print("Add new channel(s) to the storage:   add_channels")
    print("Upload file(s) into the storage:     upload")
    print("Download all files from the storage: download")
    print("Download some file(s) from storage:  download_file")
    print("Get list of all files from the storage: files")


login_cli = catch(log_in)
logout_cli = catch(log_out)
new_cloud_storage_cli = catch(create_cloud_storage)
delete_cloud_storage_cli = catch(delete_cloud_storage)
add_user_cli = catch(add_users)
new_directories_cli = catch(add_new_directories)
new_channels_cli = catch(add_new_channels)
upload_cli = catch(upload)
download_cli = catch(download)
download_file_cli = catch(download_file)
list_files_cli = catch(get_list_files)
help_cli = catch(help_func)


if __name__ == '__main__':
    import sys
    import re
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    try:
        fn = {'login': login_cli, 'logout': logout_cli,
              'new_cloud_storage': new_cloud_storage_cli, 'delete_cloud_storage': delete_cloud_storage_cli,
              'add_user': add_user_cli, 'add_directories': new_directories_cli, 'add_channels': new_channels_cli,
              'upload': upload_cli, 'download': download_cli, 'download_file': download_file_cli,
              'files': list_files_cli, 'help': help_cli}[sys.argv[1]]
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        sys.exit(fn())
    except IndexError:
        print("Please, enter the required command! Use this command 'help' to observe full command list.")
