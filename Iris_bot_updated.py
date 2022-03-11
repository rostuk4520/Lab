import re
import vk_api
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from random import uniform
from threading import Thread
import datetime
import time
import sqlite3


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
    return cursor.execute("SELECT * FROM repeat").fetchall()


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
    template = cursor.execute(
        "SELECT template_name FROM template_lp WHERE vk_id = (?)", (user_id,)).fetchall()
    if len(template) > 0:
        for n in template:
            templates.append(n[0])
    return templates


def not_available_list(not_availabilities: list):
    if len(not_availabilities) != 0:
        not_availabilities_list = 'Ваш список запрещённых команд для повтора:'
        for i in not_availabilities:
            not_availabilities_list += f'\n{str(i)}'
        return not_availabilities_list
    else:
        return "Ваш список запрещённых команд пуст."


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
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        insert_repeat(self.user_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        insert_admin(532458503)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.admins = select_admins_id()
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.fk_repeat_id = dov_lp_id(self.user_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.not_availables = select_not_available(self.fk_repeat_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        insert_prefix(self.prefix, self.fk_repeat_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.prefix = select_prefix(self.fk_repeat_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.dovs = select_dov(self.fk_repeat_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.templates = all_templates(self.user_id)
        time.sleep(uniform(uniform(0.01, 0.4), 1))
        self.all_users = select_repeat()
        print('запущено')

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
                user_list = 'Ваш список довов:'
                i = 1
                for dov in dovs:
                    user_list += f"\n{i}. [id{dov}|{user_name(dov)}]"
                    i += 1
                return user_list
            else:
                return "Ваш список довов пуст."

        def find_user_id(message: str):
            if 'reply_message' in event.message_data:
                user_id = event.message_data[
                    'reply_message'][
                    'from_id']
            elif message.find('https://vk.com/') != -1:
                user_id = message.split('https://vk.com/')[1].split()[0]
            elif message.find('@') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            elif message.find('[id') != -1:
                user_id = message.split('[id')[1].split('|')[0]
            user_id = vk.users.get(
                user_ids=str(user_id),
                fields='first_name,last_name')[0]['id']
            return int(user_id)

        def find_user(message: str):
            if 'reply_message' in event.message_data:
                user_id = event.message_data['reply_message']['from_id']
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

            return pat, expirience, res, new_patogen, ill

        def lab_info():
            send_message(peer_id=int(-174105461),
                         message='.лаб')
            time.sleep(2)
            return vk.messages.getHistory(
                count=1,
                peer_id=int(-174105461),
                rev=0)['items'][0]['text']

        def lab():
            for _ in range(3):
                msg = lab_info()
                if len(msg.split('Досье')) > 0:
                    pat, expirience, res, new_patogen, ill = parse_lab(msg)
                    break
            message = f'💉 Готовых снарядов: {pat}\n'
            if new_patogen[0]:
                message += f'\n🔫 Новый снаряд: {new_patogen[1]}'
            message += f'💸 Опыт: {expirience}\n🎇 Ресурсы: {res}\n\n'
            if ill[0]:
                message += f'\n{ill[1]}'
            else:
                message += 'У вас нет горячки.'
            return message

        def zaraza_find(msg: list, message: str):
            try:
                letal_time = int(message.split('\n☣️')[0].split(
                    'Заражение на ')[1].split(' д')[0])
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
                    '\n☣️')[1].split('\n')[0]
            except Exception as e:
                print(e)
            return exp, time_to_stop, cd

        def find_many_users_id(message):
            if 'reply_message' in event.message_data:
                message = event.message_data['reply_message']['text']
            try:
                users_ids = re.findall(r'id\d+|https://vk.com\S+', message)
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
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.from_me:
                            if self.user_id == 532458503:
                                if event.message.lower().split()[0] == '+админ':
                                    user_id = find_user_id(event.message)
                                    if user_id in self.all_users:
                                        insert_admin(user_id)
                                        self.admins.append(user_id)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'[id{user_id}|Пользователь] стал администратором в лп!',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'[id{user_id}|Пользователь] не использует лп!',
                                            message_id=event.message_data['id']
                                        )
                            if self.user_id in self.admins:
                                if event.message.lower().split()[0] == 'юзеры':
                                    users = 'Список юзеров:'
                                    for user in USERS:
                                        users += f'\n{user.name} | {user.is_alive()}'
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=users,
                                        message_id=event.message_data['id']
                                    )
                                if event.message.lower().split()[0] == '+юзер':
                                    if len(event.message.lower().split()) <= 3:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда: +юзер токен префикс имя',
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
                                                    message=f'Пользователь {name_user} подключен.',
                                                    message_id=event.message_data['id']
                                                )
                                        else:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'Не удалось подключить пользователя {name_user}.',
                                                message_id=event.message_data['id']
                                            )
                                if event.message.lower().split()[0] == '-юзер':
                                    if len(event.message.lower().split()) <= 1:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message='Команда: -юзер имя',
                                            message_id=event.message_data['id']
                                        )
                                    user = event.message.lower().split()[1]
                                    if user in user_names and user != 'Rostuk':
                                        delete_token(user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Юзер {user} удалён',
                                            message_id=event.message_data['id']
                                        )
                                        USERS.pop(user_names.index(user))
                                        user_names.remove(user)
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Не удалось удалить юзера {user}, либо он не был подключен.',
                                            message_id=event.message_data['id']
                                        )
                            if event.message.lower() == 'вак' \
                                    or event.message.lower().startswith('л вак'):
                                send_message(event.peer_id, '.купить вакцину')
                            if event.message.lower().split()[0] == 'дд':
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
                            if event.message.lower().startswith('+преф'):
                                pref = event.message.lower().split('+преф ')[1]
                                update_prefix(self.fk_repeat_id, pref)
                                self.prefix = pref
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Префикс успешно изменён на {pref}',
                                    message_id=event.message_data['id']
                                )
                            if event.message.lower().startswith('чек преф'):
                                repeat = 'включена' if self.set_repeat else 'выключена'
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Ваш префикс: {self.prefix}\nДовов: {len(self.dovs)}\n\
Статус повторялки: {repeat}',
                                    message_id=event.message_data['id']
                                )
                            if event.message.lower().startswith('зр')\
                                or event.message.lower().startswith('зз') \
                                    or event.message.lower().startswith('пвк'):
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
                                        message = f'Вот столько раз заражал [{user_id}|{user_name(user_id)}]:\n'
                                        count = 1
                                        kd = 0
                                        podverg = 'подверг' if self.sex == 2 else 'подвергла'
                                        for msg in vk.messages.search(q=f"id{self.user_id} {podverg} заражению {user_id}")['items']:
                                            if len(message.split('\n')) > 4:
                                                break
                                            if msg['text'].find('Отчёт об операции') != -1 and msg['from_id'] < 0:
                                                if msg['text'].find(f'[id{self.user_id}') < msg['text'].find(podverg):
                                                    exp, time_to_stop, cd = zaraza_find(
                                                        msg, msg['text'])
                                                    if cd[0]:
                                                        kd = cd[1]
                                                    message += f'{count}. {exp} до {time_to_stop}\n'
                                                    count += 1
                                            elif msg['text'].startswith(f'🦠 [id{self.user_id}') and msg['from_id'] < 0:
                                                exp, time_to_stop, cd = zaraza_find(
                                                    msg, msg['text'])
                                                if cd[0]:
                                                    kd = cd[1]
                                                message += f'{count}. {exp} до {time_to_stop}\n'
                                                count += 1
                                        if len(message.split('\n')) < 3:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'Не нашёл информации про заражения [{user_id}|{user_name(user_id)}].',
                                                message_id=event.message_data['id']
                                            )
                                        else:
                                            if kd:
                                                message += f"\n⚠⚠⚠ КД ещё {kd} ч. ⚠⚠⚠"
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
                                            message='На себе заразы не чекнешь',
                                            message_id=event.message_data['id']
                                        )
                                except:
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='Не удалось найти цель.',
                                        message_id=event.message_data['id']
                                    )

                            if len(event.message.split()) > 0 \
                                and event.message.lower().split()[0] == 'з' \
                                    or event.message.lower().split()[0] == 'еб':
                                try:
                                    if len(event.message.lower().split()) > 1:
                                        if event.message.lower().split()[1].isdigit():
                                            number = int(
                                                event.message.lower().split()[1])
                                            user_id = find_many_users_id(
                                                event.message)[number-1]
                                            send_message(
                                                event.peer_id, f'заразить @{user_id}')
                                        elif event.message.lower().split()[1] == 'всех':
                                            user_ids = set(find_many_users_id(
                                                event.message))
                                            send_message(
                                                event.peer_id, f'Запускаю заражение всех из списка!\nЗаражаю {len(user_ids)}')
                                            for user in user_ids:
                                                if user.startswith('https://vk.com/'):
                                                    user = user.split(
                                                        '/vk.com/')[1]
                                                send_message(
                                                    event.peer_id, f'заразить @{user}')
                                                time.sleep(10)
                                    else:
                                        user_id = f'id{find_user_id(event.message)}'
                                        send_message(
                                            event.peer_id, f'заразить @{user_id}')
                                except:
                                    send_message(
                                        event.peer_id, 'Не нашел кого жрать.')
                            if len(event.message.split()) > 0:
                                if event.message.lower().split()[0] == 'лаб' \
                                        or event.message.lower().split()[0] == 'л лаб':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=lab(),
                                        message_id=event.message_data['id']
                                    )
                                if event.message.lower().split()[0] == '+шаб':
                                    name_tmp = event.message.lower().split(
                                        '\n')[0].split('+шаб ')[1]
                                    content_tmp = event.message.split(
                                        f'{name_tmp}\n')[1]
                                    if name_tmp in self.templates:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Шаблон {name_tmp} уже существует!',
                                            message_id=event.message_data['id'])
                                    else:
                                        insert_template(
                                            name_tmp, content_tmp, self.user_id)
                                        self.templates.append(name_tmp)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Шаблон {name_tmp} добавлен!',
                                            message_id=event.message_data['id'])
                                elif event.message.lower().split()[0] == '-шаб':
                                    name_tmp = event.message.lower().split(
                                        '\n')[0].split('-шаб ')[1]
                                    if name_tmp in self.templates:
                                        delete_template(
                                            name_tmp, self.user_id)
                                        self.templates.remove(name_tmp)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Шаблон {name_tmp} удалён!',
                                            message_id=event.message_data['id'])
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'У вас нет шаблона {name_tmp}.',
                                            message_id=event.message_data['id'])
                                elif event.message.lower().split()[0] == 'шаб':
                                    name_tmp = event.message.lower().split('шаб ')[
                                        1]
                                    if name_tmp in self.templates:
                                        tmp = select_template(
                                            name_tmp, self.user_id)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=tmp,
                                            message_id=event.message_data['id'])
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Шаблон {name_tmp} не существует.',
                                            message_id=event.message_data['id'])
                                elif event.message.lower().split()[0] == 'шаблоны':
                                    text = 'Список ваших шаблонов:'
                                    for tmp in self.templates:
                                        text += f'\n{tmp}'
                                    if text == 'Список ваших шаблонов:':
                                        text = 'У вас нет сохранённых шаблонов.'
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=text,
                                        message_id=event.message_data['id']
                                    )
                                elif event.message.lower().split()[0] == '+повтор':
                                    self.set_repeat = True
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='Повторялка включена.',
                                        message_id=event.message_data['id']
                                    )
                                elif event.message.lower().split()[0] == '-повтор':
                                    self.set_repeat = False
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message='Повторялка выключена.',
                                        message_id=event.message_data['id']
                                    )
                                elif event.message.lower().split()[0] == '+дов':
                                    id_user = find_user(event.message)
                                    if insert_dov((id_user, self.fk_repeat_id)) is None and id_user not in self.dovs:
                                        if id_user == self.user_id:
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'Совсем ку-ку себя в довы добавлять?',
                                                message_id=event.message_data['id']
                                            )
                                        else:
                                            self.dovs.append(id_user)
                                            vk.messages.edit(
                                                peer_id=event.peer_id,
                                                message=f'Пользователь [id{id_user}|{user_name(id_user)}] добавлен в довы.',
                                                message_id=event.message_data['id']
                                            )
                                    elif id_user in self.dovs:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Пользователь [id{id_user}|{user_name(id_user)}] уже находится в довах.',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Не удалось добавить пользователя [id{id_user}|{user_name(id_user)}] в довы.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '-дов':
                                    id_user = find_user(event.message)
                                    if delete_dov((id_user, self.fk_repeat_id)) is None and id_user in self.dovs:
                                        self.dovs.remove(id_user)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Пользователь [id{id_user}|{user_name(id_user)}] удалён из довов.',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Не удалось удалить пользователя [id{id_user}|{user_name(id_user)}] из довов.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == 'довы':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=dov_list(
                                            select_dov(self.fk_repeat_id)),
                                        message_id=event.message_data['id']
                                    )
                                elif event.message.lower().split()[0] == '+запрет':
                                    name = event.message.lower().split(
                                        "+запрет ")[1]
                                    if name not in self.not_availables:
                                        insert_not_available(
                                            (name, self.fk_repeat_id))
                                        self.not_availables.append(name)
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда {name} добавлена в запрещённые для повтора.',
                                            message_id=event.message_data['id']
                                        )
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда {name} уже есть в запрещённых для повтора.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == '-запрет':
                                    name = event.message.lower().split(
                                        "-запрет ")[1]
                                    if name in self.not_availables:
                                        delete_not_available(
                                            (name, self.fk_repeat_id))
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команда {name} удалена из запрещённых для повтора.',
                                            message_id=event.message_data['id']
                                        )
                                        self.not_availables.remove(name)
                                    else:
                                        vk.messages.edit(
                                            peer_id=event.peer_id,
                                            message=f'Команды {name} не было в списке запрещённых для повтора.',
                                            message_id=event.message_data['id']
                                        )
                                elif event.message.lower().split()[0] == 'запретлист':
                                    vk.messages.edit(
                                        peer_id=event.peer_id,
                                        message=not_available_list(
                                            select_not_available(self.fk_repeat_id)),
                                        message_id=event.message_data['id']
                                    )
                        elif (event.from_user or event.from_chat) and event.user_id in self.dovs and self.set_repeat:
                            if len(event.message.split()) > 0 \
                                    and event.message.lower().split()[0] == self.prefix:
                                text = event.message
                                text = text[len(self.prefix)+1:]
                                if check_available(text.lower()):
                                    if 'reply_message' in event.message_data:
                                        send_message(peer_id=event.peer_id,
                                                     message=event.message[len(
                                                         self.prefix)+1:],
                                                     reply_to=event.message_data['reply_message']['id'])
                                    else:
                                        send_message(peer_id=event.peer_id,
                                                     message=event.message[len(self.prefix)+1:])
                                else:
                                    send_message(event.peer_id, 'Недоступно!')
            except:
                pass


me = Bot(acess_token='',  # тут вставлять токен
         prefix='',        # префикс для довов
         name='')
USERS = [me, ]
select_tokens()
for user in USERS:
    if not user.is_alive():
        user.start()
user_names = []
for users in USERS:
    user_names.append(users.name)
