import sqlite3


class Book:

    def __init__(self, id_num=-1, title=""):
        self.id_num = id_num
        self.title = title
        self.connection = sqlite3.connect("mydatabase.db")
        self.cursor = self.connection.cursor()

    def load_book(self, id_num: int) -> None:
        self.cursor.execute(
            "SELECT * FROM books WHERE id = ?", (id_num,)
        )
        result = self.cursor.fetchone()

        if result is None:
            raise ValueError(f"Книга с id={id_num} не найдена")

        # распаковываем кортеж (id, title)
        self.id_num, self.title = result

    def insert_book_in_db(self):
        self.cursor.execute(
            "INSERT INTO books VALUES (?, ?)", (self.id_num, self.title)
        )
        self.connection.commit()

    def __del__(self) -> None:
        # гарантируем закрытие соединения - Нихрена не гарантирует
        print("Closed connection !!!")
        self.connection.close()


# p1 = Book(10, 'DESYAT')
# p1.insert_book_in_db()
# p1.load_book(7)
# print(p1.title)

con = sqlite3.connect('mydatabase.db')
cur = con.cursor()

cur.execute("SELECT * FROM books")
results = cur.fetchall()

print(results)

con.close()
