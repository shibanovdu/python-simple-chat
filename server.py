# SIMPLE TCP SERVER
import time
import asyncio                                  # импорт необходимой библиотеки
from asyncio import transports                  # импорт необходимых классов
from typing import Optional                     # импорт необходимых классов

codePage = "utf8"                               # штатная кодировка
#codePage = "WINDOWS-1251"                       # кодировка для винды

class ServerProtocol(asyncio.Protocol):         # наш класс протокола обмена наслудующий класс Protocol из asyncio
    login: str = None                           # логин пользователя
    server: 'Server'                            # класс объявляемый в коде ниже
    transport: transports.Transport             # класс импортированный из asyncio для побайтного обмена данными по протоколу TCP

    def __init__(self, server: 'Server'):       # конструктор для инициализации класса
        self.server = server

    def send_history(self):                                 # вывод последниех 10 элементов списка для нового клиента
        length = len(self.server.history)                   # размер списка
        if length > 0:
            self.transport.write("Последние 10 сообщений форума:\r\n".encode())  # отдаём сообщения клиенту
        for i in self.server.history[length-10:length]:     # цикл на последние 10 элементов списка
            self.transport.write(f"{i}\r\n".encode())       # отдаём сообщения клиенту

    def data_received(self, data: bytes):                                           # получение и обработка данных
        print(data)                                                                 # вывод полученных необработанных данных в консоль сервера
        decoded = data.decode(codePage)                                             # декодирование данных
        if decoded != "\r\n":                                                       # если полученная строка не пустая
            if self.login is not None:                                              # если пользователь залогинился
                self.send_message(decoded)                                          # отправка сообщения другим пользователям
                self.server.history.append(decoded)                                 # добавляем сообщение в список разосланных сообщений
            else:
                if decoded.startswith("login:"):                                    # если строка начинается со служебной строки значит пришел логин
                    self.login = decoded.replace("login:", "").replace("\r\n", "")  # чистим от служебных символов
                    for item in self.server.clientsLogins:                          # цикл перебора списка активных логинов
                        if item == self.login:                                      # если логин уже есть в списке
                            self.transport.write("Login busy! Try another one. You will be disconnected after 5 seconds.\r\n".encode())  # Уведомление пользователя о негодном гогине
                            time.sleep(5)                                           # пауза перед отключением
                            self.login = None                                       # обнуляем переменную с негодным логином
                            self.transport.close()                                  # Отключение клиента от сервера

                    if self.login is not None:                                      # Если логин годный (отсутствует в списке активных логинов)
                        self.server.clientsLogins.append(self.login)                # добавляем новый логин в список активных логинов
                        self.transport.write(f"Hi, {self.login}!\r\n".encode())     # отправляем приветствие
                        print(f"Авторизовался клиент: {self.login}")                # уведомление в консоль сервера
                        self.send_history()                                         # отправка последних 10 сообщений авторизовавшемуся пользователю

                else:
                    self.transport.write("Incorrect login.\r\n".encode())



    def connection_made(self, transport: transports.Transport):                                  # новое соединение с клиентом
        self.server.clients.append(self)                                                         # добавляем в список нового клиента
        self.transport = transport
        print ("Зашёл новый клиент.")                                                            # Уведомление в консоль сервера
        self.transport.write("Welcome to our server!\r\n".encode())                              # Приветствие подключившегося пользователя
        self.transport.write("Enter your login in the following form: login: ...\r\n".encode())  # Приветствие подключившегося пользователя

    def connection_lost(self, exc: Optional[Exception]):        # отключение клиента
        self.server.clients.remove(self)                        # удаление клиента из списка
        if self.login is not None:                              # если клиент логинился
            self.server.clientsLogins.remove(self)              # удаление логина клиента из списка
        print ("Клиент вышел.")                                 # уведомление в консоль сервера

    def send_message(self,content:str):                         # отправка сообщения всем клиентам
        message = f"{self.login}: {content}\r\n"                # формируем текст сообщения
        for user in self.server.clients:                        # цикл по списку клиентов
            user.transport.write(message.encode(codePage))      # рассылка


class Server:                                                   # класс сервера
    clients: list                                               # список клиентов
    clientsLogins: list                                         # список логинов клиентов
    history:list                                                # список сообщений

    def __init__(self):                                         # конструктор для инициализации класса
        self.clients =[]                                        # инициализация списка клиентов
        self.clientsLogins =[]                                  # инициализация списка логинов клиентов
        self.history =[]                                  # инициализация списка логинов клиентов

    def build_protocol(self):                                   # создание нашего протокол обмена
        return ServerProtocol(self)

    async def start(self):                                      # запуск сервера
        loop = asyncio.get_running_loop()                       # перехватываем текущий цикл опроса событий протокола обмена данными

        coroutine = await loop.create_server(                   # создаём свой сервер
            self.build_protocol,                                # наш протокол обмена
            '127.0.0.1',                                        # IP сервера
            8888                                                # порт сервера
        )

        print("Сервер запущен...")                              # Уведомление в консоль сервера

        await coroutine.serve_forever()                         # запуск сервера


process = Server()                                              # создаём экземпляр класса сервера для запуска

try:                                                            # обработка ручного прерывания сервера
    asyncio.run(process.start())
except KeyboardInterrupt:                                       # код ручной остановки сервера
    print("Сервер остановлен вручную")                          # Уведомление в консоль сервера о обработанной ошибке
