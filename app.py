from flask import Flask, jsonify, request
import urllib.parse as up
from dotenv import load_dotenv
import os
import psycopg2

app = Flask(__name__)

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

@app.route('/expense', methods=['GET'])
def add_expense():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute('select before_gpay, after_gpay, before_cash, after_cash from transactions where id=(select max(id) from transactions);')
    transactions = cursor.fetchall()
    # cursor.execute(f"INSERT INTO transactions  VALUES( '{account}', {amount}, '{transaction_type}', '{before_gpay}', '{after_gpay}', '{before_cash}', '{after_cash}', '{datetime}', '{description}');")
    return transactions
    # db.commit()
    # cursor.close()
    # db.close()
    # before
    return {"status": 200}


@app.route("/")
def hello_world():
    return "Hello world!"


if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000, debug=False)