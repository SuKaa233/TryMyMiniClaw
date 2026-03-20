import pymysql

# Database connection settings
HOST = "127.0.0.1"
PORT = 3306
USER = "root"
PASSWORD = "123456"

# Connect without specifying a database first to create it if it doesn't exist
try:
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD)
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS `root`")
        print("Database 'root' created or already exists.")
    conn.commit()
finally:
    conn.close()

# Reconnect specifying the 'root' database
conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database="root")

# SQL to drop existing tables to start fresh
drop_tables = [
    "DROP TABLE IF EXISTS `employee_skill`;",
    "DROP TABLE IF EXISTS `task`;",
    "DROP TABLE IF EXISTS `skill`;",
    "DROP TABLE IF EXISTS `employee`;",
    "DROP TABLE IF EXISTS `department`;"
]

# SQL to create tables
create_tables = [
    """
    CREATE TABLE `department` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `name` VARCHAR(100) NOT NULL,
        `location` VARCHAR(100)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE `employee` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `name` VARCHAR(100) NOT NULL,
        `title` VARCHAR(100),
        `department_id` INT,
        `hire_date` DATE,
        FOREIGN KEY (`department_id`) REFERENCES `department`(`id`) ON DELETE SET NULL
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE `skill` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `skill_name` VARCHAR(100) NOT NULL,
        `category` VARCHAR(50)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE `task` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `title` VARCHAR(200) NOT NULL,
        `status` VARCHAR(50) DEFAULT 'Pending',
        `assigned_to` INT,
        FOREIGN KEY (`assigned_to`) REFERENCES `employee`(`id`) ON DELETE SET NULL
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE `employee_skill` (
        `employee_id` INT,
        `skill_id` INT,
        PRIMARY KEY (`employee_id`, `skill_id`),
        FOREIGN KEY (`employee_id`) REFERENCES `employee`(`id`) ON DELETE CASCADE,
        FOREIGN KEY (`skill_id`) REFERENCES `skill`(`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """
]

# SQL to insert mock data
insert_data = [
    "INSERT INTO `department` (`id`, `name`, `location`) VALUES (1, 'Engineering', 'Building A'), (2, 'Design', 'Building B');",
    
    "INSERT INTO `employee` (`id`, `name`, `title`, `department_id`, `hire_date`) VALUES "
    "(1, 'Alice Smith', 'Senior Developer', 1, '2020-05-15'), "
    "(2, 'Bob Jones', 'Junior Developer', 1, '2022-08-01'), "
    "(3, 'Charlie Brown', 'UI/UX Designer', 2, '2021-11-20');",
    
    "INSERT INTO `skill` (`id`, `skill_name`, `category`) VALUES "
    "(1, 'Python', 'Programming'), "
    "(2, 'React', 'Frontend'), "
    "(3, 'Figma', 'Design');",
    
    "INSERT INTO `task` (`id`, `title`, `status`, `assigned_to`) VALUES "
    "(1, 'Build backend API', 'In Progress', 1), "
    "(2, 'Write unit tests', 'Pending', 2), "
    "(3, 'Design landing page', 'Completed', 3);",
    
    "INSERT INTO `employee_skill` (`employee_id`, `skill_id`) VALUES "
    "(1, 1), (1, 2), "
    "(2, 1), "
    "(3, 3);"
]

try:
    with conn.cursor() as cursor:
        # Drop tables
        for sql in drop_tables:
            cursor.execute(sql)
            
        # Create tables
        for sql in create_tables:
            cursor.execute(sql)
            
        # Insert data
        for sql in insert_data:
            cursor.execute(sql)
            
    conn.commit()
    print("Test tables and mock data successfully created in MySQL!")
except Exception as e:
    print(f"Error occurred: {e}")
    conn.rollback()
finally:
    conn.close()
