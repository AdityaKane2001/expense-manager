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


def update_single_transaction(id, cursor, transaction_data):
    account = transaction_data["account"]
    amount = int(transaction_data["amount"])
    datetime_str = transaction_data["datetime"]
    description = transaction_data["description"]
    
    before_gpay = int(transaction_data["before_gpay"])
    after_gpay = int(transaction_data["after_gpay"]) 
    before_cash = int(transaction_data["before_cash"])
    after_cash = int(transaction_data["after_cash"])
    transaction_type = int(transaction_data["type"])


    cursor.execute(f"UPDATE TRANSACTIONS SET ACCOUNT='{account}', " +
                           f"AMOUNT={amount}, TYPE={transaction_type}, BEFORE_GPAY={before_gpay}, " +
                           f"AFTER_GPAY={after_gpay}, BEFORE_CASH={before_cash}, AFTER_CASH={after_cash}, " +
                           f"DATETIME='{datetime_str}', DESCRIPTION='{description}'  WHERE id={id};")

def update_affected_transactions(id, cursor, new_transaction):
    cursor.execute(f"SELECT * FROM TRANSACTIONS WHERE id > {id};")
    transactions = cursor.fetchall()
    if len(transactions) == 0:
        return 0
    else:
        prev_transaction = new_transaction
        for transaction in transactions:
            
            transaction["before_cash"] = int(prev_transaction["after_cash"])
            transaction["before_gpay"] = int(prev_transaction["after_gpay"])

            if transaction["account"] == "cash":
                transaction["after_cash"] = (transaction["type"] * transaction["amount"]) + int(transaction["before_cash"])
                transaction["after_gpay"] = int(transaction["before_gpay"])
            else:
                transaction["after_gpay"] = (transaction["type"] * transaction["amount"]) + int(transaction["before_gpay"])
                transaction["after_cash"] = int(transaction["before_cash"])


            prev_transaction = transaction
            
            update_single_transaction(transaction["id"], cursor, transaction)
        return len(transactions)


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

@app.route("/edit", methods=["GET", "POST"])
def edit_record():
    if request.method == "GET":
        id = int(request.args.get("id"))
        
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute(f"SELECT * FROM TRANSACTIONS WHERE ID={id};")
        
        transactions = cursor.fetchall()
        if len(transactions) == 0:
            return render_template("edit_record.html", fields=dict(id=-1))
        transaction = transactions[0]

        return render_template("edit_record.html", fields=transaction)
    else:
        id = int(request.form["id"])
        
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute(f"SELECT * FROM TRANSACTIONS WHERE ID > {id};")
        
        transactions = cursor.fetchall()
        if len(transactions) == 0:
            # case where the queried transaction is the last transaction

            account = request.form["account"]
            amount = int(request.form["amount"])
            datetime_str = request.form["datetime"]
            description = request.form["description"]
            
            before_gpay = int(request.form["before_gpay"])
            after_gpay = int(request.form["after_gpay"]) 
            before_cash = int(request.form["before_cash"])
            after_cash = int(request.form["after_cash"])
            transaction_type = int(request.form["type"])

            if int(request.form["type"]) * (int(request.form["after_" + account]) - int(request.form["before_" + account])) != int(amount):
                return f"<html>before and after amounts do not match with amount, check again, got {dict(request.form)=}</html>"

            cursor.execute(f"UPDATE TRANSACTIONS SET ACCOUNT='{account}', " +
                           f"AMOUNT={amount}, TYPE={transaction_type}, BEFORE_GPAY={before_gpay}, " +
                           f"AFTER_GPAY={after_gpay}, BEFORE_CASH={before_cash}, AFTER_CASH={after_cash}, " +
                           f"DATETIME='{datetime_str}', DESCRIPTION='{description}'  WHERE id={id};")
            conn.commit()       
            cursor.close()
            conn.close()

            return render_template("transaction_record_success.html", transaction_id=id)
        else:
            # get before and after delta for both modes
            # apply the same transformation to all transactions to all transactions after that
            cursor.execute(f"SELECT * FROM TRANSACTIONS WHERE ID={id};")
            transaction = cursor.fetchall()[0]



            account = request.form["account"]
            amount = int(request.form["amount"])
            datetime_str = request.form["datetime"]
            description = request.form["description"]
            
            before_gpay = int(request.form["before_gpay"])
            after_gpay = int(request.form["after_gpay"]) 
            before_cash = int(request.form["before_cash"])
            after_cash = int(request.form["after_cash"])
            transaction_type = int(request.form["type"])

            if int(request.form["type"]) * (int(request.form["after_" + account]) - int(request.form["before_" + account])) != int(amount):
                return f"<html>before and after amounts do not match with amount, check again, got {dict(request.form)=}</html>"
            
            cursor.execute(f"UPDATE TRANSACTIONS SET ACCOUNT='{account}', " +
                           f"AMOUNT={amount}, TYPE={transaction_type}, BEFORE_GPAY={before_gpay}, " +
                           f"AFTER_GPAY={after_gpay}, BEFORE_CASH={before_cash}, AFTER_CASH={after_cash}, " +
                           f"DATETIME='{datetime_str}', DESCRIPTION='{description}'  WHERE id={id};")

            update_affected_transactions(id, cursor, dict(request.form))

            conn.commit()       
            cursor.close()
            conn.close()

            return render_template("transaction_record_success.html", transaction_id=id) 
        
def get_transactions_greater_than(id):
    pass


@app.route("/income", methods=["POST", "GET"])
def add_income():
    if request.method == "POST":
        conn = connect_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT BEFORE_GPAY, AFTER_GPAY, BEFORE_CASH, AFTER_CASH FROM TRANSACTIONS WHERE ID=(SELECT MAX(ID) FROM TRANSACTIONS);")

        transaction = dict(cursor.fetchall()[0])

        account = request.form["account"]
        amount = int(request.form["amount"])
        datetime_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
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
        datetime_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
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