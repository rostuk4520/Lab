#!/usr/bin/python
# -*- coding: utf-8 -*-
import vk_api
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread
import time


class Bot(Thread):
    def __init__(self, acess_token, ):
        super(Bot, self).__init__()
        self.token = acess_token

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        vk = self.vk_session.get_api()

        def send_message(peer_id, message=None):
            vk.messages.send(
                random_id=get_random_id(),
                message=message,
                peer_id=peer_id,
            )

        while True:
            time.sleep(0.1)
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.from_me and event.from_chat:
                            if event.message.lower().startswith('команда'):
                                count_mens = count_womens = 0
                                users = vk.messages.getChat(chat_id=event.chat_id, fields='sex')['users']
                                for user in users:
                                    if user['type'] == 'profile':
                                        if user['sex'] == 2:
                                            count_mens += 1
                                        elif user['sex'] == 1:
                                            count_womens += 1
                                send_message(event.peer_id, f'Всего особей мужской стати в беседе: {count_mens}, \nженской: {count_womens},\nне определено стати(либо боты): {len(users)-count_mens-count_womens}.')
            except:
                pass


me = Bot(
    acess_token='',
)


USERS = [me, ]


for user in USERS:
    user.start()
