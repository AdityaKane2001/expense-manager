# expense-manager

A micro app written in Flask using the following (inspired by [ashutosh1919/grocery-todo](https://github.com/ashutosh1919/grocery-todo)):

- Flask Application backend is provides APIs for Database CRUD operation which can be used by frontend client. Flask is hosted on [Render](https://render.com/).
    - Base URL for deployed web service (API): [https://grocery-todo-backend.onrender.com](https://grocery-todo-backend.onrender.com)
- PostgreSQL database stores all the list data in form of (ID, Item) row in the `groceries` table. It is hosted on [ElephantSQL](https://elephantsql.com)