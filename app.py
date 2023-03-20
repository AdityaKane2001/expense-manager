from flask import Flask, request, render_template
from flask_cors import CORS
import urllib.parse as up
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras
from datetime import datetime


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
    cursor.execute("insert into transactions values")
    del conn

@app.route('/expense', methods=["GET", "POST"])
def add_expense():

    if request.method == "POST":
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('select before_gpay, after_gpay, before_cash, after_cash from transactions where id=(select max(id) from transactions);')

        transaction = dict(cursor.fetchall()[0])

        del cursor

        
        account = request.form["account"]
        amount = int(request.form["amount"])
        datetime_str = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        description = request.form["description"]
        
        before_gpay = int(transaction["before_gpay"])
        after_gpay = int(transaction["after_gpay"]) 
        before_cash = int(transaction["before_cash"])
        after_cash = int(transaction["after_cash"])

        if account == "gpay":
            after_gpay = before_gpay - amount
            after_cash = before_cash
        else:
            after_cash = before_cash - amount
            after_gpay = before_gpay
        
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(f"insert into transactions(account, amount, type, before_gpay, after_gpay, before_cash, after_cash, datetime, description) " +
                       f"values ( '{account}', {amount}, -1, {before_gpay}, {after_gpay}, {before_cash}, {after_cash}, '{datetime_str}', '{description}') returning id;")
        transaction_id = cursor.fetchall()[0]["id"]
        return render_template("transaction_record_success.html", transaction_id=transaction_id)
    else:
        return render_template("expense.html")
    
    


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