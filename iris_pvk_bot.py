import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread
import datetime
import time


class Bot(Thread):
    def __init__(self, acess_token):
        super(Bot, self).__init__()
        self.token = acess_token

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        vk = self.vk_session.get_api()
        self.user_id = vk.users.get()[0]['id']

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

        while True:
            time.sleep(0.1)
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.from_me:
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
            except Exception as e:
                print(e)


me = Bot(acess_token='token')

USERS = [me, ]

for user in USERS:
    user.start()
