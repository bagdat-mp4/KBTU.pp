import psycopg2  # PostgreSQL дерекқорымен жұмыс істеуге арналған psycopg2 кітапханасын импорттау
import csv       # CSV файлдарымен жұмыс істеуге арналған csv кітапханасын импорттау
import os        # Операциялық жүйемен байланысты функциялар үшін os кітапханасын импорттау

# PostgreSQL-ға қосылу үшін параметрлерді орнату
conn = psycopg2.connect(  # PostgreSQL дерекқорына қосылуды бастау
    database="postgres",  # Қосылатын дерекқордың аты
    user="postgres",      # Дерекқорға кіру үшін пайдаланушы аты
    password="1111",      # Пайдаланушының құпиясөзі
    host="localhost",     # Дерекқор сервері орналасқан хост (компьютер)
    port="5432"           # Дерекқор сервері тыңдайтын порт нөмірі
)

cur = conn.cursor()  # Дерекқорда SQL сұрауларын орындау үшін курсор нысанын жасау

# contacts кестесінің бар екенін тексеру функциясы
def check_table_exists(): # 'check_table_exists' атты функцияны анықтау
    try: # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        # 'public.contacts' кестесінің бар-жоғын тексеретін SQL сұрауын орындау
        cur.execute("SELECT to_regclass('public.contacts');")
        # Сұрау нәтижесін алу
        result = cur.fetchone()[0]
        if result is None: # Егер кесте жоқ болса
            print("Кесте жоқ, оны жасау керек.") # Хабарлама шығару
            # Егер кесте жоқ болса, оны жасау керек
            cur.execute(""" # Көп жолды SQL сұрауын бастау
                CREATE TABLE contacts ( # 'contacts' атты жаңа кесте жасау
                    id SERIAL PRIMARY KEY, # Автоматты түрде өсетін бірегей идентификатор
                    name VARCHAR(100),     # Аты сақталатын баған
                    phone VARCHAR(20)      # Телефон нөмірі сақталатын баған
                );
            """) # SQL сұрауын аяқтау
            conn.commit() # Өзгерістерді дерекқорда сақтау
            print("Кесте жасалды.") # Сәтті жасалғаны туралы хабарлама
        else: # Егер кесте бар болса
            print("Кесте бар.") # Бар екендігі туралы хабарлама
    except Exception as e: # Егер қате орын алса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама
        conn.rollback() # Өзгерістерді болдырмау

# Үлгі (pattern) бойынша барлық жазбаларды қайтаратын функция
def search_contacts(pattern): # 'search_contacts' функциясын анықтау ('pattern' параметрімен)
    try: # Қателерді ұстау блогы
        # Ат немесе телефон берілген үлгіге сәйкес келетін жазбаларды іздеу (ILIKE - регистрге тәуелсіз)
        cur.execute("SELECT * FROM contacts WHERE name ILIKE %s OR phone ILIKE %s", (f'%{pattern}%', f'%{pattern}%'))
        rows = cur.fetchall() # Барлық табылған жолдарды алу
        if rows: # Егер жолдар табылса
            for row in rows: # Әрбір жолды итерациялау
                print(row) # Жолды экранға шығару
        else: # Егер ештеңе табылмаса
            print("Мәлімет табылмады.") # Хабарлама шығару
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама

# Аты мен телефоны бойынша жаңа пайдаланушыны енгізуге арналған процедура, егер пайдаланушы бар болса, телефонын жаңартады
def insert_or_update_user(user_name, user_phone): # 'insert_or_update_user' процедурасын анықтау
    try: # Қателерді ұстау блогы
        # Берілген ат бойынша пайдаланушының бар-жоғын тексеру
        cur.execute("SELECT id FROM contacts WHERE name = %s", (user_name,))
        result = cur.fetchone() # Нәтижені алу (табылса кортеж, жоқ болса None)
        if result: # Егер пайдаланушы табылса
            # Пайдаланушының телефонын жаңарту
            cur.execute("UPDATE contacts SET phone = %s WHERE name = %s", (user_phone, user_name))
            print(f"User {user_name} phone updated.") # Жаңартылғаны туралы хабарлама
        else: # Егер пайдаланушы табылмаса
            # Жаңа пайдаланушыны кестеге қосу
            cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (user_name, user_phone))
            print(f"User {user_name} added.") # Қосылғаны туралы хабарлама
        conn.commit() # Өзгерістерді (қосу немесе жаңарту) сақтау
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама
        conn.rollback() # Өзгерістерді болдырмау

