import numpy as np
import discord
import threading
import asyncio
import editdistance
import time

WIN_TIME = 180

import camera
import controller

class discordHost(discord.Client):
    def __init__(self, questioner):
        super().__init__()
        self.questioner = questioner
        self.answered = asyncio.Event()
        self.questioning = False
        self.running = False

        self.nova_channel = 842844768576471041
        self.ravagers_channel = 842844877301874709

    async def on_ready(self):
        print("questioner", self.questioner)
        print('Logged on as {0}!'.format(self.user))

        self.guild = self.guilds[0]
        self.nova = self.get_channel(self.nova_channel)
        self.ravagers = self.get_channel(self.ravagers_channel)

    async def send_both(self, message):
        await asyncio.gather(*[self.nova.send(message),self.ravagers.send(message)])

    async def send_questions(self):
        self.running = True
        introMessage = "Welcome to Nova Rover Authenticator v1.0. Standby to answer security questions."
        await self.send_both(introMessage)
        
        while True:
            qa = self.questioner.next_question()
            if bool(self.questioner.camera.scanned.value) or qa is None:
                self.running = False
                break
            await self.send_both("> Next question: " + qa[0])
            self.questioning = True
            await self.answered.wait()
            self.questioning = False
            self.answered.clear()

    async def on_message(self, message):
        if self.questioning and message.author != self.user:
            print('Message from {0.author}: {0.content}'.format(message))
            if (message.channel.id == self.nova_channel):
                dist = self.questioner.check_answer(message.content)
                if dist == -1:
                    await self.nova.send(str(message.author.mention) + " Question has already been answered!")
                elif dist == 0:
                    await self.nova.send(str(message.author.mention) + " Correct!")
                    await self.nova.send("> Rover password: " + self.questioner.get_password())
                    await self.nova.send("> Driving interface: http://novainterns.mynetgear.com/car_control")
                    await self.nova.send("> Camera interface: http://novainterns.mynetgear.com/camera_control")
                    await self.ravagers.send("Nova have gotten the answer!")
                    self.questioner.win(WIN_TIME)
                    time.sleep(WIN_TIME)
                    self.questioner.done()
                    self.questioning = True
                    self.answered.set()
                elif dist < 3:
                    await self.nova.send(str(message.author.mention) + " Close! (edit distance: " + str(dist) + ")")
                else:
                    await self.nova.send(str(message.author.mention) + " Keep trying! (edit distance: " + str(dist) + ")")
            elif (message.channel.id == self.ravagers_channel): 
                dist = self.questioner.check_answer(message.content)
                if dist == -1:
                    await self.ravagers.send(str(message.author.mention) + " Question has already been answered!")
                elif dist == 0:
                    await self.ravagers.send(str(message.author.mention) + " Correct!")
                    await self.ravagers.send("> Rover password: " + self.questioner.get_password())
                    await self.ravagers.send("> Driving interface: http://novainterns.mynetgear.com/car_control")
                    await self.ravagers.send("> Camera interface: http://novainterns.mynetgear.com/camera_control")
                    await self.nova.send("Ravagers have gotten the answer!")
                    self.questioner.win(WIN_TIME)
                    time.sleep(WIN_TIME)
                    self.questioner.done()
                    self.questioning = True
                    self.answered.set()
                elif dist < 3:
                    await self.ravagers.send(str(message.author.mention) + " Close! (edit distance: " + str(dist) + ")")
                else:
                    await self.ravagers.send(str(message.author.mention) + " Keep trying! (edit distance: " + str(dist) + ")")


class Threader(threading.Thread):
    def __init__(self, token, questioner):
        threading.Thread.__init__(self)
        self.token = token
        self.loop = asyncio.get_event_loop()
        self.questioner = questioner
        self.start()

    async def starter(self):
        self.discord_client = discordHost(self.questioner)
        await self.discord_client.start(self.token)

    async def question_sender(self):
        await self.discord_client.send_questions()

    def run(self):
        self.name = 'Discord.py'

        self.loop.create_task(self.starter())
        self.loop.run_forever()

    def send_questions(self):
        self.loop.create_task(self.question_sender())

class Questioner():
    def __init__(self, controller, camera, questions_loc = "questions.csv", n_rounds = 4, n_questions_per_round = 7) -> None:
        self.controller = controller
        self.camera = camera

        self.questioning = False
        self.camera.scanned.value = False
        self.questions = np.genfromtxt(questions_loc, delimiter=',', dtype=str)

        self.round = 0
        self.question = 0
        self.n_rounds = n_rounds
        self.n_questions_per_round = n_questions_per_round

        self.question_lock = threading.Lock()

        if (len(self.questions) < n_rounds * n_questions_per_round):
            raise ValueError("# questions " + str(len(self.questions)) + " less than desired " + str(n_rounds * n_questions_per_round))

        self.solved = False

    def run(self, token):
        self.th = Threader(token, self)

    def next_question(self):
        self.question_lock.acquire(True)
        if self.question >= self.n_questions_per_round or self.round >= self.n_rounds:
            return None
        qa = self.questions[self.round * self.n_questions_per_round + self.question]
        self.solved = False
        self.question_lock.release()
        return qa

    def check_answer(self, answer):
        self.question_lock.acquire(True)
        if self.solved:
            dist = -1
        else:
            qa = self.questions[self.round * self.n_questions_per_round + self.question]
            dist = editdistance.eval(qa[1].lower(), answer.lower())
            if dist == 0:
                self.solved = True
                self.question += 1
        self.question_lock.release()
        return dist

    def get_password(self):
        self.question_lock.acquire(True)
        qa = self.questions[self.round * self.n_questions_per_round + self.question]
        self.question_lock.release()
        return qa[2]

    def set_round(self, round):
        self.question_lock.acquire(True)
        self.camera.scanned.value = False
        if (round >= self.n_rounds or round < 0):
            self.question_lock.release()
            raise ValueError("round " + str(round) + " greater than max " + str(self.n_rounds - 1))
        self.question = 0
        self.round = round
        self.question_lock.release()
        self.camera.set_mode(camera.CameraMode.BLANK)
        self.controller.set_mode(controller.Mode.LOST)
        if not self.th.discord_client.running:
            self.th.send_questions()
        else:
            self.th.discord_client.answered.set()
            self.questioning = True

    def exit(self):
        self.th.join()

    def win(self, countdown):
        self.camera.set_mode(camera.CameraMode.NORMAL)
        self.camera.set_countdown(countdown)
        self.controller.set_mode(controller.Mode.COMPUTER_SC)
        self.camera.password = self.get_password()

    def done(self):
        if not bool(self.camera.scanned.value):
            self.camera.set_mode(camera.CameraMode.BLANK)
            self.controller.set_mode(controller.Mode.LOST)
            self.camera.password = self.camera.root_password

if __name__ == "__main__":
    c = controller.Controller()
    cam = camera.Camera()
    cam.run()
    cam.set_mode(camera.CameraMode.BLANK)
    q = Questioner(c, cam)
    q.run("ODQzNTA1MTA3MDE4MTg2NzUy.YKE1WQ.HR36xuZi_w8o3FSP6kjaK1oDqsc")

    time.sleep(10)
    q.start()

    q.exit()