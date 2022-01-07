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


def not_available_list(not_availabilities: list):
    if len(not_availabilities) != 0:
        not_availabilities_list = 'Ваш список запрещённых команд для повтора:'
        for i in not_availabilities:
            not_availabilities_list += f'\n{str(i)}'
        return not_availabilities_list
    else:
        return "Ваш список запрещённых команд пуст."


def change_prefix(fk_repeat_id, pref):
    select_prefix(fk_repeat_id)


class Bot(Thread):
    def __init__(self, acess_token, prefix):
        super(Bot, self).__init__()
        self.token = acess_token
        self.prefix = prefix

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        vk = self.vk_session.get_api()
        self.user_id = vk.users.get()[0]['id']
        time.sleep(random.randint(1, 3))
        insert_repeat(self.user_id)
        time.sleep(random.randint(1, 3))
        self.fk_repeat_id = dov_lp_id(self.user_id)
        time.sleep(random.randint(1, 3))
        self.not_availables = select_not_available(self.fk_repeat_id)
        insert_prefix(self.prefix, self.fk_repeat_id)
        time.sleep(random.randint(1, 3))
        self.prefix = select_prefix(self.fk_repeat_id)
        time.sleep(random.randint(1, 3))
        self.dovs = select_dov(self.fk_repeat_id)
        print('запущено')

        def send_message(peer_id, message=None, keyboard=None, attachment=None,
                         forward=None):
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
                forward=forward,
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
                user_list = 'Ваш список довов:'
                i = 1
                for dov in dovs:
                    user_list += f"\n{i}. [id{dov}|{user_name(dov)}]"
                    i += 1
                return user_list
            else:
                return "Ваш список довов пуст."

        def find_user_id(message):
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

        def find_user(message):
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
                pat = lab_info.split('патогенов: ')[1].split('\n')[0]
                expirience = lab_info.split('опыт: ')[1].split('\n')[0]
                res = lab_info.split('ресурс: ')[1].split('\n')[0]
                if len(lab_info.split('патоген: ')) > 1:
                    new = lab_info.split('патоген: ')[1].split('\n')[0]
                    new_patogen = (True, new)
                else:
                    new_patogen = (False, None)
                if len(lab_info.split('\n')[-1].split('горячки')) > 1:
                    ill_min = lab_info.split('\n')[-1]
                    ill = (True, ill_min)
                else:
                    ill = (False, None)
            else:
                time.sleep(2)
                send_message(peer_id=int(-174105461), message='.лаб')
                time.sleep(2)
                lab_info = vk.messages.getHistory(
                    count=1,
                    peer_id=int(-174105461),
                    rev=0)['items'][0]['text']
                if len(lab_info.split('\n')) > 1:
                    pat = lab_info.split('патогенов: ')[1].split('\n')[0]
                    expirience = lab_info.split('опыт: ')[1].split('\n')[0]
                    res = lab_info.split('ресурс: ')[1].split('\n')[0]
                    if len(lab_info.split('патоген: ')) > 1:
                        new = lab_info.split('патоген: ')[1].split('\n')[0]
                        new_patogen = (True, new)
                    else:
                        new_patogen = (False, None)
                    if len(lab_info.split('\n')[-1].split('горячки')) > 1:
                        ill_min = lab_info.split('\n')[-1]
                        ill = (True, ill_min)
                    else:
                        ill = (False, None)
                else:
                    pat = expirience = res = 'нет инфы('
                    new_patogen = (False, None)
                    ill = (False, None)
            return pat, expirience, res, new_patogen, ill

        def lab():
            send_message(peer_id=int(-174105461), message='.лаб')
            time.sleep(2)
            text = vk.messages.getHistory(
                count=1,
                peer_id=int(-174105461),
                rev=0)['items'][0]['text']
            pat, expirience, res, new_patogen, ill = parse_lab(text)
            message = f'💉 Готовых снарядов: {pat}\n'
            if new_patogen[0]:
                message += f'\n🔫 Новый снаряд: {new_patogen[1]}'
            message += f'💸 Опыт: {expirience}\n🎇 Ресурсы: {res}\n\n'
            if ill[0]:
                message += f'\n{ill[1]}'
            else:
                message += 'У вас нет горячки.'
            return message

        while True:
            time.sleep(0.1)
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.from_me:
                            if event.message.lower().startswith('+преф'):
                                id_message = vk.messages.getHistory(
                                    count=1,
                                    peer_id=event.peer_id,
                                    rev=0)['items'][0]['id']
                                pref = event.message.lower().split('+преф ')[1]
                                update_prefix(self.fk_repeat_id, pref)
                                self.prefix = pref
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Префикс успешно изменён на {pref}',
                                    message_id=id_message
                                )
                            if event.message.lower().startswith('чек преф'):
                                
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Ваш префикс: {select_prefix(self.fk_repeat_id)}\nДовов: {len(select_dov(self.fk_repeat_id))}',
                                    message_id=vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                )
                            if event.message.lower().startswith('л лаб'):
                                id_message = vk.messages.getHistory(
                                    count=1,
                                    peer_id=event.peer_id,
                                    rev=0)['items'][0]['id']
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=lab(),
                                    message_id=id_message
                                )
                            if event.message.lower().startswith('зр'):
                                id_message = vk.messages.getHistory(
                                    count=1,
                                    peer_id=event.peer_id,
                                    rev=0)['items'][0]['id']
                                user_id = find_user_id(event.message)
                                message = f'Вот столько раз заражал [id{user_id}|ево]:\n'
                                count = 1
                                for msg in vk.messages.search(q=f"id{self.user_id} подверг заражению id{user_id}")['items']:
                                    if msg['text'].startswith(f'🦠 [id{self.user_id}') and msg['from_id'] < 0:
                                        letal_time = int(msg['text'].split('\n☣️')[0].split(
                                            'Заражение на ')[1].split(' д')[0])
                                        timestamp = int(
                                            msg['date'])+(letal_time*3600*24)
                                        value = datetime.datetime.fromtimestamp(
                                            timestamp)
                                        time_to_stop = f"{value:%d-%m-%Y}"
                                        exp = msg['text'].split(
                                            '\n☣️')[1].split('\n')[0]
                                        message += f'{count}. {exp} до {time_to_stop}\n'
                                        count += 1
                                count = 0
                                if message == f'Вот столько раз заражал [id{user_id}|ево]\n':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=f'Не нашёл информации про заражения [id{user_id}|пользователя].',
                                        message_id=id_message
                                    )
                                else:
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=message,
                                        message_id=id_message
                                    )
                            if len(event.message.lower().split()) > 0:
                                if event.message.lower().split()[0] == '+дов':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    id_user = find_user(event.message)
                                    if insert_dov((id_user, self.fk_repeat_id)) is None:
                                        self.dovs.append(id_user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Пользователь [id{id_user}|{user_name(id_user)}] добавлен в довы.',
                                            message_id=id_message
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Не удалось добавить пользователя [id{id_user}|{user_name(id_user)}] в довы.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == '-дов':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    id_user = find_user(event.message)
                                    if delete_dov((id_user, self.fk_repeat_id)) is None:
                                        self.dovs.remove(id_user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Пользователь [id{id_user}|{user_name(id_user)}] удалён из довов.',
                                            message_id=id_message
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Не удалось удалить пользователя [id{id_user}|{user_name(id_user)}] из довов.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == 'довы':
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
                                elif event.message.lower().split()[0] == '+запрет':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    name = event.message.lower().split("+запрет ")[1]
                                    if name not in self.not_availables:
                                        insert_not_available(
                                            (name, self.fk_repeat_id))
                                        self.not_availables.append(name)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда {name} добавлена в запрещённые для повтора.',
                                            message_id=id_message
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда {name} уже есть в запрещённых для повтора.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == '-запрет':
                                    id_message = vk.messages.getHistory(
                                        count=1,
                                        peer_id=event.peer_id,
                                        rev=0)['items'][0]['id']
                                    name = event.message.lower().split("-запрет ")[1]
                                    if name in self.not_availables:
                                        delete_not_available(
                                            (name, self.fk_repeat_id))
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда {name} удалена из запрещённых для повтора.',
                                            message_id=id_message
                                        )
                                        self.not_availables.remove(name)
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команды {name} не было в списке запрещённых для повтора.',
                                            message_id=id_message
                                        )
                                elif event.message.lower().split()[0] == 'запретлист':
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
                        elif (event.from_user or event.from_chat) and event.user_id in self.dovs:
                            if len(event.message.lower().split()) > 0 \
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
                                    vk.messages.send(
                                        random_id=get_random_id(),
                                        peer_id=event.peer_id,
                                        message=event.message[len(self.prefix)+1:])
                                else:
                                    vk.messages.send(
                                        random_id=get_random_id(),
                                        peer_id=event.peer_id,
                                        message='Недоступно!')
            except Exception as e:
                print(e)


me = Bot(acess_token='token',
         prefix='pref')

USERS = [me, ]

for user in USERS:
    user.start()
