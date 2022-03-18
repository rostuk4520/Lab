import os
import vk_api
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread
import sqlite3
import datetime
import time
import re
import urllib.request
from vk_api.upload import VkUpload

sql = sqlite3.connect('templates.db')
cursor = sql.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS templates(
    template_lp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_link BLOB DEFAULT ( NULL ),
    template_text TEXT DEFAULT ( NULL ),
    vk_id INT NOT NULL,
    UNIQUE(template_name, vk_id)
)''')
sql.commit()
sql.close()


def sql(func):
    def wrapper(*args, **kwargs):
        global cursor, sql
        sql = sqlite3.connect('templates.db')
        cursor = sql.cursor()
        response = func(*args, **kwargs)
        sql.commit()
        sql.close()
        return response
    return wrapper


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
def all_template(user_id: int):
    names = []
    try:
        name = cursor.execute(
            "SELECT template_name FROM templates WHERE vk_id = (?)", (user_id,)).fetchall()
        for n in name:
            names.append(n[0])
    except:
        names = []
    return names


class Bot(Thread):
    def __init__(self, acess_token):
        super(Bot, self).__init__()
        self.token = acess_token

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session, preload_messages=True)
        vk = self.vk_session.get_api()
        self.user_id = vk.users.get()[0]['id']
        self.uploader = VkUpload(vk)
        self.templates = all_template(self.user_id)

        while True:
            time.sleep(0.1)
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.from_me:
                        if event.message.lower().split()[0] == 'шаб':
                            name_tmp = event.message.lower().split('шаб ')[1]
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
                                    message=f'У вас нет шаблона с названием {name_tmp}!',
                                    message_id=event.message_data['id']
                                    )
                        elif event.message.lower().split()[0] == '+шаб':
                            rez = event.message_data['attachments']
                            msg = event.message.lower()
                            name_tmp = msg.split('\n')[0].split('+шаб ')[1]
                            while name_tmp[-1] == ' ':
                                name_tmp = name_tmp[:-1]
                            if len(rez) > 0 and 'type' in rez[0] and rez[0]['type'] == 'photo':
                                photo = bytes(urllib.request.urlopen(
                                    rez[0]['photo']['sizes'][-5]['url']).read())
                            else:
                                photo = 'null'
                            if len(msg.split('\n')) > 1:
                                text = msg[msg.find(name_tmp)+len(name_tmp)+1:]
                            else:
                                text = 'null'
                            if name_tmp not in self.templates:
                                insert_template(
                                    name_tmp, text, self.user_id, photo)
                                self.templates.append(name_tmp)
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Шаблон {name_tmp} успешно сохранен!',
                                    message_id=event.message_data['id']
                                    )
                            else:
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Шаблон {name_tmp} уже есть в списке!',
                                    message_id=event.message_data['id']
                                    )
                        elif event.message.lower().split()[0] == 'шаблоны':
                            msg = 'Ваш список шаблонов:'
                            if len(self.templates) > 0:
                                for tmp in self.templates:
                                    msg += f'\n{tmp}'
                            else:
                                msg = 'Ваш список шаблонов пуст.'
                            vk.messages.edit(
                                peer_id=event.peer_id,
                                message=msg,
                                message_id=event.message_data['id']
                                )
                        elif event.message.lower().split()[0] == '-шаб':
                            name_tmp = event.message.lower().split('\n')[0].split('-шаб ')[1]
                            if name_tmp in self.templates:
                                delete_template(name_tmp, self.user_id)
                                self.templates.remove(name_tmp)
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'Шаблон {name_tmp} успешно удален!',
                                    message_id=event.message_data['id']
                                )
                            else:
                                vk.messages.edit(
                                    peer_id=event.peer_id,
                                    message=f'У вас не было шаблона {name_tmp}!',
                                    message_id=event.message_data['id']
                                )
            except:
                pass


me = Bot(acess_token='') # user token

USERS = [me, ]

for user in USERS:
    user.start()
