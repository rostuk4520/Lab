import re
import vk_api
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread
import datetime
import time
import sqlite3
import random

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
cursor.execute('''CREATE TABLE IF NOT EXISTS template_lp(
    template_lp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_content TEXT NOT NULL,
    vk_id INT NOT NULL,
    UNIQUE(template_name, vk_id)
)''')
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
def insert_prefix(value: str, fk_repeat_id: int):
    return cursor.execute("INSERT OR IGNORE INTO prefix_lp VALUES (null, ?,?)", (value, fk_repeat_id)).fetchone()


@sql
def select_prefix(fk_repeat_id: int):
    return cursor.execute(f"SELECT prefix FROM prefix_lp WHERE fk_repeat_id = {fk_repeat_id}").fetchone()[0]


@sql
def update_prefix(fk_repeat_id: int, prefix: str):
    return cursor.execute(f"UPDATE prefix_lp SET prefix = (?) WHERE fk_repeat_id = (?) ", (prefix, fk_repeat_id)).fetchall()


@sql
def insert_repeat(value: int):
    return cursor.execute(f"INSERT OR IGNORE INTO repeat VALUES (null, {value})").fetchone()


@sql
def select_repeat():
    return cursor.execute("SELECT * FROM repeat").fetchall()


@sql
def insert_dov(values: tuple):
    return cursor.execute(
        f"INSERT OR IGNORE INTO dov_lp VALUES (null, {values[0]}, {values[1]})").fetchone()


@sql
def dov_lp_id(id_user: int):
    return cursor.execute(
        f'SELECT repeat_id FROM repeat WHERE user_id ={id_user}').fetchone()[0]


@sql
def delete_dov(values: tuple):
    return cursor.execute(
        f'DELETE FROM dov_lp WHERE dov_id ={values[0]} AND fk_repeat_id = {values[1]}').fetchone()


@sql
def select_dov(fk_repeat_id: int):
    users = cursor.execute(
        f"SELECT dov_id FROM dov_lp WHERE fk_repeat_id = {fk_repeat_id}").fetchall()
    user_list = []
    if len(users) != 0:
        for user in users:
            user_list.append(user[0])
        return user_list
    else:
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
        f"SELECT not_available_name FROM not_available WHERE fk_repeat_id = {fk_repeat_id}").fetchall()
    not_available = []
    if len(not_availables) != 0:
        for i in not_availables:
            not_available.append(i[0])
        return not_available
    else:
        return not_available


@sql
def insert_template(name: str, content: str, user_id: int):
    return cursor.execute("INSERT OR IGNORE INTO template_lp VALUES (null,?,?,?)", (name, content, user_id)).fetchone()


@sql
def select_template(name: str, user_id: int):
    return cursor.execute('SELECT template_content FROM template_lp WHERE vk_id=? AND template_name=?', (user_id, name)).fetchone()[0]


@sql
def delete_template(name: str, user_id: int):
    return cursor.execute('DELETE FROM template_lp WHERE template_name=? AND vk_id=?', (name, user_id))


@sql
def all_templates(user_id: int):
    templates = []
    try:
        template = cursor.execute(
            "SELECT template_name FROM template_lp WHERE vk_id = (?)", (user_id,)).fetchall()
        for n in template:
            templates.append(n[0])
    except:
        templates = []
    return templates


def not_available_list(not_availabilities: list):
    if len(not_availabilities) != 0:
        not_availabilities_list = '?????? ???????????? ?????????????????????? ???????????? ?????? ??????????????:'
        for i in not_availabilities:
            not_availabilities_list += f'\n{str(i)}'
        return not_availabilities_list
    else:
        return "?????? ???????????? ?????????????????????? ???????????? ????????."


def change_prefix(fk_repeat_id, pref):
    select_prefix(fk_repeat_id)


