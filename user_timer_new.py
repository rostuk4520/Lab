from threading import Thread
from time import sleep
import vk_api
import schedule
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType


class Bot(Thread):
    def __init__(self, acess_token, name):
        super(Bot, self).__init__()
        self.token = acess_token
        self.name = name

    def run(self):
        self.vk_session = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.vk = self.vk_session.get_api()

        def send_message(peer_id, message=None):
            self.vk.messages.send(
                random_id=get_random_id(),
                message=message,
                peer_id=peer_id
            )
        while True:
            sleep(0.5)
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW \
                            and event.from_me:
                        msg = event.message.lower()
                        if msg.startswith('+таймер'):
                            '''
                                +таймер время название
                                текст для повтора
                            '''
                            time_to_work = int(
                                msg.split('\n')[0].split('+таймер ')[1].split()[0])
                            tag = (
                                event.message.split('\n')[0].split('+таймер ')[1].split()[1])
                            text_msg = event.message.split(
                                f'{time_to_work} {tag}\n')[1]
                            print(text_msg, str(time_to_work), tag)
                            send_message(
                                event.peer_id, f'✅ Таймер {tag} создан.')
                            schedule.every(time_to_work).seconds.do(
                                send_message, peer_id=event.peer_id, message=text_msg).tag(self.name, tag)
                        if msg.startswith('-таймеры'):
                            '''
                                -таймеры
                            '''
                            send_message(
                                event.peer_id, '❌ Все таймеры удалены.')
                            schedule.clear()
                        elif msg.startswith('-таймер'):
                            '''
                                -таймер название
                            '''
                            tag = msg.split('-таймер ')[1]
                            schedule.clear(self.name, tag)
                            send_message(
                                event.peer_id, f'❌ Таймер {tag} удалён.')
                        if msg.startswith('таймеры'):
                            '''
                                таймеры
                            '''
                            all_jobs = schedule.get_jobs(self.name)
                            if len(all_jobs) > 0:
                                jobs = 'All your timers:'
                                all_jobs = str(all_jobs)[1:-1].split('), ')
                                for job in all_jobs:
                                    jobs += f'\n{all_jobs.index(job)+1}. {job}'
                            else:
                                jobs = "You have no timers."
                            send_message(event.peer_id, jobs)
            except Exception as e:
                print(e)


User = Bot(
    acess_token='',
    name=''
)

USERS = [User, ]
for user in USERS:
    user.start()
while True:
    try:
        sleep(0.1)
        schedule.run_pending()
    except Exception as e:
        print(e)
