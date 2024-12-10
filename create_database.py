import sqlite3

def add_test_courier():
    connection_params = {"database": "mydb.sqlite3"}
    connect = sqlite3.connect(connection_params["database"])
    cursor = connect.cursor()

    # Проверяем, есть ли транспорт
    cursor.execute("SELECT ТранспортID FROM Транспорт LIMIT 1;")
    transport = cursor.fetchone()

    if transport is None:
        print("Транспорт отсутствует. Добавьте хотя бы один транспорт.")
        return

    transport_id = transport[0]

    # Добавляем курьера
    courier_data = ("Иван Иванов", "+375291234567", transport_id)
    cursor.execute("INSERT INTO Курьер (Имя, Телефон, ТранспортID) VALUES (?, ?, ?);", courier_data)

    # Проверяем, что курьер добавился
    cursor.execute("SELECT * FROM Курьер;")
    all_couriers = cursor.fetchall()
    print("Данные в таблице 'Курьер':", all_couriers)

    connect.commit()
    print("Курьер добавлен успешно.")
    connect.close()


def create_tables():
    connection_params = {"database": "mydb.sqlite3"}
    try:
        connect = sqlite3.connect(connection_params["database"])
        cursor = connect.cursor()
        print("Подключение к базе данных успешно.")
    except sqlite3.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return

    try:
        # Удаление и пересоздание таблицы Курьер
        cursor.execute("DROP TABLE IF EXISTS Курьер;")
        print("Старая таблица 'Курьер' удалена.")

        # Создание таблицы Клиент
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Клиент (
                КлиентID INTEGER PRIMARY KEY,
                Имя TEXT
            )
        ''')
        print("Таблица 'Клиент' успешно создана или уже существует.")

        # Создание таблицы Курьер
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Курьер (
                КурьерID INTEGER PRIMARY KEY,
                Имя TEXT,
                Телефон TEXT,
                ТранспортID INTEGER,
                FOREIGN KEY (ТранспортID) REFERENCES Транспорт (ТранспортID) ON DELETE SET NULL
            )
        ''')
        print("Таблица 'Курьер' успешно создана или уже существует.")

        # Создание таблицы Транспорт
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Транспорт (
                ТранспортID INTEGER PRIMARY KEY,
                Тип TEXT,
                Номер_транспорта TEXT
            )
        ''')
        print("Таблица 'Транспорт' успешно создана или уже существует.")

        # Создание таблицы Адрес
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Адрес (
                АдресID INTEGER PRIMARY KEY,
                Город TEXT,
                Улица TEXT,
                Дом TEXT,
                Квартира TEXT
            )
        ''')
        print("Таблица 'Адрес' успешно создана или уже существует.")

        # Создание таблицы Заказ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Заказ (
                ЗаказID INTEGER PRIMARY KEY,
                КлиентID INTEGER,
                КурьерID INTEGER,
                АдресID INTEGER,
                ТранспортID INTEGER,
                Дата_и_время_заказа TEXT,
                Статус TEXT,
                FOREIGN KEY (КлиентID) REFERENCES Клиент (КлиентID) ON DELETE CASCADE,
                FOREIGN KEY (КурьерID) REFERENCES Курьер (КурьерID) ON DELETE CASCADE,
                FOREIGN KEY (АдресID) REFERENCES Адрес (АдресID) ON DELETE CASCADE,
                FOREIGN KEY (ТранспортID) REFERENCES Транспорт (ТранспортID) ON DELETE CASCADE
            )
        ''')
        print("Таблица 'Заказ' успешно создана или уже существует.")

        connect.commit()
        print("Все изменения успешно сохранены в базе данных.")
    except sqlite3.Error as e:
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        connect.close()
        print("Соединение с базой данных закрыто.")

create_tables()
