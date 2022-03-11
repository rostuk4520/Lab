#!/usr/bin/python
# -*- coding: utf-8 -*-
import vk_api
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread
import time
import random
import schedule
import datetime


class Bot(Thread):
    def __init__(self, acess_token, name, param):
        super(Bot, self).__init__()
        self.token = acess_token
        self.name = name
        self.param = param
        self.success = self.fail = self.count = 0
        self.repeat = 0

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        vk = self.vk_session.get_api()
        self.user_id = vk.users.get()[0]['id']

        def send_message(peer_id, message=None, keyboard=None, attachment=None,
                         forward=None):
            vk.messages.setActivity(
                user_id=str(self.user_id),
                type='typing',
                peer_id=peer_id)
            time.sleep(random.randint(1, 3))
            vk.messages.send(
                random_id=get_random_id(),
                message=message,
                peer_id=peer_id,
                keyboard=keyboard,
                attachment=attachment,
                forward=forward,
            )

        def starts():
            send_message(-174105461, '.лаб')
            time.sleep(5)
            response = vk.messages.getHistory(
                count=1,
                peer_id=-174105461,
                rev=0)['items'][0]['text'].split('\n')
            try:
                if len(response[4].split('патогенов:')) > 1:
                    patog = int(response[4].split(
                        'патогенов:')[1].split()[0])
                    time_to_new_patogen = int(
                        response[5].split('ур (')[1].split()[0])
                else:
                    patog = int(response[5].split(
                        'патогенов:')[1].split()[0])
                    time_to_new_patogen = int(
                        response[6].split('ур (')[1].split()[0])

            except IndexError:
                patog = -1
                time_to_new_patogen = -1
            return patog, int(time_to_new_patogen*60)

        def infection():
            send_message(-174105461, f'заразить {self.param}')
            self.count += 1
            return 0

        def inf_response():
            time.sleep(4)
            response = vk.messages.getHistory(
                count=1,
                peer_id=int(-174105461),
                rev=0)['items'][0]['text'].split('\n')
            if len(response[0].split('заражению патогеном')) > 1:
                self.success += 1
                return True
            else:
                self.fail += 1
                if len(response[0].split('У вас горячка')) > 1:
                    return False
                elif len(response[0].split('Пока не произведено')) > 1:
                    return False
                elif len(response[0].split(f'заразить {self.param}')) > 1:
                    time.sleep(2)
                    if self.repeat > 2:
                        self.repeat = 0
                        return True
                    else:
                        self.repeat += 1
                        self.fail -= 1
                        inf_response()
                elif len(response[0].split('Не удалось найти')) > 1:
                    nonlocal patogen
                    patogen += 1
                    self.fail -= 1
                    return True
                return True

        def zaraza(pat):
            for _ in range(pat):
                infection()
                if inf_response():
                    time.sleep(random.randint(10, 20))
                    continue
                else:
                    break
        patogen, time_to_new_patogen = starts()
        print(patogen, time_to_new_patogen)
        print(f'Thread | Name {self.name} started')

        def start_thread():
            patogen, time_to_new_patogen = starts()
            if patogen > 0 and time_to_new_patogen > 0:
                zaraza(patogen)
                return 0
            elif patogen == 0 and time_to_new_patogen > 0:
                return 0
            else:
                return 0

        def results():
            time_now = str(datetime.datetime.now()).split()[1]
            send_message(self.user_id, f'Текущее время: {time_now} \n\
 Cтатистика автозаражалки за день:\n\n\
 Всего команда заразить {self.param} была отправлена: {self.count} раз(а)\n\
 Удачных заражений: {self.success}\n\
 Неудачных заражений: {self.fail}')
            self.success = self.fail = self.count = 0

        schedule.every(
            time_to_new_patogen).to(time_to_new_patogen + random.randint(15, 40)).seconds.do(start_thread).tag(self.name)
        schedule.every().day.at("00:00:00").do(results)


User = Bot(
    acess_token='',
    name='',
    param=''  # =,-,р
)


USERS = [User, ]


for user in USERS:
    user.start()

while True:
    try:
        schedule.run_pending()
        time.sleep(0.1)

    except Exception as e:
        print(e)
