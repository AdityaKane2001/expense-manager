from flask import Flask, request, render_template
from flask_cors import CORS
import urllib.parse as up
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)

load_dotenv()

up.uses_netloc.append("postgres")

def connect_db():
    url = up.urlparse(os.environ["DB_URL"])

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn


@app.route("/income", methods=["POST"])
def add_income():
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("insert into transactions ")
    del conn

@app.route('/expense', methods=["POST"])
def add_expense():
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('select before_gpay, after_gpay, before_cash, after_cash from transactions where id=(select max(id) from transactions);')
    # cursor.execute('select * from transactions;')
    
    transactions = cursor.fetchall()
    
    
    # cursor.execute(f"INSERT INTO transactions  VALUES( '{account}', {amount}, '{transaction_type}', '{before_gpay}', '{after_gpay}', '{before_cash}', '{after_cash}', '{datetime}', '{description}');")
    return transactions
    # conn.commit()
    # cursor.close()
    # conn.close()
    # before
    return {"status": 200}


@app.route("/ping")
def hello_world():
    return "Ping successful!"


@app.route("/")
def show_transactions():
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('select * from transactions order by id desc;')
    transactions = [dict(transac) for transac in cursor.fetchall()]
    
    return render_template("transactions.html", records=transactions)

if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000, debug=False)