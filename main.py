import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
from ttkthemes import ThemedTk
from tkinter import filedialog

class DatabaseApp:
    def __init__(self, master, connection_params):
        self.master = master
        self.connection_params = connection_params
        self.master.title("АРМ Курьерской службы")

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both')

        try:
            self.conn = sqlite3.connect(**connection_params)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as err:
            print(f"Error: {err}")
            messagebox.showerror("Ошибка базы данных", "Не удалось подключиться к базе данных.")
            return

        self.table_names = self.get_table_names()
        if not self.table_names:
            print("Нет таблиц в базе данных!")
            messagebox.showwarning("Внимание", "В базе данных нет таблиц. Пожалуйста, создайте таблицы.")
            return

        print("Таблицы: ", self.table_names)
        for table_name in self.table_names:
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=table_name)
            self.create_table_view(frame, table_name)

    def get_table_names(self):
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [row[0] for row in self.cursor.fetchall()]
            return table_names
        except sqlite3.Error as err:
            print(f"Ошибка при получении таблиц: {err}")
            return []

    def create_table_view(self, frame, table_name):
        print(f"Загружаем таблицу: {table_name}")
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in self.cursor.fetchall()]
        except sqlite3.Error as err:
            print(f"Ошибка при загрузке данных таблицы {table_name}: {err}")
            return

        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        tree.pack(expand=True, fill='both')

        for col in columns:
            tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(tree, table_name, c, False))
            tree.column(col, width=100, anchor='center')

        self.populate_treeview(tree, table_name)

        add_button = tk.Button(frame, text="Добавить", command=lambda: self.add_row(tree, table_name))
        add_button.pack(side=tk.LEFT, padx=10)

        delete_button = tk.Button(frame, text="Удалить", command=lambda: self.delete_row(tree, table_name))
        delete_button.pack(side=tk.LEFT, padx=10)

        edit_button = tk.Button(frame, text="Изменить", command=lambda: self.edit_row(tree, table_name))
        edit_button.pack(side=tk.LEFT, padx=10)

        refresh_button = tk.Button(frame, text="Обновить", command=lambda: self.populate_treeview(tree, table_name))
        refresh_button.pack(side=tk.LEFT, padx=10)

        search_entry = tk.Entry(frame)
        search_entry.pack(side=tk.LEFT, padx=10)

        search_button = tk.Button(frame, text="Поиск", command=lambda: self.search_treeview(tree, search_entry.get()))
        search_button.pack(side=tk.LEFT, padx=10)

        generate_receipt_button = tk.Button(frame, text="Напечатать чек", command=lambda: self.generate_receipt(tree))
        generate_receipt_button.pack(side=tk.LEFT, padx=10)

    def populate_treeview(self, tree, table_name):
        print(f"Загружаем данные из таблицы: {table_name}")
        try:
            self.cursor.execute(f"SELECT * FROM {table_name};")
            data = self.cursor.fetchall()
        except sqlite3.Error as err:
            print(f"Ошибка при загрузке данных таблицы {table_name}: {err}")
            return

        tree.delete(*tree.get_children())

        for row in data:
            tree.insert('', 'end', values=row)

    def add_row(self, tree, table_name):
        from datetime import datetime
        add_dialog = tk.Toplevel(self.master)
        add_dialog.title("Добавить строку")

        # Получаем названия столбцов
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        entry_widgets = []
        for col in columns:
            label = tk.Label(add_dialog, text=col)
            label.grid(row=columns.index(col), column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(add_dialog)
            entry.grid(row=columns.index(col), column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(entry)

        def validate_and_insert():
            values = [entry.get() for entry in entry_widgets]
            errors = []

            # Проверка поля "Адрес"
            if "Адрес" in columns:
                index = columns.index("Адрес")
                if not values[index].strip():  # Проверка, что поле "Адрес" не пустое
                    errors.append("Поле 'Адрес' не может быть пустым.")

            # Проверяем поле даты и времени
            if "Дата_и_время_заказа" in columns:
                index = columns.index("Дата_и_время_заказа")
                try:
                    datetime.strptime(values[index], "%Y-%m-%d %H:%M")
                except ValueError:
                    errors.append(f"Неверный формат даты и времени. Используйте ГГГГ-ММ-ДД ЧЧ:ММ.")

            # Если есть ошибки, показываем их
            if errors:
                messagebox.showerror("Ошибка ввода", "\n".join(errors))
                return

            # Добавление в таблицу
            placeholders = ', '.join(['?' for _ in values])
            query = f"INSERT INTO {table_name} VALUES ({placeholders});"
            try:
                self.cursor.execute(query, values)
                self.conn.commit()
                self.populate_treeview(tree, table_name)
                add_dialog.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Не удалось добавить запись: {e}")

        # Кнопка подтверждения
        submit_button = tk.Button(add_dialog, text="Подтвердить", command=validate_and_insert)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def delete_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для удаления.")
            return

        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту строку?")
        if not confirm:
            return

        values = tree.item(selected_item)['values']
        primary_key_column = tree['columns'][0]  # Предположим, что первая колонка - это PRIMARY KEY

        query = f"DELETE FROM {table_name} WHERE {primary_key_column} = ?;"
        try:
            self.cursor.execute(query, (values[0],))  # Значение первой колонки как ключ
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            messagebox.showinfo("Удаление", "Запись успешно удалена.")
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении записи: {e}")

    def edit_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для изменения.")
            return

        values = tree.item(selected_item)['values']
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        edit_dialog = tk.Toplevel(self.master)
        edit_dialog.title("Изменить строку")

        entry_widgets = []
        for col, value in zip(columns, values):
            label = tk.Label(edit_dialog, text=col)
            label.grid(row=columns.index(col), column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(edit_dialog)
            entry.insert(0, value)
            entry.grid(row=columns.index(col), column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(entry)

        def validate_and_update():
            new_values = [entry.get() for entry in entry_widgets]
            if table_name == "Заказ":  # Проверяем только таблицу "Заказ"
                errors = []
                foreign_keys = {
                    "КлиентID": "Клиент",
                    "КурьерID": "Курьер",
                    "АдресID": "Адрес",
                    "ТранспортID": "Транспорт"
                }
                for col, related_table in foreign_keys.items():
                    if col in columns:
                        try:
                            index = columns.index(col)
                            self.cursor.execute(f"SELECT COUNT(*) FROM {related_table} WHERE {col} = ?;",
                                                (new_values[index],))
                            if self.cursor.fetchone()[0] == 0:
                                errors.append(f"{col} ({new_values[index]}) не существует в таблице {related_table}.")
                        except sqlite3.Error as e:
                            errors.append(f"Ошибка при проверке {col}: {e}")

                if errors:
                    messagebox.showerror("Ошибка редактирования", "\n".join(errors))
                    return

            set_clause = ', '.join([f"{column} = ?" for column in columns])
            where_clause = ' AND '.join([f"{column} = ?" for column in columns])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};"
            try:
                self.cursor.execute(query, new_values + values)
                self.conn.commit()
                self.populate_treeview(tree, table_name)
                edit_dialog.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Не удалось изменить запись: {e}")

        submit_button = tk.Button(edit_dialog, text="Подтвердить", command=validate_and_update)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def sort_treeview(self, tree, table_name, column, reverse):
        query = f"SELECT * FROM {table_name} ORDER BY {column} {'DESC' if reverse else 'ASC'};"
        self.cursor.execute(query)
        data = self.cursor.fetchall()

        tree.delete(*tree.get_children())

        for row in data:
            tree.insert('', 'end', values=row)

        tree.heading(column, command=lambda: self.sort_treeview(tree, table_name, column, not reverse))

    def search_treeview(self, tree, search_term):
        for item in tree.get_children():
            values = tree.item(item)['values']

            if any(str(search_term).lower() in str(value).lower() for value in values):
                tree.selection_add(item)
            else:
                tree.selection_remove(item)

    def generate_receipt(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для генерации чека.")
            return

        values = tree.item(selected_item)['values']

        client_id = values[0]

        self.generate_receipt_function(client_id)

    def generate_receipt_function(self, order_id):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as receipt_file:
                # Получение информации о заказе
                self.cursor.execute('''
                    SELECT 
                        Заказ.ЗаказID, Клиент.Имя AS Клиент, Курьер.Имя AS Курьер, 
                        Адрес.Город, Адрес.Улица, Адрес.Дом, Адрес.Квартира, 
                        Транспорт.Номер_транспорта, Заказ.Дата_и_время_заказа, Заказ.Статус
                    FROM Заказ
                    JOIN Клиент ON Заказ.КлиентID = Клиент.КлиентID
                    JOIN Курьер ON Заказ.КурьерID = Курьер.КурьерID
                    JOIN Адрес ON Заказ.АдресID = Адрес.АдресID
                    JOIN Транспорт ON Заказ.ТранспортID = Транспорт.ТранспортID
                    WHERE Заказ.ЗаказID = ?;
                ''', (order_id,))
                order_data = self.cursor.fetchone()

                if not order_data:
                    messagebox.showwarning("Ошибка", "Заказ не найден.")
                    return

                # Записываем данные в файл
                receipt_file.write("Чек заказа\n")
                receipt_file.write("=====================\n\n")
                receipt_file.write(f"Номер заказа: {order_data[0]}\n")
                receipt_file.write(f"Клиент: {order_data[1]}\n")
                receipt_file.write(f"Курьер: {order_data[2]}\n")
                receipt_file.write(
                    f"Адрес: {order_data[3]}, {order_data[4]}, д. {order_data[5]}, кв. {order_data[6]}\n")
                receipt_file.write(f"Транспорт: {order_data[7]}\n")
                receipt_file.write(f"Дата и время заказа: {order_data[8]}\n")
                receipt_file.write(f"Статус: {order_data[9]}\n")
                receipt_file.write("=====================\n\n")

            messagebox.showinfo("Генерация чека", "Чек успешно создан.")
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при генерации чека: {e}")


if __name__ == "__main__":
    connection_params = {"database": "mydb.sqlite3"}
    try:
        root = ThemedTk(theme="kroc")
        app = DatabaseApp(root, connection_params)
        root.mainloop()

    except sqlite3.Error as err:
        print(f"Error: {err}")
