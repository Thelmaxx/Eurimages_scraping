import pyodbc

cnxn = pyodbc.connect("Driver={SQL Server};"
                        "Server=LAPTOP-IUA12HD6\SQLSERVER2;"
                        "Database=Coeurimages;"
                        "Trusted_Connection=yes;")

crsr = cnxn.cursor()
crsr.execute('insert into Test_connection (test) values (9)')
crsr.commit()