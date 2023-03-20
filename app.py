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


@app.route("/single_record")
def single_record():
    if request.method == "POST":
        transac_num = request.form.get("id")
    else:
        transac_num = request.args.get("id")
    
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(f"SELECT * FROM TRANSACTIONS WHERE id={transac_num};")

    transactions = cursor.fetchall()
    if len(transactions) == 0:
        return render_template("single_record.html", fields=dict(id=-1))
    transaction = transactions[0]

    # return transaction
    return render_template("single_record.html", fields=transaction)

    

@app.route("/income", methods=["POST"])
def add_income():
    if request.method == "POST":
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT BEFORE_GPAY, AFTER_GPAY, BEFORE_CASH, AFTER_CASH FROM TRANSACTIONS WHERE ID=(SELECT MAX(ID) FROM TRANSACTIONS);")

        transaction = dict(cursor.fetchall()[0])

        account = request.form["account"]
        amount = int(request.form["amount"])
        datetime_str = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        description = request.form["description"]
        
        before_gpay = int(transaction["before_gpay"])
        after_gpay = int(transaction["after_gpay"]) 
        before_cash = int(transaction["before_cash"])
        after_cash = int(transaction["after_cash"])

        if account == "gpay":
            before_gpay = after_gpay
            after_gpay = after_gpay + amount
            after_cash = before_cash
        else:
            before_cash = after_cash
            after_cash = after_cash + amount
            after_gpay = before_gpay
        
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(f"INSERT INTO TRANSACTIONS(ACCOUNT, AMOUNT, TYPE, BEFORE_GPAY, AFTER_GPAY, BEFORE_CASH, AFTER_CASH, DATETIME, DESCRIPTION) " +
                       f"VALUES ( '{account}', {amount}, +1, {before_gpay}, {after_gpay}, {before_cash}, {after_cash}, '{datetime_str}', '{description}');")
        
        conn.commit()       
        cursor.close()
        conn.close()

        transaction_id = cursor.fetchall()[0]["id"]
        return render_template("transaction_record_success.html", transaction_id=transaction_id)
    else:
        return render_template("income.html")


@app.route("/expense", methods=["GET", "POST"])
def add_expense():

    if request.method == "POST":
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT BEFORE_GPAY, AFTER_GPAY, BEFORE_CASH, AFTER_CASH FROM TRANSACTIONS WHERE ID=(SELECT MAX(ID) FROM TRANSACTIONS);")

        transaction = dict(cursor.fetchall()[0])

        account = request.form["account"]
        amount = int(request.form["amount"])
        datetime_str = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        description = request.form["description"]
        
        before_gpay = int(transaction["before_gpay"])
        after_gpay = int(transaction["after_gpay"]) 
        before_cash = int(transaction["before_cash"])
        after_cash = int(transaction["after_cash"])

        if account == "gpay":
            before_gpay = after_gpay
            after_gpay = after_gpay - amount
            after_cash = before_cash
        else:
            before_cash = after_cash
            after_cash = after_cash - amount
            after_gpay = before_gpay
        
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(f"INSERT INTO TRANSACTIONS(ACCOUNT, AMOUNT, TYPE, BEFORE_GPAY, AFTER_GPAY, BEFORE_CASH, AFTER_CASH, DATETIME, DESCRIPTION) " +
                       f"VALUES ( '{account}', {amount}, -1, {before_gpay}, {after_gpay}, {before_cash}, {after_cash}, '{datetime_str}', '{description}') RETURNING id;")
        
        transaction_id = cursor.fetchall()[0]["id"]
        conn.commit()       
        cursor.close()
        conn.close()

        return render_template("transaction_record_success.html", transaction_id=transaction_id)
    else:
        return render_template("expense.html")


@app.route("/ping")
def hello_world():
    return "Ping successful!"


@app.route("/")
def show_transactions():
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM TRANSACTIONS ORDER BY ID DESC LIMIT 100;")
    transactions = [dict(transac) for transac in cursor.fetchall()]
    
    return render_template("index.html", records=transactions)

if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000, debug=False)