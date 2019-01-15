import pyodbc as engine


class dbConnection:
    def __init__(self, statement):
        self.string = engine.connect('DRIVER=FreeTDS;SERVER=192.168.0.100;PORT=1433;'
                                     'DATABASE=JonasNET;UID=Jonas01;PWD=Jonas01;TDS_Version=8.0;')
        self.cursor = self.string.cursor()
        self.cursor.execute(statement)
        self.rows = self.cursor.fetchall()

    def data(self):
        return self.rows
