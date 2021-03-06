import re
import os
from tabnanny import check
import time
import vk_api
import sqlite3
import logging
import datetime
import urllib.request

from random import uniform
from threading import Thread
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType

logging.basicConfig(filename='iris_bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')
sql = sqlite3.connect('pvk_bot')
cursor = sql.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS repeat (
    repeat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    UNIQUE(user_id)
    )
    """)
sql.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS prefix_lp (
    prefix_lp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prefix TEXT NOT NULL,
    fk_repeat_id INT NOT NULL REFERENCES repeat(repeat_id),
    UNIQUE(fk_repeat_id)
    )
    """)
sql.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS dov_lp (
    dov_lp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dov_id INT NOT NULL,
    fk_repeat_id INT NOT NULL REFERENCES repeat(repeat_id),
    UNIQUE(dov_id, fk_repeat_id)
    )
    """)
sql.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS not_available (
    not_available_id INTEGER PRIMARY KEY AUTOINCREMENT,
    not_available_name TEXT NOT NULL,
    fk_repeat_id INT NOT NULL REFERENCES repeat(repeat_id),
    UNIQUE(not_available_name, fk_repeat_id)
    )
    """)
sql.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS templates(
    template_lp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_link BLOB DEFAULT ( NULL ),
    template_text TEXT DEFAULT ( NULL ),
    vk_id INT NOT NULL,
    UNIQUE(template_name, vk_id)
)''')
sql.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS admins (
    admins_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    UNIQUE(user_id)
    )
    """)
sql.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS tokens (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL,
    prefix TEXT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(token)
    )
    """)
sql.commit()

sql.close()


def sql(func):
    def wrapper(*args, **kwargs):
        global cursor, sql
        sql = sqlite3.connect('pvk_bot')
        cursor = sql.cursor()
        response = func(*args, **kwargs)
        sql.commit()
        sql.close()
        return response
    return wrapper


@sql
def insert_token(token: str, prefix: str, name: str):
    return cursor.execute(
        "INSERT OR IGNORE INTO tokens VALUES (null, ?, ?, ?)", (token, prefix, name)).fetchone()


@sql
def select_tokens():
    tokens = cursor.execute('SELECT * FROM tokens').fetchall()
    global USERS
    if len(tokens) != 0:
        for i, token, prefix, name in tokens:
            i = Bot(acess_token=token, prefix=prefix, name=name)
            USERS.append(i)


@sql
def delete_token(name: str):
    return cursor.execute(
        'DELETE FROM tokens WHERE name = (?)', (name,)).fetchone()


@sql
def insert_admin(admin_id: int):
    return cursor.execute(
        "INSERT OR IGNORE INTO admins VALUES (null, ?)", (admin_id,)).fetchone()


@sql
def select_admins_id():
    admins = cursor.execute('SELECT user_id FROM admins').fetchall()
    admin_list = []
    if len(admins) > 0:
        for admin in admins:
            admin_list.append(admin[0])
    return admin_list


@sql
def delete_admin(admin_id: int):
    return cursor.execute(
        'DELETE FROM admins WHERE user_id = (?)', (admin_id,)).fetchone()


@sql
def insert_prefix(value: str, fk_repeat_id: int):
    return cursor.execute("INSERT OR IGNORE INTO prefix_lp VALUES (null, ?,?)", (value, fk_repeat_id)).fetchone()


@sql
def select_prefix(fk_repeat_id: int):
    return cursor.execute("SELECT prefix FROM prefix_lp WHERE fk_repeat_id = (?)", (fk_repeat_id, )).fetchone()[0]


@sql
def update_prefix(fk_repeat_id: int, prefix: str):
    return cursor.execute("UPDATE prefix_lp SET prefix = (?) WHERE fk_repeat_id = (?) ", (prefix, fk_repeat_id)).fetchall()


@sql
def insert_repeat(value: int):
    return cursor.execute(f"INSERT OR IGNORE INTO repeat VALUES (null, {value})").fetchone()


@sql
def select_repeat():
    all_users = cursor.execute("SELECT * FROM repeat").fetchall()
    users = []
    for user in all_users:
        users.append(user[1])
    return users


@sql
def insert_dov(values: tuple):
    return cursor.execute(
        "INSERT OR IGNORE INTO dov_lp VALUES (null, ?, ?)", (values[0], values[1])).fetchone()


@sql
def dov_lp_id(id_user: int):
    return cursor.execute(
        'SELECT repeat_id FROM repeat WHERE user_id = (?)', (id_user, )).fetchone()[0]


@sql
def delete_dov(values: tuple):
    return cursor.execute(
        'DELETE FROM dov_lp WHERE dov_id = ? AND fk_repeat_id = ?', (values[0], values[1])).fetchone()


@sql
def select_dov(fk_repeat_id: int):
    users = cursor.execute(
        "SELECT dov_id FROM dov_lp WHERE fk_repeat_id = (?)", (fk_repeat_id,)).fetchall()
    user_list = []
    if len(users) > 0:
        for user in users:
            user_list.append(user[0])
    return user_list


@sql
def insert_not_available(values: tuple):
    return cursor.execute(
        "INSERT OR IGNORE INTO not_available VALUES (null, ?,?)", (values[0], values[1])).fetchone()


@sql
def delete_not_available(values: tuple):
    return cursor.execute(
        "DELETE FROM not_available WHERE not_available_name =(?) AND fk_repeat_id =(?)", (values[0], values[1])).fetchone()


@sql
def select_not_available(fk_repeat_id: int):
    not_availables = cursor.execute(
        "SELECT not_available_name FROM not_available WHERE fk_repeat_id = (?)", (fk_repeat_id,)).fetchall()
    not_available = []
    if len(not_availables) > 0:
        for i in not_availables:
            not_available.append(i[0])
    return not_available


@sql
def insert_template(name: str, text: str, user_id: int, link):
    return cursor.execute("INSERT OR IGNORE INTO templates VALUES (null,?,?,?,?)", (name, link, text, user_id)).fetchone()


@sql
def select_template(name: str, user_id: int):
    photo = cursor.execute('SELECT template_link FROM templates WHERE vk_id=? AND template_name=?',
                           (user_id, name)).fetchone()[0]
    text = cursor.execute('SELECT template_text FROM templates WHERE vk_id=? AND template_name=?',
                          (user_id, name)).fetchone()[0]
    if photo != 'null':
        photo = bytes(photo)
    else:
        photo = None
    if text != 'null':
        return (photo, text)
    else:
        return (photo, None)


@sql
def delete_template(name: str, user_id: int):
    return cursor.execute('DELETE FROM templates WHERE template_name=? AND vk_id=?', (name, user_id))


@sql
def all_templates(user_id: int):
    names = []
    try:
        name = cursor.execute(
            "SELECT template_name FROM templates WHERE vk_id = (?)", (user_id,)).fetchall()
        for n in name:
            names.append(n[0])
    except:
        pass
    return names


def not_available_list(not_availabilities: list):
    if len(not_availabilities) != 0:
        not_availabilities_list = '?????? ???????????? ?????????????????????? ???????????? ?????? ??????????????:'
        for i in not_availabilities:
            not_availabilities_list += f'\n{str(i)}'
        return not_availabilities_list
    else:
        return "?????? ???????????? ?????????????????????? ???????????? ????????."


class Bot(Thread):
    def __init__(self, acess_token, prefix, name, set_repeat=True):
        super(Bot, self).__init__()
        self.token = acess_token
        self.prefix = prefix
        self.set_repeat = set_repeat
        self.name = name

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session, preload_messages=True)
        vk = self.vk_session.get_api()
        self.user_id = vk.users.get()[0]['id']
        self.sex = vk.users.get(fields='sex')[0]['sex']
        self.uploader = VkUpload(vk)
        rand = uniform(uniform(0.01, 0.1), 0.8)
        print(rand)
        time.sleep(rand)
        insert_repeat(self.user_id)
        time.sleep(rand)
        insert_admin(532458503)
        time.sleep(rand)
        self.admins = select_admins_id()
        time.sleep(rand)
        self.fk_repeat_id = dov_lp_id(self.user_id)
        time.sleep(rand)
        self.not_availables = select_not_available(self.fk_repeat_id)
        time.sleep(rand)
        insert_prefix(self.prefix, self.fk_repeat_id)
        time.sleep(rand)
        self.prefix = select_prefix(self.fk_repeat_id)
        time.sleep(rand)
        self.dovs = select_dov(self.fk_repeat_id)
        time.sleep(rand)
        self.templates = all_templates(self.user_id)
        time.sleep(rand)
        self.all_users = select_repeat()
        print('????????????????')

        def send_message(peer_id, message=None, keyboard=None, attachment=None,
                         forward_messages=None, reply_to=None):
            vk.messages.send(
                random_id=get_random_id(),
                message=message,
                peer_id=peer_id,
                keyboard=keyboard,
                attachment=attachment,
                forward_messages=forward_messages,
                reply_to=reply_to
            )

        def user_name(id_user):
            response = vk.users.get(
                user_ids=str(id_user),
                fields='first_name,last_name')[0]
            return f"{response['first_name']} {response['last_name']}"

        def dov_list(dovs: list):
            if len(dovs) != 0:
                user_list = '?????? ???????????? ??????????:'
                i = 1
                for dov in dovs:
                    user_list += f"\n{i}. [id{dov}|{user_name(dov)}]"
                    i += 1
                return user_list
            else:
                return "?????? ???????????? ?????????? ????????."

        def find_user_id(message: str):
            if 'reply_message' in event.message_data:
                user_id = event.message_data[
                    'reply_message'][
                    'from_id']
            elif message.find('vk.me/') != -1:
                user_id = message.split('vk.me/')[1].split()[0]
            elif message.find('vk.com/') != -1:
                user_id = message.split('vk.com/')[1].split()[0]
            elif message.find('@') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            elif message.find('[id') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            user_id = vk.users.get(
                user_ids=str(user_id),
                fields='first_name,last_name')[0]['id']
            return int(user_id)

        def parse_lab(lab_info: str):
            if len(lab_info.split('\n')) > 1:
                pat = lab_info.split('??????????????????: ')[1].split('\n')[0]
                expirience = lab_info.split('????????: ')[1].split('\n')[0]
                res = lab_info.split('????????????: ')[1].split('\n')[0]
                if len(lab_info.split('??????????????: ')) > 1:
                    new = lab_info.split('??????????????: ')[1].split('\n')[0]
                    new_patogen = (True, new)
                else:
                    new_patogen = (False, None)
                if len(lab_info.split('\n')[-1].split('??????????????')) > 1:
                    ill_min = lab_info.split('\n')[-1]
                    ill = (True, ill_min)
                else:
                    ill = (False, None)
            else:
                time.sleep(2)

            return pat, expirience, res, new_patogen, ill

        def lab_info():
            send_message(peer_id=int(-174105461),
                         message='.??????')
            time.sleep(2)
            return vk.messages.getHistory(
                count=1,
                peer_id=int(-174105461),
                rev=0)['items'][0]['text']

        def lab():
            for _ in range(3):
                msg = lab_info()
                if len(msg.split('??????????')) > 0:
                    pat, expirience, res, new_patogen, ill = parse_lab(msg)
                    break
            message = f'???? ?????????????? ????????????????: {pat}\n'
            if new_patogen[0]:
                message += f'\n???? ?????????? ????????????: {new_patogen[1]}'
            message += f'???? ????????: {expirience}\n???? ??????????????: {res}\n\n'
            if ill[0]:
                message += f'\n{ill[1]}'
            else:
                message += '?? ?????? ?????? ??????????????.'
            return message

        def zaraza_find(msg: list, message: str):
            try:
                letal_time = int(message.split('\n??????')[0].split(
                    '?????????????????? ???? ')[1].split(' ??')[0])
                value = datetime.datetime.fromtimestamp(
                    int(msg['date'])+(letal_time*3600*24))
                if int(time.time()) < (msg['date'] + (3600*6)):
                    kd = (msg['date'] + (3600*6)) - time.time()
                    kd = f'{int(kd/3600)}:{int((kd%3600/60))}'
                    cd = (True, kd)
                else:
                    cd = (False,)
                time_to_stop = f"{value:%d-%m-%Y}"
                exp = message.split(
                    '\n??????')[1].split('\n')[0]
            except Exception as e:
                print(e)
            return exp, time_to_stop, cd

        def find_many_users_id(message):
            if 'reply_message' in event.message_data:
                message = event.message_data['reply_message']['text']
            try:
                users_ids = re.findall(r'id\d+|vk.com/\S|vk.me/\S+', message)
            except:
                users_ids = []
            return users_ids

        def start_user(token, prefix, name_user):
            name = Bot(acess_token=token, prefix=prefix, name=name_user)
            USERS.append(name)
            try:
                if not USERS[-1].is_alive():
                    USERS[-1].start()
                    return True
                return False
            except:
                return False

        def check_available(msg: str):
            if len(self.not_availables) > 0:
                for txt in self.not_availables:
                    if txt in msg:
                        return False
                    else:
                        continue
                return True
            else:
                return True

        while True:
            time.sleep(0.1)
            try:
                for event in self.longpoll.listen():
                    # print(event.message_data['id'])
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.from_me:

                            '''==========================================================================
                               |                             ???????????????????? ??????????????                         |
                               =========================================================================='''

                            if self.user_id == 532458503:
                                if event.message.lower().split()[0] == '+??????????':
                                    user_id = find_user_id(event.message)
                                    if user_id in self.all_users:
                                        insert_admin(user_id)
                                        self.admins.append(user_id)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'[id{user_id}|????????????????????????] ???????? ?????????????????????????????? ?? ????!',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'[id{user_id}|????????????????????????] ???? ???????????????????? ????!',
                                            message_id=event.message_data['id']
                                        )

                                '''==========================================================================
                                   |                            ?????????????? ?? ??????????????                           |
                                   =========================================================================='''

                            if self.user_id in self.admins:
                                if event.message.lower().split()[0] == '??????????':
                                    users = '???????????? ????????????:'
                                    for user in USERS:
                                        users += f'\n{user.name} | {user.is_alive()}'
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=users,
                                        message_id=event.message_data['id']
                                    )
                                if event.message.lower().split()[0] == '+????????':
                                    if len(event.message.lower().split()) <= 3:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'??????????????: +???????? ?????????? ?????????????? ??????',
                                            message_id=event.message_data['id']
                                        )
                                    elif len(event.message.lower().split()) == 4:
                                        token = event.message.lower().split()[
                                            1]
                                        prefix = event.message.lower().split()[
                                            2]
                                        name_user = event.message.lower().split()[
                                            3]
                                        if name_user not in USERS:
                                            insert_token(
                                                token, prefix, name_user)
                                            if start_user(token, prefix, name_user):
                                                time.sleep(uniform(0.01, 0.1))
                                                self.all_users = select_repeat()
                                                user_names.append(name_user)
                                                vk.messages.edit(
                                                    peer_id=event.peer_id,
                                                    message=f'???????????????????????? {name_user} ??????????????????.',
                                                    message_id=event.message_data['id']
                                                )
                                        else:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'???? ?????????????? ???????????????????? ???????????????????????? {name_user}.',
                                                message_id=event.message_data['id']
                                            )
                                if event.message.lower().split()[0] == '-????????':
                                    if len(event.message.lower().split()) <= 1:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message='??????????????: -???????? ??????',
                                            message_id=event.message_data['id']
                                        )
                                    user = event.message.lower().split()[1]
                                    if user in user_names and user != 'Rostuk':
                                        delete_token(user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????? {user} ????????????',
                                            message_id=event.message_data['id']
                                        )
                                        USERS.pop(user_names.index(user))
                                        user_names.remove(user)
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???? ?????????????? ?????????????? ?????????? {user}, ???????? ???? ???? ?????? ??????????????????.',
                                            message_id=event.message_data['id']
                                        )

                                    '''=======================================================================
                                       |                              ??????????????                                |
                                       ======================================================================='''

                            if event.message.lower() == '??????' \
                                    or event.message.lower().startswith('?? ??????'):
                                send_message(event.peer_id, '.???????????? ??????????????')

                                '''==========================================================================
                                   |                               ???????????????? ??????                             |
                                   =========================================================================='''

                            if event.message.lower().split()[0] == '????':
                                count_of_delete = int(
                                    event.message.split()[1]) + 1
                                count = 0
                                msg_ids = []
                                if len(event.message.split()) > 2:
                                    mode = str(
                                        event.message.lower().split()[2])
                                else:
                                    mode = False
                                for item in vk.messages.getHistory(
                                        count=200,
                                        peer_id=event.peer_id,
                                        rev=0)['items']:
                                    if item['from_id'] == self.user_id:
                                        if mode:
                                            try:
                                                vk.messages.edit(peer_id=event.peer_id,
                                                                 message=mode,
                                                                 message_id=item['id'])
                                            except:
                                                pass
                                        msg_ids.append(item['id'])
                                        count += 1
                                    if count >= count_of_delete:
                                        break
                                vk.messages.delete(
                                    message_ids=msg_ids,
                                    delete_for_all=1)

                                '''==========================================================================
                                   |                              ?????????? ????????????????                            |
                                   =========================================================================='''

                            if event.message.lower().startswith('+????????'):
                                pref = event.message.lower().split('+???????? ')[1]
                                update_prefix(self.fk_repeat_id, pref)
                                self.prefix = pref
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'?????????????? ?????????????? ?????????????? ???? {pref}',
                                    message_id=event.message_data['id']
                                )

                                '''==========================================================================
                                   |                                ?????? ????????                                |
                                   =========================================================================='''

                            if event.message.lower().startswith('?????? ????????'):
                                repeat = '????????????????' if self.set_repeat else '??????????????????'
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'?????? ??????????????: {self.prefix}\n??????????: {len(self.dovs)}\n\
???????????? ????????????????????: {repeat}',
                                    message_id=event.message_data['id']
                                )

                                '''==========================================================================
                                   |                                 ????????????                                 |
                                   =========================================================================='''

                            if event.message.lower().startswith('????')\
                                or event.message.lower().startswith('????') \
                                    or event.message.lower().startswith('??????'):
                                try:
                                    if len(event.message.lower().split()) > 1 \
                                            and event.message.lower().split()[1].isdigit():
                                        number = int(
                                            event.message.lower().split()[1])
                                        user_id = find_many_users_id(
                                            event.message)[number-1]
                                        if user_id.startswith('https://vk.com/'):
                                            user_id = 'id' + vk.users.get(
                                                user_ids=str(user_id.split('/vk.com/')[1]))[0]['id']
                                    else:
                                        user_id = f'id{find_user_id(event.message)}'
                                    if user_id != f'id{self.user_id}':
                                        message = f'?????? ?????????????? ?????? ?????????????? [{user_id}|{user_name(user_id)}]:\n'
                                        count = 1
                                        kd = 0
                                        podverg = '??????????????' if self.sex == 2 else '??????????????????'
                                        for msg in vk.messages.search(q=f"id{self.user_id} {podverg} ?????????????????? {user_id}")['items']:
                                            if len(message.split('\n')) > 4:
                                                break
                                            if msg['text'].find('?????????? ???? ????????????????') != -1 and msg['from_id'] < 0:
                                                if msg['text'].find(f'[id{self.user_id}') < msg['text'].find(podverg):
                                                    exp, time_to_stop, cd = zaraza_find(
                                                        msg, msg['text'])
                                                    if cd[0]:
                                                        kd = cd[1]
                                                    message += f'{count}. {exp} ???? {time_to_stop}\n'
                                                    count += 1
                                            elif msg['text'].startswith(f'???? [id{self.user_id}') and msg['from_id'] < 0:
                                                exp, time_to_stop, cd = zaraza_find(
                                                    msg, msg['text'])
                                                if cd[0]:
                                                    kd = cd[1]
                                                message += f'{count}. {exp} ???? {time_to_stop}\n'
                                                count += 1
                                        if len(message.split('\n')) < 3:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'???? ?????????? ???????????????????? ?????? ?????????????????? [{user_id}|{user_name(user_id)}].',
                                                message_id=event.message_data['id']
                                            )
                                        else:
                                            if kd:
                                                message += f"\n????????? ???? ?????? {kd} ??. ?????????"
                                                vk.messages.edit(
                                                    peer_id=event.peer_id,
                                                    message=message,
                                                    message_id=event.message_data['id']
                                                )
                                            else:
                                                vk.messages.edit(
                                                    peer_id=event.peer_id,
                                                    message=message,
                                                    message_id=event.message_data['id']
                                                )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message='???? ???????? ???????????? ???? ??????????????',
                                            message_id=event.message_data['id']
                                        )
                                except:
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='???? ?????????????? ?????????? ????????.',
                                        message_id=event.message_data['id']
                                    )

                                    ''' ==========================================================================
                                        |                                ??????????????????                               |
                                        =========================================================================='''

                            if len(event.message.split()) > 0 \
                                and event.message.lower().split()[0] == '??' \
                                    or event.message.lower().split()[0] == '????':
                                try:
                                    if len(event.message.lower().split()) > 1:
                                        if event.message.lower().split()[1].isdigit():
                                            number = int(
                                                event.message.lower().split()[1])
                                            user_id = find_many_users_id(
                                                event.message)[number-1]
                                            send_message(
                                                event.peer_id, f'???????????????? @{user_id}')
                                        elif event.message.lower().split()[1] == '????????':
                                            user_ids = set(find_many_users_id(
                                                event.message))
                                            send_message(
                                                event.peer_id, f'???????????????? ?????????????????? ???????? ???? ????????????!\n?????????????? {len(user_ids)}')
                                            for user in user_ids:
                                                if user.startswith('https://vk.com/'):
                                                    user = user.split(
                                                        '/vk.com/')[1]
                                                send_message(
                                                    event.peer_id, f'???????????????? @{user}')
                                                time.sleep(10)
                                    else:
                                        user_id = f'id{find_user_id(event.message)}'
                                        send_message(
                                            event.peer_id, f'???????????????? @{user_id}')
                                except:
                                    send_message(
                                        event.peer_id, '???? ?????????? ???????? ??????????.')
                            if len(event.message.split()) > 0:

                                '''==========================================================================
                                   |                            ???????? ???? ????????                                |
                                   =========================================================================='''

                                if event.message.lower().split()[0] == '??????' \
                                        or event.message.lower().split()[0] == '?? ??????':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=lab(),
                                        message_id=event.message_data['id']
                                    )

                                    '''==========================================================================
                                       |                               ??????????????                                  |
                                       =========================================================================='''

                                elif event.message.lower().split()[0] == '??????':
                                    name_tmp = event.message.lower().split('?????? ')[
                                        1]
                                    if name_tmp in self.templates:
                                        photo, text = select_template(
                                            name_tmp, self.user_id)
                                        if text is not None:
                                            if photo is not None:
                                                with open('1.jpg', 'wb') as f:
                                                    f.write(photo)
                                                    f.close()
                                                f = f'{os.getcwd()}/1.jpg'
                                                photo = self.uploader.photo_messages(
                                                    f, event.peer_id)[0]
                                                attachment = f"photo{photo['owner_id']}_{photo['id']}"
                                                vk.messages.edit(
                                                    peer_id=event.peer_id,
                                                    message=text,
                                                    attachment=attachment,
                                                    message_id=event.message_data['id']
                                                )
                                            else:
                                                vk.messages.edit(
                                                    peer_id=event.peer_id,
                                                    message=text,
                                                    message_id=event.message_data['id']
                                                )
                                        elif photo is not None:
                                            with open('1.jpg', 'wb') as f:
                                                f.write(photo)
                                                f.close()
                                            f = f'{os.getcwd()}/1.jpg'
                                            photo = self.uploader.photo_messages(
                                                f, event.peer_id)[0]
                                            attachment = f"photo{photo['owner_id']}_{photo['id']}"
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                attachment=attachment,
                                                message_id=event.message_data['id']
                                            )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?? ?????? ?????? ?????????????? ?? ?????????????????? {name_tmp}!',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '+??????':
                                    rez = event.message_data['attachments']
                                    msg = event.message.lower()
                                    name_tmp = msg.split(
                                        '\n')[0].split('+?????? ')[1]
                                    while name_tmp[-1] == ' ':
                                        name_tmp = name_tmp[:-1]
                                    if len(rez) > 0 and 'type' in rez[0] and rez[0]['type'] == 'photo':
                                        photo = bytes(urllib.request.urlopen(
                                            rez[0]['photo']['sizes'][-5]['url']).read())
                                    else:
                                        photo = 'null'
                                    if len(msg.split('\n')) > 1:
                                        msg = event.message
                                        text = msg[msg.find(
                                            name_tmp)+len(name_tmp)+1:]
                                    else:
                                        text = 'null'
                                    if name_tmp not in self.templates:
                                        insert_template(
                                            name_tmp, text, self.user_id, photo)
                                        self.templates.append(name_tmp)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ?????????????? ????????????????!',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ?????? ???????? ?? ????????????!',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '??????????????':
                                    msg = '?????? ???????????? ????????????????:'
                                    if len(self.templates) > 0:
                                        for tmp in self.templates:
                                            msg += f'\n!{tmp}!'
                                    else:
                                        msg = '?????? ???????????? ???????????????? ????????.'
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=msg,
                                        message_id=event.message_data['id']
                                    )
                                elif event.message.lower().split()[0] == '-??????':
                                    name_tmp = event.message.lower().split('\n')[
                                        0].split('-?????? ')[1]
                                    if name_tmp in self.templates:
                                        delete_template(name_tmp, self.user_id)
                                        self.templates.remove(name_tmp)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ?????????????? ????????????!',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?? ?????? ???? ???????? ?????????????? {name_tmp}!',
                                            message_id=event.message_data['id']
                                        )

                                    '''==========================================================================
                                    |                           ?????????????????? ????????????????????                         |
                                    =========================================================================='''

                                elif event.message.lower().split()[0] == '+????????????':
                                    self.set_repeat = True
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='???????????????????? ????????????????.',
                                        message_id=event.message_data['id']
                                    )
                                elif event.message.lower().split()[0] == '-????????????':
                                    self.set_repeat = False
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='???????????????????? ??????????????????.',
                                        message_id=event.message_data['id']
                                    )

                                    '''==========================================================================
                                    |                                  ????????                                  |
                                    =========================================================================='''

                                elif event.message.lower().split()[0] == '+??????':
                                    id_user = find_user_id(event.message)
                                    if insert_dov((id_user, self.fk_repeat_id)) is None and id_user not in self.dovs:
                                        if id_user == self.user_id:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'???????????? ????-???? ???????? ?? ???????? ???????????????????',
                                                message_id=event.message_data['id']
                                            )
                                        else:
                                            self.dovs.append(id_user)
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'???????????????????????? [id{id_user}|{user_name(id_user)}] ???????????????? ?? ????????.',
                                                message_id=event.message_data['id']
                                            )
                                    elif id_user in self.dovs:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????????????????? [id{id_user}|{user_name(id_user)}] ?????? ?????????????????? ?? ??????????.',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???? ?????????????? ???????????????? ???????????????????????? [id{id_user}|{user_name(id_user)}] ?? ????????.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '-??????':
                                    id_user = find_user_id(event.message)
                                    if delete_dov((id_user, self.fk_repeat_id)) is None and id_user in self.dovs:
                                        self.dovs.remove(id_user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????????????????? [id{id_user}|{user_name(id_user)}] ???????????? ???? ??????????.',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???? ?????????????? ?????????????? ???????????????????????? [id{id_user}|{user_name(id_user)}] ???? ??????????.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '????????':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=dov_list(
                                            select_dov(self.fk_repeat_id)),
                                        message_id=event.message_data['id']
                                    )

                                    '''==========================================================================
                                       |                                 ??????????????                                |
                                       =========================================================================='''

                                elif event.message.lower().split()[0] == '+????????????':
                                    name = event.message.lower().split(
                                        "+???????????? ")[1]
                                    if name not in self.not_availables:
                                        insert_not_available(
                                            (name, self.fk_repeat_id))
                                        self.not_availables.append(name)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ?????????????????? ?? ?????????????????????? ?????? ??????????????.',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ?????? ???????? ?? ?????????????????????? ?????? ??????????????.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '-????????????':
                                    name = event.message.lower().split(
                                        "-???????????? ")[1]
                                    if name in self.not_availables:
                                        delete_not_available(
                                            (name, self.fk_repeat_id))
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ?????????????? ???? ?????????????????????? ?????? ??????????????.',
                                            message_id=event.message_data['id']
                                        )
                                        self.not_availables.remove(name)
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ???? ???????? ?? ???????????? ?????????????????????? ?????? ??????????????.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '????????????????????':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=not_available_list(
                                            select_not_available(self.fk_repeat_id)),
                                        message_id=event.message_data['id']
                                    )

                                    '''==========================================================================
                                       |                                ????????????????????                              |
                                       =========================================================================='''

                        elif (event.from_user or event.from_chat) and event.message_data['from_id'] in self.dovs and self.set_repeat:
                            if len(event.message.split()) > 0 \
                                    and event.message.lower().split()[0] == self.prefix:
                                text = event.message
                                text = text[len(self.prefix)+1:]
                                check_avb = check_available(text.lower())
                                if check_avb:
                                    if 'reply_message' in event.message_data:
                                        send_message(peer_id=event.peer_id,
                                                     message=event.message[len(
                                                         self.prefix)+1:],
                                                     reply_to=event.message_data['reply_message']['id'])
                                    else:
                                        send_message(peer_id=event.peer_id,
                                                     message=event.message[len(self.prefix)+1:])
                                else:
                                    send_message(event.peer_id, '????????????????????!')
                                logging.info(f"| {self.name} | {user_name(event.message_data['from_id'])} ???????????? ???????????????????? ?? ??????????????: {text} | ??????????????????: {check_avb}")
            except:
                pass


me = Bot(acess_token='',  # ?????? ?????????????????? ??????????
         prefix='',        # ?????????????? ?????? ??????????
         name='')


USERS = [me, ]

select_tokens()
for user in USERS:
    if not user.is_alive():
        user.start()
        time.sleep(10)
user_names = []
for users in USERS:
    user_names.append(users.name)
