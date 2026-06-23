import pymysql
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='srigan@7484',
        database='medical_appointment_system'
    )
    return connection

