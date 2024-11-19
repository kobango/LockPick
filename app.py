from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
#import SQLAlchemy
from sqlalchemy import inspect
import os

app = Flask(__name__, template_folder='templates')

# Konfiguracja połączenia z bazą danych (tu: SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(basedir, 'chinook.db')
if os.path.exists(file_path):
    print(f"Database file exists: {file_path}")
else:
    print(f"Database file does not exist: {file_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'chinook.db')}"
print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
# Podaj tutaj ścieżkę do swojej bazy danych
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Funkcja do pobrania listy tabel i kolumn
def get_tables_and_columns():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        tables = {}
        for table_name in table_names:
            columns = inspector.get_columns(table_name)
            print(f"Columns in {table_name}: {columns}")
            tables[table_name] = [column['name'] for column in columns]

        return tables


# Strona główna z listą tabel
@app.route('/')
def index():
    try:
        with db.engine.connect() as connection:
            print("Database connected successfully!")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
    tables = get_tables_and_columns()
    return render_template('index.html', tables=tables)


# Strona wyświetlająca dane z wybranej tabeli
@app.route('/table/<table_name>')
def table_view(table_name):
    tables = get_tables_and_columns()  # Lista tabel i kolumn
    if table_name not in tables:
        return f"Table {table_name} does not exist.", 404

    # Pobranie danych z tabeli jako lista słowników
    data = db.session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
    column_names = tables[table_name]
    return render_template('table.html', table_name=table_name, columns=column_names, data=data)


if __name__ == '__main__':
    app.run(debug=True)