# Аты мен телефоны тізімі бойынша көптеген жаңа пайдаланушыларды енгізу процедурасы, телефон дұрыстығын тексереді
def insert_multiple_users(users_list): # 'insert_multiple_users' процедурасын анықтау ('users_list' тізімін қабылдайды)
    try: # Қателерді ұстау блогы
        for user_data in users_list: # Тізімдегі әрбір элемент ('user_data') үшін цикл
            name_part, phone_part = user_data.split(',') # Элементті үтір арқылы ат пен телефонға бөлу
            # Телефон нөмірі тек сандардан тұрмаса НЕМЕСЕ ұзындығы 10-нан аз болса (қарапайым тексеру)
            if not phone_part.isdigit() or len(phone_part) < 10:
                print(f"Қате дерек: {user_data} дұрыс емес телефон.") # Қате формат туралы хабарлама
            else: # Егер телефон форматы дұрыс болса
                 # Пайдаланушыны қосу немесе жаңарту үшін алдыңғы процедураны шақыру
                insert_or_update_user(name_part, phone_part)
        print("Барлық деректер қосылды.") # Барлық деректерді өңдеу әрекеті аяқталғаны туралы хабарлама
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама

# Пагинацияға арналған функция (limit және offset)
def get_contacts_paginated(limit_size, offset_size): # 'get_contacts_paginated' функциясын анықтау
    try: # Қателерді ұстау блогы
        # Белгілі бір саннан ('limit_size') аспайтын және белгілі бір орыннан ('offset_size') басталатын контактілерді таңдау
        cur.execute("SELECT * FROM contacts LIMIT %s OFFSET %s", (limit_size, offset_size))
        rows = cur.fetchall() # Табылған жолдарды алу
        if rows: # Егер жолдар табылса
            for row in rows: # Әрбір жолды итерациялау
                print(row) # Жолды шығару
        else: # Егер ештеңе табылмаса
            print("Мәлімет табылмады.") # Хабарлама шығару
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама

# Пайдаланушы аты немесе телефоны бойынша контактіні өшіру процедурасы
def delete_contact_by_user_or_phone(user_name=None, user_phone=None): # 'delete_contact_by_user_or_phone' процедурасын анықтау (міндетті емес параметрлермен)
    try: # Қателерді ұстау блогы
        if user_name: # Егер 'user_name' берілсе
            # Аты бойынша контактіні өшіру
            cur.execute("DELETE FROM contacts WHERE name = %s", (user_name,))
        elif user_phone: # Немесе, егер 'user_phone' берілсе
            # Телефоны бойынша контактіні өшіру
            cur.execute("DELETE FROM contacts WHERE phone = %s", (user_phone,))
        conn.commit() # Өшіру операциясын сақтау
        print("❌ Контакт өшірілді.") # Өшірілгені туралы хабарлама
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама
        conn.rollback() # Өзгерістерді болдырмау

# CSV файлынан деректерді енгізу функциясы (жаңартылған)
def insert_from_csv(file_path): # 'insert_from_csv' функциясын анықтау
    try: # Қателерді ұстау блогы
        with open(file_path, 'r') as f: # Файлды оқуға ашу
            reader = csv.reader(f) # CSV оқу құралын жасау
            for row in reader: # Файлдағы әрбір жол үшін
                if len(row) == 2: # Егер жолда 2 элемент болса
                    # Пайдаланушыны қосу немесе жаңарту үшін 'insert_or_update_user' процедурасын шақыру
                    insert_or_update_user(row[0], row[1])
                else: # Егер формат дұрыс болмаса
                    print(f"Ескерту: {row} жолы дұрыс емес форматта.") # Ескерту шығару
            print("📥 CSV деректері қосылды.") # Аяқталғаны туралы хабарлама
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама

# Қолмен енгізу арқылы деректерді енгізу функциясы (жаңартылған)
def insert_from_input(): # 'insert_from_input' функциясын анықтау
    try: # Қателерді ұстау блогы
        name = input("Атыңызды енгізіңіз: ") # Пайдаланушыдан атты сұрау
        phone = input("Телефон нөмірі: ") # Пайдаланушыдан телефонды сұрау
        # Пайдаланушыны қосу немесе жаңарту үшін 'insert_or_update_user' процедурасын шақыру
        insert_or_update_user(name, phone)
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама

