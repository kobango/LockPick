from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
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

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{file_path}"
print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
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

# Strona wyświetlająca dane z wybranej tabeli z paginacją
@app.route('/table/<table_name>')
def table_view(table_name):
    tables = get_tables_and_columns()  # Lista tabel i kolumn
    if table_name not in tables:
        return f"Table {table_name} does not exist.", 404

    # Parametry paginacji
    page = request.args.get('page', 1, type=int)
    per_page = 100  # Liczba rekordów na stronę
    offset = (page - 1) * per_page

    # Pobranie danych z tabeli z paginacją i uwzględnieniem rowid
    data = db.session.execute(
        text(f"SELECT rowid, * FROM {table_name} LIMIT :limit OFFSET :offset"),
        {'limit': per_page, 'offset': offset}
    ).fetchall()

    column_names = ['rowid'] + tables[table_name]
    total_records = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    total_pages = (total_records + per_page - 1) // per_page

    return render_template(
        'table.html',
        table_name=table_name,
        columns=column_names,
        data=data,
        page=page,
        total_pages=total_pages
    )

# Strona edycji wiersza
@app.route('/table/<table_name>/edit/<int:row_id>', methods=['GET', 'POST'])
def edit_row(table_name, row_id):
    tables = get_tables_and_columns()
    if table_name not in tables:
        return f"Table {table_name} does not exist.", 404

    column_names = tables[table_name]
    if request.method == 'POST':
        # Pobranie danych z formularza
        updated_data = {col: request.form[col] for col in column_names}
        # Budowanie zapytania SQL
        set_clause = ", ".join([f"{col} = :{col}" for col in column_names])
        query = text(f"UPDATE {table_name} SET {set_clause} WHERE rowid = :row_id")
        db.session.execute(query, {**updated_data, 'row_id': row_id})
        db.session.commit()
        return redirect(url_for('table_view', table_name=table_name))

    # Pobranie danych wiersza
    row_data = db.session.execute(
        text(f"SELECT rowid, * FROM {table_name} WHERE rowid = :row_id"),
        {'row_id': row_id}
    ).fetchone()

    return render_template('edit_row.html', table_name=table_name, columns=column_names, row=row_data)


if __name__ == '__main__':
    app.run(debug=True)
