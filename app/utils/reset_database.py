import pymysql

from app.config import ADMIN_HOST, ADMIN_PASSWORD, ADMIN_USERNAME


def reset_database():
    conn = pymysql.connect(
        host=ADMIN_HOST,
        user=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
    )
    cursor = conn.cursor()

    # get all databases
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    for item in databases:
        database_name = item[0]
        if database_name.startswith("tenant_"):
            # Delete the database
            cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
            print(f"Deleted database: {database_name}")

    cursor.execute("DROP DATABASE IF EXISTS management_database")
    print("Deleted database: management_database")
    cursor.execute("CREATE DATABASE management_database")
    print("Created database: management_database")