# Контактіні жаңарту функциясы (ID бойынша)
def update_contact(): # 'update_contact' функциясын анықтау
    try: # Қателерді ұстау блогы
        contact_id = input("Қай ID жаңартасың? ") # Жаңартылатын ID сұрау
        new_name = input("Жаңа аты: ") # Жаңа атты сұрау
        new_phone = input("Жаңа телефон: ") # Жаңа телефонды сұрау
        # Берілген ID бойынша ат пен телефонды жаңарту
        cur.execute("UPDATE contacts SET name = %s, phone = %s WHERE id = %s", (new_name, new_phone, contact_id))
        conn.commit() # Жаңартуды сақтау
        print("♻️ Контакт жаңартылды.") # Сәтті жаңартылғаны туралы хабарлама
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама
        conn.rollback() # Өзгерістерді болдырмау

# Фильтрмен сұраныс жасау функциясы (бұрынғыдай)
def query_with_filter(): # 'query_with_filter' функциясын анықтау
    try: # Қателерді ұстау блогы
        keyword = input("Аты не номер бойынша ізде: ") # Іздеу кілт сөзін сұрау
        # Ат немесе телефон бойынша іздеу (ILIKE - регистрге тәуелсіз)
        cur.execute("SELECT * FROM contacts WHERE name ILIKE %s OR phone ILIKE %s", (f'%{keyword}%', f'%{keyword}%'))
        rows = cur.fetchall() # Барлық табылған жолдарды алу
        if rows: # Егер жолдар табылса
            for row in rows: # Әрбір жолды итерациялау
                print(row) # Жолды шығару
        else: # Егер ештеңе табылмаса
            print("Мәлімет табылмады.") # Хабарлама шығару
    except Exception as e: # Қате болса
        print(f"Қате орын алды: {e}") # Қате туралы хабарлама

# Негізгі меню (жаңартылған)
def menu(): # 'menu' функциясын анықтау
    run = True # Циклдің жұмысын басқаратын айнымалы
    check_table_exists()  # Меню алдында кестені тексеру

    while run: # 'run' True болғанша цикл жалғасады
        print("\n📱 PHONEBOOK MENU:") # Меню тақырыбы
        print("1 - Search by pattern")      # 1-ші опция: Үлгі бойынша іздеу
        print("2 - Insert from CSV")        # 2-ші опция: CSV-дан енгізу
        print("3 - Insert from input")      # 3-ші опция: Қолмен енгізу
        print("4 - Update contact")         # 4-ші опция: Контактіні жаңарту (ID бойынша)
        print("5 - Query with filter")      # 5-ші опция: Фильтрмен сұраныс
        print("6 - Delete contact")         # 6-ші опция: Контактіні өшіру (ат/телефон бойынша)
        print("7 - Exit")                   # 7-ші опция: Шығу

        # Пайдаланушыдан таңдау сұрау
        choice = input("Таңдаңыз (1–7): ") # Таңдауды алу

        if choice == '1': # Егер таңдау '1' болса
            pattern = input("Іздеу үшін үлгі енгізіңіз: ") # Үлгіні сұрау
            search_contacts(pattern) # Үлгі бойынша іздеу функциясын шақыру
        elif choice == '2': # Егер таңдау '2' болса
            file_path = input("CSV файлдың толық жолын енгізіңіз: ") # CSV файл жолын сұрау
            insert_from_csv(file_path) # CSV-дан енгізу функциясын шақыру
        elif choice == '3': # Егер таңдау '3' болса
            insert_from_input() # Қолмен енгізу функциясын шақыру
        elif choice == '4': # Егер таңдау '4' болса
            update_contact() # Контактіні жаңарту (ID бойынша) функциясын шақыру
        elif choice == '5': # Егер таңдау '5' болса
            query_with_filter() # Фильтрмен сұраныс функциясын шақыру
        elif choice == '6': # Егер таңдау '6' болса
            user_name_or_phone = input("Өшірілетін контактінің аты немесе телефон нөмірін енгізіңіз: ") # Ат немесе телефонды сұрау
            # Ат немесе телефон бойынша өшіру процедурасын шақыру (берілген мәнді 'user_name' ретінде жібереді)
            delete_contact_by_user_or_phone(user_name=user_name_or_phone)
        elif choice == '7': # Егер таңдау '7' болса
            run = False # Циклды тоқтату үшін 'run' айнымалысын 'False' ету
        else: # Егер жарамсыз таңдау болса
            print("❗ Қате таңдау.") # Қате туралы хабарлама

# Бағдарламаны іске қосу
menu()  # Негізгі меню функциясын шақыру

# Курсор мен байланыс объектілерін жабу
cur.close() # Курсорды жабу
conn.close() # Дерекқормен байланысты жабу