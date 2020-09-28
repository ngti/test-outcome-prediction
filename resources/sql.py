import pyodbc


class SQLConnection:
    def __init__(self, database_sever, database, username, password):
        self.database_server = database_sever
        self.database = database
        self.username = username
        self.password = password
        self.sql_conn = None

    def __enter__(self):
        print("ENTER SQL CONNECTION")
        sql_conn = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};Server=tcp:' + self.database_server + ',1433;'
            'Database=' + self.database + ';Uid=' + self.username + ';Pwd=' + self.password + ';'
            'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=120;')
        sql_conn.autocommit = False
        self.sql_conn = sql_conn
        return self.sql_conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("EXIT SQL CONNECTION")
        self.sql_conn.close()

    def list_sql_column_names(self):
        column_list = []
        cursor = self.sql_conn.cursor()
        # TODO: Add name of SQL table
        cursor.execute("SELECT TOP 1 * FROM ExampleTable")
        cursor.commit()
        # TODO: Add name of SQL table
        for row in cursor.columns(table='ExampleTable'):
            column_list.append(row.column_name)
        return column_list[7:]

    def insert_row_into_sql(self, row_list):
        cursor = self.sql_conn.cursor()
        cursor.fast_executemany = True
        # TODO: Add name of SQL table
        # TODO: Check if amount of "?"'s matches amount of features used for training
        cursor.executemany(
            "INSERT INTO ExampleTable VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?)",
            row_list)
        cursor.commit()

    def insert_prediction(self, final_result):
        project = final_result[0]
        prediction = final_result[1]
        real_result = final_result[2]

        print("INSERT VALUES: ")
        print("PROJECT: ", project)
        print("PREDICTION: ", prediction)
        print("REAL RESULT: ", real_result)

        cursor = self.sql_conn.cursor()
        cursor.execute("INSERT INTO predictions(project, prediction, realResult) VALUES (?, ?, ?)",
                       (project, prediction, real_result))
        cursor.commit()
