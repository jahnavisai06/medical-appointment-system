from config import get_db_connection

def create_notification(user_id, user_type, message, link=None):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO notifications (user_id, user_type, message, link) VALUES (%s, %s, %s, %s)",
        (user_id, user_type, message, link)
    )
    connection.commit()
    cursor.close()
    connection.close()

def get_notifications(user_id, user_type):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, message, is_read, created_at, link FROM notifications WHERE user_id = %s AND user_type = %s ORDER BY created_at DESC",
        (user_id, user_type)
    )
    notifications = cursor.fetchall()
    cursor.close()
    connection.close()
    return notifications

def mark_as_read(user_id, user_type):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND user_type = %s",
        (user_id, user_type)
    )
    connection.commit()
    cursor.close()
    connection.close()

def get_unread_count(user_id, user_type):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND user_type = %s AND is_read = FALSE",
        (user_id, user_type)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return count