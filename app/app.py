# Импорт необходимых библиотек для граф приложения, взаимодействия с бд, email и нейросетью
import keras
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QApplication, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import sys
import hashlib
from validate_email import validate_email
from supabase import create_client
import smtplib
from email.message import EmailMessage
from random import choice
from string import ascii_letters, digits
import cv2
from face_detection import FaceDetection
import time

# Константы размера окна, и необходимых ключей
WINDOW_SIZE = (640, 480)
SUPABASE_URL = 'https://knrwaedsovpgiuxmftow.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtucndhZWRzb3ZwZ2l1eG1mdG93Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0NDMwMjEsImV4cCI6MjA2NDAxOTAyMX0.4If7Gnoxha7qG8QdUC_5q4kagQGJnTKOcYEvmBllXfI'
EMAIL = 'facedetectiontester@gmail.com'
APP_PASSWORD = 'hurm sozf leaf rcsl'

# Переменная для хранения логина текущего пользователя.
current_user = ''


# Функция хэширования пароля
def hash_password(pwd):
    return hashlib.sha224(pwd.encode()).hexdigest()


# Функция отправки сообщения на почту
def send_email_key(email):
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        # Подключение к серверу и вход в аккаунт почты
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)

        # Генерация ключа и создание текста письма.
        key = ''.join([choice(ascii_letters + digits) for _ in range(6)])
        msg_text = f'Код подтверждения:\n{key}\nЕсли вы его не запрашивали, то проигнорируйте сообщение!'

        # Отправка письма
        message = EmailMessage()
        message['From'] = EMAIL
        message['To'] = email
        message['Subject'] = 'Код подтверждения'
        message.set_content(msg_text)
        server.send_message(message)

        server.close()
    return key


# Функция удаления записи из БД
def delete(table, eq_column, eq_value):
    database = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        database.table(table)
        .delete()
        .eq(eq_column, eq_value)
        .execute()
    )


# Функция получения записи из БД
def select(table, eq_column, eq_value, *columns):
    database = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        database.table(table)
        .select(*columns)
        .eq(eq_column, eq_value)
        .execute()
    )
    return response.data


# Функция добавления записи из БД
def insert(table, data):
    database = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        database.table(table)
        .insert(data)
        .execute()
    )

# Функция изменения записи из БД
def update(table, data, eq_column, eq_value):
    database = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        database.table(table)
        .update(data)
        .eq(eq_column, eq_value)
        .execute()
    )


