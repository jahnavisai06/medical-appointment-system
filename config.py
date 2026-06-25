import pymysql
import os

def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv('MYSQLHOST', 'localhost'),
        port=int(os.getenv('MYSQLPORT', 3306)),
        user=os.getenv('MYSQLUSER', 'root'),
        password=os.getenv('MYSQLPASSWORD', 'srigan@7484'),
        database=os.getenv('MYSQLDATABASE', 'medical_appointment_system')
    )
    return connection