class Bot(Thread):
    def __init__(self, acess_token, prefix, set_repeat=True):
        super(Bot, self).__init__()
        self.token = acess_token
        self.prefix = prefix
        self.set_repeat = set_repeat

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        vk = self.vk_session.get_api()
        self.user_id = vk.users.get()[0]['id']
        self.sex = vk.users.get(fields='sex')[0]['sex']
        time.sleep(random.uniform(0.1, 1))
        insert_repeat(self.user_id)
        time.sleep(random.uniform(0.1, 1))
        self.fk_repeat_id = dov_lp_id(self.user_id)
        time.sleep(random.uniform(0.1, 1))
        self.not_availables = select_not_available(self.fk_repeat_id)
        insert_prefix(self.prefix, self.fk_repeat_id)
        time.sleep(random.uniform(0.1, 1))
        self.prefix = select_prefix(self.fk_repeat_id)
        time.sleep(random.uniform(0.1, 1))
        self.dovs = select_dov(self.fk_repeat_id)
        time.sleep(random.uniform(0.1, 1))
        self.templates = all_templates(self.user_id)
        print('????????????????')

        def send_message(peer_id, message=None, keyboard=None, attachment=None,
                         forward_messages=None):
            vk.messages.setActivity(
                user_id=str(self.user_id),
                type='typing',
                peer_id=peer_id)
            vk.messages.send(
                random_id=get_random_id(),
                message=message,
                peer_id=peer_id,
                keyboard=keyboard,
                attachment=attachment,
                forward_messages=forward_messages,
            )

        def user_name(id_user):
            response = vk.users.get(
                user_ids=str(id_user),
                fields='first_name,last_name')[0]
            first_name = response['first_name']
            last_name = response['last_name']
            name = first_name + ' ' + last_name
            return name

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
            if 'reply_message' in vk.messages.getHistory(
                    count=1,
                    peer_id=event.peer_id,
                    rev=0)['items'][0]:
                user_id = vk.messages.getHistory(count=1,
                                                 peer_id=event.peer_id,
                                                 rev=0)['items'][0][
                    'reply_message'][
                    'from_id']
            elif message.find('https://vk.com/') != -1:
                user_id = message.split('https://vk.com/')[1]
            elif message.find('@') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            elif message.find('[id') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            else:
                user_id = 0
            user_id = vk.users.get(
                user_ids=str(user_id),
                fields='first_name,last_name')[0]['id']
            return int(user_id)

        def find_user(message: str):
            if 'reply_message' in vk.messages.getHistory(
                    count=1,
                    peer_id=event.peer_id,
                    rev=0)['items'][0]:
                user_id = vk.messages.getHistory(count=1,
                                                 peer_id=event.peer_id,
                                                 rev=0)['items'][0][
                    'reply_message'][
                    'from_id']
            elif message.find('https://vk.com/') != -1:
                user_id = message.split('https://vk.com/')[1]
            elif message.find('@') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            else:
                user_id = 0
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
                send_message(peer_id=int(-174105461), message='.??????')
                time.sleep(2)
                lab_info = vk.messages.getHistory(
                    count=1,
                    peer_id=int(-174105461),
                    rev=0)['items'][0]['text']
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
                    pat = expirience = res = '?????? ????????('
                    new_patogen = (False, None)
                    ill = (False, None)
            return pat, expirience, res, new_patogen, ill

        def lab():
            send_message(peer_id=int(-174105461), message='.??????')
            time.sleep(2)
            text = vk.messages.getHistory(
                count=1,
                peer_id=int(-174105461),
                rev=0)['items'][0]['text']
            pat, expirience, res, new_patogen, ill = parse_lab(text)
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
            if 'reply_message' in vk.messages.getHistory(
                    count=1,
                    peer_id=event.peer_id,
                    rev=0)['items'][0]:
                message = vk.messages.getHistory(
                    count=1,
                    peer_id=event.peer_id,
                    rev=0)['items'][0]['reply_message']['text']
            try:
                users_ids = re.findall(r'id\d+', message)
            except:
                users_ids = []
            return users_ids

        while True:
            time.sleep(0.1)
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.from_me:
                            if event.message.lower() == '??????' \
                                    or event.message.lower().startswith('?? ??????'):
                                send_message(event.peer_id, '.???????????? ??????????????')
                            if event.message.lower().startswith('+????????'):
                                id_message = vk.messages.getHistory(
                                    count=1,
                                    peer_id=event.peer_id,
                                    rev=0)['items'][0]['id']
                                pref = event.message.lower().split('+???????? ')[1]
                                update_prefix(self.fk_repeat_id, pref)
                                self.prefix = pref
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'?????????????? ?????????????? ?????????????? ???? {pref}',
                                    message_id=id_message
                                )
                            if event.message.lower().startswith('?????? ????????'):
                                repeat = '????????????????' if self.set_repeat else '??????????????????'
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'?????? ??????????????: {select_prefix(self.fk_repeat_id)}\n??????????: {len(select_dov(self.fk_repeat_id))}]\n\
???????????? ????????????????????: {repeat}',
                                    message_id=vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                )
                            if event.message.lower().startswith('????')\
                                or event.message.lower().startswith('????') \
                                    or event.message.lower().startswith('??????'):
                                id_message = vk.messages.getHistory(
                                    count=1,
                                    peer_id=event.peer_id,
                                    rev=0)['items'][0]['id']
                                try:
                                    if len(event.message.lower().split()) > 1 \
                                            and event.message.lower().split()[1].isdigit():
                                        number = int(
                                            event.message.lower().split()[1])
                                        user_id = find_many_users_id(
                                            event.message)[number-1]
                                    else:
                                        user_id = f'id{find_user_id(event.message)}'
                                    message = f'?????? ?????????????? ?????? ?????????????? [id{user_id}|??????]:\n'
                                    count = 1
                                    kd = 0
                                    podverg = '??????????????' if self.sex == 2 else '??????????????????'
                                    for msg in vk.messages.search(q=f"id{self.user_id} {podverg} ?????????????????? id{user_id}")['items']:
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
                                    if message == f'?????? ?????????????? ?????? ?????????????? [{user_id}|??????]\n':
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???? ?????????? ???????????????????? ?????? ?????????????????? [id{user_id}|????????????????????????].',
                                            message_id=id_message
                                        )
                                    else:
                                        if kd:
                                            message += f"\n????????? ???? ?????? {kd} ??. ?????????"
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=message,
                                                message_id=id_message
                                            )
                                        else:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=message,
                                                message_id=id_message
                                            )
                                except:
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='???? ?????????????? ?????????? ????????.',
                                        message_id=id_message
                                    )

                            if len(event.message.split()) > 0 \
                                and event.message.lower().split()[0] == '??' \
                                    or event.message.lower().split()[0] == '????':
                                try:
                                    if len(event.message.lower().split()) > 1 \
                                            and event.message.lower().split()[1].isdigit():
                                        number = int(
                                            event.message.lower().split()[1])
                                        user_id = find_many_users_id(
                                            event.message)[number-1]
                                    else:
                                        user_id = f'id{find_user_id(event.message)}'
                                    send_message(
                                        event.peer_id, f'???????????????? @{user_id}')
                                except:
                                    send_message(
                                        event.peer_id, '???? ?????????? ???????? ??????????.')
                            if len(event.message.lower().split()) > 0:
                                if event.message.lower().split()[0] == '??????' \
                                        or event.message.lower().split()[0] == '?? ??????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=lab(),
                                        message_id=id_message
                                    )
                                if event.message.lower().split()[0] == '+??????':
                                    name_tmp = event.message.lower().split(
                                        '\n')[0].split('+?????? ')[1]
                                    content_tmp = event.message.split(
                                        f'{name_tmp}\n')[1]
                                    if name_tmp in self.templates:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ?????? ????????????????????!',
                                            message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id'])
                                    else:
                                        insert_template(
                                            name_tmp, content_tmp, self.user_id)
                                        self.templates.append(name_tmp)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ????????????????!',
                                            message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id'])
                                elif event.message.lower().split()[0] == '-??????':
                                    name_tmp = event.message.lower().split(
                                        '\n')[0].split('-?????? ')[1]
                                    if name_tmp in self.templates:
                                        delete_template(
                                            name_tmp, self.user_id)
                                        self.templates.remove(name_tmp)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ????????????!',
                                            message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id'])
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?? ?????? ?????? ?????????????? {name_tmp}.',
                                            message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id'])
                                elif event.message.lower().split()[0] == '??????':
                                    name_tmp = event.message.lower().split('?????? ')[
                                        1]
                                    if name_tmp in self.templates:
                                        tmp = select_template(
                                            name_tmp, self.user_id)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=tmp,
                                            message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id'])
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????? {name_tmp} ???? ????????????????????.',
                                            message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id'])
                                elif event.message.lower().split()[0] == '??????????????':
                                    text = '???????????? ?????????? ????????????????:'
                                    for tmp in self.templates:
                                        text += f'\n{tmp}'
                                    if text == '???????????? ?????????? ????????????????:':
                                        text = '?? ?????? ?????? ?????????????????????? ????????????????.'
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=text,
                                        message_id=vk.messages.getHistory(
                                            count=1,
                                            peer_id=event.peer_id,
                                            rev=0)['items'][0]['id'])
                                elif event.message.lower().split()[0] == '+????????????':
                                    self.set_repeat = True
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='???????????????????? ????????????????.',
                                        message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id']
                                    )
                                elif event.message.lower().split()[0] == '-????????????':
                                    self.set_repeat = False
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='???????????????????? ??????????????????.',
                                        message_id=vk.messages.getHistory(
                                                count=1,
                                                peer_id=event.peer_id,
                                                rev=0)['items'][0]['id']
                                    )
                                elif event.message.lower().split()[0] == '+??????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    id_user = find_user(event.message)
                                    if insert_dov((id_user, self.fk_repeat_id)) is None:
                                        self.dovs.append(id_user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????????????????? [id{id_user}|{user_name(id_user)}] ???????????????? ?? ????????.',
                                            message_id=id_message
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???? ?????????????? ???????????????? ???????????????????????? [id{id_user}|{user_name(id_user)}] ?? ????????.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == '-??????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    id_user = find_user(event.message)
                                    if delete_dov((id_user, self.fk_repeat_id)) is None:
                                        self.dovs.remove(id_user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???????????????????????? [id{id_user}|{user_name(id_user)}] ???????????? ???? ??????????.',
                                            message_id=id_message
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'???? ?????????????? ?????????????? ???????????????????????? [id{id_user}|{user_name(id_user)}] ???? ??????????.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == '????????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=dov_list(
                                            select_dov(self.fk_repeat_id)),
                                        message_id=id_message
                                    )
                                elif event.message.lower().split()[0] == '+????????????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    name = event.message.lower().split(
                                        "+???????????? ")[1]
                                    if name not in self.not_availables:
                                        insert_not_available(
                                            (name, self.fk_repeat_id))
                                        self.not_availables.append(name)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ?????????????????? ?? ?????????????????????? ?????? ??????????????.',
                                            message_id=id_message
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ?????? ???????? ?? ?????????????????????? ?????? ??????????????.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == '-????????????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    name = event.message.lower().split(
                                        "-???????????? ")[1]
                                    if name in self.not_availables:
                                        delete_not_available(
                                            (name, self.fk_repeat_id))
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ?????????????? ???? ?????????????????????? ?????? ??????????????.',
                                            message_id=id_message
                                        )
                                        self.not_availables.remove(name)
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'?????????????? {name} ???? ???????? ?? ???????????? ?????????????????????? ?????? ??????????????.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == '????????????????????':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=not_available_list(
                                            select_not_available(self.fk_repeat_id)),
                                        message_id=id_message
                                    )
                        elif (event.from_user or event.from_chat) and event.user_id in self.dovs and self.set_repeat:
                            if len(event.message.split()) > 0 \
                                    and event.message.lower().split()[0] == self.prefix:
                                text = event.message
                                text = text[len(self.prefix)+1:]

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
                                if check_available(text.lower()):
                                    result = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]
                                    if 'reply_message' in result:
                                        vk.messages.setActivity(
                                            user_id=str(self.user_id),
                                            type='typing',
                                            peer_id=event.peer_id)
                                        vk.messages.send(
                                            random_id=get_random_id(),
                                            peer_id=event.peer_id,
                                            message=event.message[len(
                                                self.prefix)+1:],
                                            reply_to=result['reply_message']['id'])
                                    else:
                                        vk.messages.send(
                                            random_id=get_random_id(),
                                            peer_id=event.peer_id,
                                            message=event.message[len(self.prefix)+1:])
                                else:
                                    vk.messages.send(
                                        random_id=get_random_id(),
                                        peer_id=event.peer_id,
                                        message='????????????????????!')
            except:
                pass


me = Bot(acess_token='',
           prefix='pref')

USERS = [me]

for user in USERS:
    user.start()
