import ui
import paramiko
import console
from re import findall, match
from os.path import join
from datetime import datetime

# EDITABLE PARAMETERS
HOST = ''
USERNAME = ''
PKEY_PATH = ''
DLL_PATH = '/opt/DiscordChatExporter/DiscordChatExporter.Cli.dll'  # Path to Cli.dll file
SAVE_PATH = '~/discord_charts/'  # Path to directory to save to
ADDITIONAL_ARGUMENTS = '--dateformat u'
# # #


MIN_ID_LENGTH = 14

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

console.show_activity()
ssh.connect(
    HOST,
    username=USERNAME,
    pkey=paramiko.RSAKey.from_private_key_file(PKEY_PATH))
console.hide_activity()


def isIDValid(textfield):
    def alpha(value: float):
        for button in buttons:
            button.alpha = value

    text = textfield.text

    buttons = list()
    if textfield.name == 'guildID':
        buttons = [
            textfield.superview["showChannels"],
            textfield.superview["exportGuildChannels"]
        ]
    elif textfield.name == 'channelID':
        buttons = [textfield.superview["exportChannel"]]

    if MIN_ID_LENGTH <= len(text):
        alpha(1.0)
    else:
        alpha(0.5)

    if not text.isdigit():
        textfield.text_color = 'red'
        alpha(0.5)
    else:
        textfield.text_color = None


class DelegatedChannelIDTextField(object):
    def textfield_did_change(self, tf):
        isIDValid(tf)


class DelegatedGuildIDTextField(object):
    def textfield_did_change(self, tf):
        isIDValid(tf)


class DelegatedTableView(object):
    def get_textfield(self, tableview):
        view = tableview.superview
        if view["tableLabel"].text == 'Servers':
            return view["guildID"]
        elif view["tableLabel"].text == 'Channels':
            return view["channelID"]

    def tableview_did_select(self, tableview, section, row):
        textfield = self.get_textfield(tableview)
        textfield.text = match(r'\d+', tableview.data_source.items[row])[0]
        isIDValid(textfield)

    def tableview_did_deselect(self, tableview, section, row):
        textfield = self.get_textfield(tableview)
        textfield.text = ''
        isIDValid(textfield)


def log(sender, text):
    view = sender.superview
    view['consoleView'].text += text + '\n'


def sshcmd(command):
    return ssh.exec_command(command)[1].read().decode()


def dce(view, *args, save: bool = False):
    token = view["tokenField"].text
    if token:
        console.show_activity()
        is_bot = view["isBot"].value

        if save:
            full_path = join(SAVE_PATH, datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
            sshcmd("mkdir " + full_path)

        command = f'{f"cd {full_path}; " if save else ""}dotnet {DLL_PATH} {" ".join(args)} -t {token}{" -b " if is_bot else " "}'
        log(view["tokenField"], '> ' + command)
        console.hide_activity()
        return sshcmd(command)
    else:
        console.alert("Token is not specified.")


def parse_strings(answer, view, label_name: str):
    strings = findall(r'\d{' + str(MIN_ID_LENGTH) + ',} \| .+', answer)
    if strings:
        view["tableLabel"].text = label_name
        table = view["table"]
        table.alpha = 1.0
        table.data_source.items = strings


def show_servers(sender):
    view = sender.superview
    answer = dce(view, 'guilds')
    log(sender, answer)

    parse_strings(answer, view, 'Servers')


def show_pms(sender):
    view = sender.superview
    answer = dce(view, 'dm')
    log(sender, answer)

    parse_strings(answer, view, 'Channels')


def show_guild_channels(sender):
    if sender.alpha == 1.0:
        view = sender.superview
        answer = dce(view, 'channels', '-g', view["guildID"].text)
        log(sender, answer)

        parse_strings(answer, view, 'Channels')
    else:
        console.alert("You haven't specified Guild ID or specified ID is invalid.")


def export_channel(sender):
    if sender.alpha == 1.0:
        view = sender.superview
        answer = dce(view, 'export', '-c', view["channelID"].text, '-f',
                     view["format"].segments[view["format"].selected_index],
                     '--dateformat u', '--media' if view["dlMedia"].value else '',
                     save=True)
        log(sender, answer)
    else:
        console.alert("You haven't specified Channel ID or specified ID is invalid.")


def export_guild_channels(sender):
    if sender.alpha == 1.0:
        view = sender.superview
        answer = dce(view, 'exportguild', '-g', view["guildID"].text, '-f',
                     view["format"].segments[view["format"].selected_index],
                     '--dateformat u', '--media' if view["dlMedia"].value else '',
                     save=True)
        log(sender, answer)
    else:
        console.alert("You haven't specified Guild ID or specified ID is invalid.")


def export_pms(sender):
    answer = console.alert(
        "Are you sure you want to export all private message chats?",
        button1="Yes",
        button2="No",
        hide_cancel_button=True)
    if answer == 1:
        view = sender.superview
        answer = dce(view, 'exportdm', '-f',
                     view["format"].segments[view["format"].selected_index],
                     '--dateformat u', '--media' if view["dlMedia"].value else '',
                     save=True)
        log(sender, answer)


def export_all_channels(sender):
    answer = console.alert(
        "Are you sure you want to export all accessible channels?",
        button1="Yes",
        button2="No",
        hide_cancel_button=True)
    if answer == 1:
        view = sender.superview
        answer = dce(view, 'exportall', '-f',
                     view["format"].segments[view["format"].selected_index],
                     '--dateformat u', '--media' if view["dlMedia"].value else '',
                     save=True)
        log(sender, answer)


v = ui.load_view()

v["guildID"].delegate = DelegatedGuildIDTextField()
v["channelID"].delegate = DelegatedChannelIDTextField()
v["table"].delegate = DelegatedTableView()

datasource = ui.ListDataSource([])
datasource.font = ('Menlo-Regular', 10)
datasource.delete_enabled = False
v["table"].data_source = datasource

v.present('sheet')