# Класс окна входа
class Login(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/login.ui', self)

        self.setFixedSize(640, 480)

        self.password_hide = True

        self.initUI()
        self.resetUI()

    # Функция сброса UI
    def resetUI(self):
        self.password_hide = True
        self.password.setEchoMode(QLineEdit.Password)

        self.login.setText('')
        self.password.setText('')

        self.error_login.hide()
        self.pwd_error.hide()
        self.enter_error.hide()

    # Функция обработки нажатия на кнопки
    def initUI(self):
        self.registration_button.clicked.connect(self.registration)
        self.style_password_button.clicked.connect(self.style_password)
        self.login_button.clicked.connect(self.login_user)
        self.forget_password.clicked.connect(self.update_password)

    # Функция перехода на экран восстановления пароля
    def update_password(self):
        self.close()
        self.resetUI()
        update_password.resetUI()
        update_password.show()

    # Функция обработки входа в систему
    def login_user(self):
        global current_user
        # Хэширование пароля и проверка наличия пользователя
        hashed_pwd = hash_password(self.password.text())
        db_data = select('admins', 'login', self.login.text(), 'password')
        similarity_pwd = hashed_pwd == db_data[0]['password'] if db_data else None

        # Обработка ошибок
        self.error_checking(db_data, similarity_pwd)

        # Открытие главного окна
        if db_data and similarity_pwd:
            self.close()
            current_user = self.login.text()
            main_window.set_current_user(current_user)
            main_window.show()
            self.resetUI()

    # Функция обработки ошибок
    def error_checking(self, db_data, similarity_pwd):
        if self.login.text():
            self.error_login.hide()
        else:
            self.error_login.show()

        if self.password.text():
            self.pwd_error.hide()
        else:
            self.pwd_error.show()

        if db_data and similarity_pwd:
            self.enter_error.hide()
        else:
            self.enter_error.show()

    # Функция видимости пароль
    def style_password(self):
        if self.password_hide:
            self.password_hide = False
            self.password.setEchoMode(QLineEdit.Normal)
        else:
            self.password_hide = True
            self.password.setEchoMode(QLineEdit.Password)

    # Функция открытия окна регистрации
    def registration(self):
        self.resetUI()
        self.close()
        registration.resetUI()
        registration.show()


# Класс окна Регистрации
class Registration(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/registration.ui', self)

        # Установка скрытого стиля паролей
        self.password_hide = True
        self.pwd_check_hide = True
        self.password.setEchoMode(QLineEdit.Password)
        self.check_pwd.setEchoMode(QLineEdit.Password)

        self.setFixedSize(*WINDOW_SIZE)

        self.user_data = {}

        self.initUI()

    # Функция сброса UI
    def resetUI(self):
        self.user_data = {}

        self.password_hide = True
        self.pwd_check_hide = True
        self.password.setEchoMode(QLineEdit.Password)
        self.check_pwd.setEchoMode(QLineEdit.Password)

        self.error_email.hide()
        self.error_login.hide()
        self.error_pwd.hide()
        self.error_check_pwd.hide()
        self.error_login_exist.hide()
        self.error_email_exist.hide()

        self.email.setText('')
        self.login.setText('')
        self.password.setText('')
        self.check_pwd.setText('')

    # Функция обработки нажатия на кнопки
    def initUI(self):
        self.registration_button.clicked.connect(self.registration)
        self.style_password_button.clicked.connect(self.style_password)
        self.style_pwd_check_button.clicked.connect(self.style_pwd_check)
        self.back_button.clicked.connect(self.back)

    # Функция возвращения на экран входа
    def back(self):
        self.resetUI()
        self.close()
        login.show()

    # Функции видимости паролей
    def style_password(self):
        if self.password_hide:
            self.password_hide = False
            self.password.setEchoMode(QLineEdit.Normal)
        else:
            self.password_hide = True
            self.password.setEchoMode(QLineEdit.Password)

    def style_pwd_check(self):
        if self.pwd_check_hide:
            self.pwd_check_hide = False
            self.check_pwd.setEchoMode(QLineEdit.Normal)
        else:
            self.pwd_check_hide = True
            self.check_pwd.setEchoMode(QLineEdit.Password)

    # Функция регистрации
    def registration(self):
        # Хэширование паролей
        hashed_password = hash_password(self.password.text())
        hashed_check_pwd = hash_password(self.check_pwd.text())
        similarity_pwd = hashed_check_pwd == hashed_password
        # Проверка корректности email и логина
        valid_email = validate_email(self.email.text(), verify=True)
        email_exist = select('admins', 'email', self.email.text(), 'email')
        login_exist = select('admins', 'login', self.login.text(), 'login')

        self.error_checking(similarity_pwd, valid_email, login_exist, email_exist)

        # Регистрация нового адмминистратора
        if not login_exist\
                and valid_email\
                and similarity_pwd\
                and not email_exist\
                and self.password.text():
            self.user_data = {'login': self.login.text(),
                              'email': self.email.text(),
                              'password': hashed_password}

            # Открытие окна с подтверджением пароля и передача пользовательский данных
            email_check.show()
            email_check.prepare(self.email.text(), 'registration', self.user_data)
            email_check.send()
            self.close()

    # Функция обработок ошибок
    def error_checking(self, similarity_pwd, valid_email, login_exist, email_exist):
        if self.email.text():
            self.error_email.hide()
        else:
            self.error_email.show()

        if self.login.text():
            self.error_login.hide()
        else:
            self.error_login.show()

        if self.password.text():
            self.error_pwd.hide()
        else:
            self.error_pwd.show()

        if similarity_pwd:
            self.error_check_pwd.hide()
        else:
            self.error_check_pwd.show()

        if (valid_email or not self.email.text()) and not email_exist:
            self.error_email_exist.hide()
        else:
            self.error_email_exist.show()

        if login_exist:
            self.error_login_exist.show()
        else:
            self.error_login_exist.hide()


# Класс окна проверки почты
class CheckEmail(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/check_email.ui', self)
        self.setFixedSize(*WINDOW_SIZE)

        self.key_error.hide()

        # Переменные ключа, почты получателя и данных о пользователе.
        self.key = ''
        self.email = ''
        self.task = ''
        self.user_data = {}

        self.loadUI()

    # Функция установки значений о пользователе
    def prepare(self, email, task, user_data):
        self.user_data = user_data
        self.email = email
        self.task = task

    # Функция обработки нажатий кнопок
    def loadUI(self):
        self.check_button.clicked.connect(self.check)
        self.send_button.clicked.connect(self.send)

    # Функция проверки корректного пароля подтверждения
    def check(self):
        if self.check_key.text() == self.key:
            self.key_error.hide()

            # Добавление или обновления данных о пользователе в зависимости от задачи
            if self.task == 'registration':
                insert('admins', self.user_data)
                self.close()
                login.show()
            elif self.task == 'update':
                update('admins', self.update_data, 'email', update_password.current_email)
                self.close()
                login.show()
        else:
            self.key_error.show()

    # Отправка кода подтверждения на почту
    def send(self):
        self.check_key.setText('')
        self.key = send_email_key(self.email)


# Класс окна для обновления пароля
class UpdatePassword(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/update_pwd.ui', self)
        self.setFixedSize(*WINDOW_SIZE)

        # Установка скрытой видимости пароля
        self.password_hide = True
        self.pwd_check_hide = True
        self.password.setEchoMode(QLineEdit.Password)
        self.check_pwd.setEchoMode(QLineEdit.Password)

        self.update_data = {}

        self.loadUI()

    # Функция сброса UI
    def resetUI(self):
        self.update_data = {}

        self.email.setText('')
        self.password.setText('')
        self.check_pwd.setText('')

        self.password_hide = True
        self.pwd_check_hide = True
        self.password.setEchoMode(QLineEdit.Password)
        self.check_pwd.setEchoMode(QLineEdit.Password)

        self.error_email.hide()
        self.error_pwd.hide()
        self.error_check_pwd.hide()
        self.error_email_exist.hide()

    # Функция для обработки нажатия на кнопки
    def loadUI(self):
        self.back_button.clicked.connect(self.back)
        self.style_password_button.clicked.connect(self.style_password)
        self.style_pwd_check_button.clicked.connect(self.style_pwd_check)
        self.update_button.clicked.connect(self.update_password)

    # Функция обновления пароля
    def update_password(self):
        # Хэширование пароля и проверка наличия email в бд
        hashed_password = hash_password(self.password.text())
        hashed_check_pwd = hash_password(self.check_pwd.text())
        similarity_pwd = hashed_check_pwd == hashed_password
        email_exist = select('admins', 'email', self.email.text(), 'email')

        # Обработка ошибок
        self.error_checking(similarity_pwd, email_exist)

        # Обновление пароля пользователя
        if self.password.text() and similarity_pwd and email_exist:
            self.update_data = {'email': self.email.text(),
                                'password': hashed_password}

            # Отправка кода подтверждения, открытия окна для его ввода и передача пользовательских данных.
            email_check.show()
            email_check.prepare(self.email.text(), 'update', self.update_data)
            email_check.send()
            self.close()

    # Функция обработки ошибок
    def error_checking(self, similarity_pwd, email_exist):
        if self.email.text():
            self.error_email.hide()
        else:
            self.error_email.show()

        if self.password.text():
            self.error_pwd.hide()
        else:
            self.error_pwd.show()

        if similarity_pwd:
            self.error_check_pwd.hide()
        else:
            self.error_check_pwd.show()

        if not self.email.text() or email_exist:
            self.error_email_exist.hide()
        else:
            self.error_email_exist.show()

    # Функция возвращения на экран входа
    def back(self):
        self.close()
        self.resetUI()
        login.show()

    # Функции отображения видимости паролей
    def style_password(self):
        if self.password_hide:
            self.password_hide = False
            self.password.setEchoMode(QLineEdit.Normal)
        else:
            self.password_hide = True
            self.password.setEchoMode(QLineEdit.Password)

    def style_pwd_check(self):
        if self.pwd_check_hide:
            self.pwd_check_hide = False
            self.check_pwd.setEchoMode(QLineEdit.Normal)
        else:
            self.pwd_check_hide = True
            self.check_pwd.setEchoMode(QLineEdit.Password)


# Класс главного окна
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/main_window.ui', self)
        self.setFixedSize(*WINDOW_SIZE)

        self.resetUI()
        self.initUI()

    # Функция сброса UI
    def resetUI(self):
        self.CurrentUser_label.setText('')
        self.camera_error.hide()

    # Установка логина текущего пользователя в label
    def set_current_user(self, current_user):
        self.CurrentUser_label.setText(current_user)

    # Функция обработки нажатия кнопок
    def initUI(self):
        self.exit_button.clicked.connect(self.exit)
        self.start_button.clicked.connect(self.start_FaceDetection)
        self.add_button.clicked.connect(self.add_participant)
        self.view_button.clicked.connect(self.view_participant)

    # Функция отображения окна для просмотра участников.
    def view_participant(self):
        self.close()
        self.camera_error.hide()
        participant.set_searchUI()
        participant.show()

    # Функция отображения окна для добавления участников.
    def add_participant(self):
        self.close()
        self.camera_error.hide()
        participant.show()
        participant.set_addUI()

    # Функция открытия окна распознавателя лиц.
    def start_FaceDetection(self):
        # Проверка наличия веб-камеры у устройства
        if cv2.VideoCapture(0).isOpened():
            self.close()
            facedetection_window.show()
            facedetection_window.start_timer()
            self.camera_error.hide()
        else:
            self.camera_error.show()

    # Функция выхода из админ панели
    def exit(self):
        self.close()
        self.resetUI()
        login.show()


# Класс окна участников
class Participant(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/participant.ui', self)
        self.setFixedSize(*WINDOW_SIZE)

        self.image = b''
        self.initUI()

    # Установка UI для добавления новых участников.
    def set_addUI(self):
        self.search_list.hide()
        self.search_button.hide()
        self.search_error.hide()
        self.change_button.hide()
        self.delete_button.hide()
        self.save_button.hide()

        self.name_error.hide()
        self.surname_error.hide()
        self.spec_key_error.hide()
        self.spec_key_exist.hide()
        self.image_error.hide()
        self.image_label.hide()

        self.name.setText('')
        self.surname.setText('')
        self.spec_key.setText('')
        self.add_image_button.setText('👤')
        self.add_image_button.setIcon(QIcon())
        self.complete_label.setText('')
        self.image = b''

        self.add_button.show()
        self.name_label.show()
        self.surname_label.show()
        self.spec_key_label.show()

        self.name.show()
        self.name.setEnabled(True)
        self.surname.show()
        self.surname.setEnabled(True)
        self.spec_key.show()
        self.spec_key.setEnabled(True)
        self.add_image_button.show()

    # Функция установки UI поиска участников
    def set_searchUI(self):
        # Заполнение выпадающего списка участниками соответсвующего администратора
        self.search_list.clear()
        list_participants = select('participants', 'admin', current_user,
                                   'surname', 'name', 'spec_key')
        self.search_list.addItems([f'{participant["surname"]} {participant["name"]} ({participant["spec_key"]})'
                                   for participant in list_participants])

        # Установка видимости элементов
        self.search_list.show()
        self.search_button.show()

        self.search_error.hide()
        self.change_button.hide()
        self.delete_button.hide()

        self.name_error.hide()
        self.surname_error.hide()
        self.spec_key_error.hide()
        self.spec_key_exist.hide()
        self.image_error.hide()

        self.name.hide()
        self.surname.hide()
        self.spec_key.hide()
        self.add_image_button.hide()
        self.add_image_button.setIcon(QIcon())
        self.complete_label.hide()
        self.add_button.hide()
        self.save_button.hide()

        self.name_label.hide()
        self.surname_label.hide()
        self.spec_key_label.hide()
        self.image_label.hide()

    # Функция обработки нажатия на кнопки
    def initUI(self):
        self.back_button.clicked.connect(self.back)
        self.add_image_button.clicked.connect(self.add_image)
        self.add_button.clicked.connect(self.add_participant)
        self.search_button.clicked.connect(self.view_participant)
        self.delete_button.clicked.connect(self.delete_participant)
        self.change_button.clicked.connect(self.change_participant)
        self.save_button.clicked.connect(self.save_changes)

    # Функция сохранения изменений информации об участнике
    def save_changes(self):
        # Обработка ошибок
        self.error_checking(False)

        # Сохранение измений об участнике
        if self.name.text() \
                and self.surname.text() \
                and self.spec_key.text() \
                and self.image:
            # Обновление данных
            participant_data = {'admin': current_user,
                                'name': self.name.text(),
                                'surname': self.surname.text(),
                                'spec_key': self.spec_key.text(),
                                'image_path': f'{self.spec_key.text()}.jpg'}
            update('participants', participant_data, 'spec_key', self.spec_key.text())
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            supabase.storage.from_('images').update(file=self.image,
                                                    path=f'{self.spec_key.text()}.jpg',
                                                    file_options={'upsert': 'false', 'content-type': 'image/jpeg'})
            self.set_searchUI()
            self.complete_label.setText('Участник изменен')
            self.complete_label.show()

    # Функция отображения UI для изменения участников
    def change_participant(self):
        self.search_list.hide()
        self.search_button.hide()
        self.image_label.hide()
        self.change_button.hide()
        self.delete_button.hide()

        self.name.setEnabled(True)
        self.surname.setEnabled(True)

        self.add_image_button.setText('')
        self.add_image_button.setIcon(QIcon(self.pixmap))
        self.add_image_button.setIconSize(self.add_image_button.size())
        self.add_image_button.show()

        self.save_button.show()

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.image = supabase.storage.from_('images').download(f'{self.spec_key.text()}.jpg')

    # Функция удаления участника
    def delete_participant(self):
        delete('participants', 'spec_key', self.spec_key.text())

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.storage.from_('images').remove(f'{self.spec_key.text()}.jpg')

        self.set_searchUI()
        self.complete_label.setText('Участник удален')
        self.complete_label.show()

    # Функция просмотра выбранного при поиске участника
    def view_participant(self):
        # Получение информации о выбранном участнике
        participant_key = self.search_list.currentText().split()[-1][1:-1]
        selected_participant = select('participants', 'spec_key', participant_key, '*')[0]
        if selected_participant:
            # Отображение информации
            self.complete_label.setText('')
            self.name_label.show()
            self.surname_label.show()
            self.spec_key_label.show()

            self.name.show()
            self.name.setText(selected_participant['name'])
            self.name.setEnabled(False)
            self.surname.show()
            self.surname.setText(selected_participant['surname'])
            self.surname.setEnabled(False)
            self.spec_key.show()
            self.spec_key.setText(selected_participant['spec_key'])
            self.spec_key.setEnabled(False)

            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            image = supabase.storage.from_('images').download(f'{self.spec_key.text()}.jpg')
            image = QImage.fromData(image)
            self.pixmap = QPixmap.fromImage(image)

            self.image_label.setPixmap(self.pixmap.scaled(171, 181))
            self.image_label.show()

            self.change_button.show()
            self.delete_button.show()
        else:
            self.search_error.show()

    # Функция добавления изображения
    def add_image(self):
        # Открытие диалогового окна для просмотра файлов
        dialog = QFileDialog(self)
        dialog.setDirectory('C:/images/')
        # Установка загрузки файлов из системы и установка допустимых расширений
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Images (*.png *.jpg *jpeg)")
        dialog.setViewMode(QFileDialog.ViewMode.List)

        # Загрузка, чтение и отображение выбранного изображение
        if dialog.exec():
            filename = dialog.selectedFiles()
            if filename:
                self.add_image_button.setText('')
                self.add_image_button.setIcon(QIcon(*filename))
                self.add_image_button.setIconSize(self.add_image_button.size())
                self.image = open(*filename, 'rb')

    # Функция добавления нового участника
    def add_participant(self):
        # Обработка ошибок и проверка наличия в системе спец логина
        spec_key_exist = select('participants', 'spec_key', self.spec_key.text(), 'spec_key')
        self.error_checking(spec_key_exist)

        if self.name.text()\
                and self.surname.text()\
                and self.spec_key.text()\
                and self.image\
                and not spec_key_exist:
            try:
                # Добавление участника в базу данных при корректных данных
                participant_data = {'admin': current_user,
                                    'name': self.name.text(),
                                    'surname': self.surname.text(),
                                    'spec_key': self.spec_key.text(),
                                    'image_path': f'{self.spec_key.text()}.jpg'}
                insert('participants', participant_data)

                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                supabase.storage.from_('images').upload(file=self.image,
                                                        path=f'{self.spec_key.text()}.jpg',
                                                        file_options={'upsert': 'false', 'content-type': 'image/jpeg'})
                self.set_addUI()
                self.complete_label.setText('Участник добавлен')
            except:
                self.spec_key_error.show()
        else:
            self.complete_label.setText('')

    # Функция обработки ошибок
    def error_checking(self, spec_key_exist):
        if self.name.text():
            self.name_error.hide()
        else:
            self.name_error.show()

        if self.surname.text():
            self.surname_error.hide()
        else:
            self.surname_error.show()

        if self.spec_key.text():
            self.spec_key_error.hide()
        else:
            self.spec_key_error.show()

        if not spec_key_exist:
            self.spec_key_exist.hide()
        else:
            self.spec_key_exist.show()

        if self.image:
            self.image_error.hide()
        else:
            self.image_error.show()

    # Функция возвращения на главный экран
    def back(self):
        self.close()
        main_window.show()


# Класс окна для распознавания лиц
class FaceDetectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/detection_window.ui', self)
        self.setFixedSize(*WINDOW_SIZE)

        # Получение доступа к веб-камере
        self.cap = cv2.VideoCapture(0)

        # Установка таймера для частоты кадров
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Создание объекта класса для реализации второго потока нахождения сходств лиц
        self.face_comparison = FaceComparison()
        self.face_comparison.finished.connect(self.stop_thread)
        self.thread_working = False

    # Запуск таймера
    def start_timer(self):
        self.timer.start(30)

    # Функция обновления кадра
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Перевод изображения в цветовую палитру rgb, а также перевод изображения в тензор
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = face_detection.img2array(frame)

            # Классификация наличия лица
            model_predict = model_classification.predict(image)[0][0]
            if model_predict < 0.5:
                # При наличии лица локализация его и получение изображения с ограничевающей рамкой около лица
                image = face_detection(frame)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                height, width, channels = image.shape

                # Запуск второго потока для нахождения сходств лица с лицами в бд
                if not self.thread_working:
                    self.face_comparison.set_image(frame)
                    self.start_thread()
            else:
                image = (image.numpy() * 255).astype(np.uint8)
                height, width, channels = image.shape[1:]

            # Перевод тензора в формат изображения и отображение его
            bytes_per_line = channels * width
            image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(*WINDOW_SIZE)
            self.video_view.setPixmap(pixmap)

    # Старт второго потока
    def start_thread(self):
        self.thread_working = True
        self.face_comparison.start()

    # Функция выполняющаяся после получения сигнала о завершении работы второго потока.
    def stop_thread(self):
        self.thread_working = False


# Класс второго потока
class FaceComparison(QThread):
    def __init__(self):
        super().__init__()
        finished = pyqtSignal()

        self.image = np.ndarray([])

    # Установка изображения
    def set_image(self, image):
        self.image = image

    # Функция запуска второго потока
    def run(self):
        # Получение изображения локализованного лица
        crop_image = self.croped_image()

        # Проверка сходств локализованного лица с лицами в бд
        images_path = select('participants', 'admin', current_user, 'image_path')
        for path in images_path:
            # Получение изображения из бд и перевод в тензор
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            image = supabase.storage.from_('images').download(path['image_path'])
            image_array = np.frombuffer(image, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = cv2.resize(image, (224, 224))

            # Сравнение лиц на основе основного изображения и шаблона
            res = cv2.matchTemplate(image, crop_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            # Разрешение доступа в случая превышения коэффициента сходства установленного порога
            if max_val >= .55:
                facedetection_window.success.setText('ДОСТУП РАЗРЕШЕН')
                time.sleep(3)
                facedetection_window.success.setText('')
                break

    # Функция вырезания из изображения локализованного лица
    def croped_image(self):
        # Получение размеров рамки лица
        array = face_detection.img2array(self.image)
        cam = face_detection.compute_cam(array)
        x, y, w, h = face_detection.get_bbox_from_cam(cam)

        # Вырезание области лица
        image = cv2.resize(self.image, (224, 224))
        crop_image = image[y:y + h, x:x + w]
        crop_image = cv2.resize(crop_image, (150, 180))
        crop_image = cv2.cvtColor(crop_image, cv2.COLOR_BGR2GRAY)

        return crop_image


# Запуск приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Загрузка моделей нейросетей и создание объекта класса для распознавания лиц.
    model_classification = keras.models.load_model('models/model_classification.keras')
    model_localization = keras.models.load_model('models/model_localization.keras')
    face_detection = FaceDetection(model_localization)

    # Создание объектов класса окон приложения
    registration = Registration()
    email_check = CheckEmail()
    update_password = UpdatePassword()
    main_window = MainWindow()
    login = Login()
    participant = Participant()
    facedetection_window = FaceDetectionWindow()

    # Отображение окна входа как стартового
    login.show()

    # Завершение работы программы
    sys.exit(app.exec())

