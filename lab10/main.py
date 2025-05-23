import psycopg2  # PostgreSQL дерекқорымен жұмыс істеуге арналған psycopg2 кітапханасын импорттау
import csv       # CSV файлдарымен жұмыс істеуге арналған csv кітапханасын импорттау
import os        # Операциялық жүйемен байланысты функциялар үшін os кітапханасын импорттау (бұл кодта тікелей қолданылмаған)

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
def check_table_exists():  # 'check_table_exists' атты функцияны анықтау
    try:  # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        # 'public.contacts' кестесінің бар-жоғын тексеретін SQL сұрауын орындау
        cur.execute("SELECT to_regclass('public.contacts');")
        # Сұрау нәтижесін алу (кесте бар болса кесте аты, жоқ болса None)
        result = cur.fetchone()[0]
        if result is None:  # Егер нәтиже None болса (кесте жоқ)
            print("Кесте жоқ, оны жасау керек.") # Кестенің жоқ екенін хабарлау
            # Егер кесте жоқ болса, оны жасау керек
            cur.execute("""  # Көп жолды SQL сұрауын бастау
                CREATE TABLE contacts (  # 'contacts' атты жаңа кесте жасау
                    id SERIAL PRIMARY KEY,  # Автоматты түрде өсетін бірегей идентификатор (негізгі кілт)
                    name VARCHAR(100),      # Аты сақталатын баған (100 символға дейін)
                    phone VARCHAR(20)       # Телефон нөмірі сақталатын баған (20 символға дейін)
                );
            """) # SQL сұрауын аяқтау
            conn.commit()  # Өзгерістерді (кестені жасауды) дерекқорда сақтау
            print("Кесте жасалды.") # Кестенің сәтті жасалғанын хабарлау
        else:  # Егер кесте бар болса
            print("Кесте бар.") # Кестенің бар екенін хабарлау
    except Exception as e:  # Егер try блогында қате орын алса
        print(f"Қате орын алды: {e}") # Қатенің мәтінін шығару
        conn.rollback() # Қате болған жағдайда транзакцияны (өзгерістерді) бастапқы күйіне қайтару

# CSV файлдан деректерді енгізу функциясы
def insert_from_csv(file_path): # 'insert_from_csv' функциясын анықтау (файл жолын параметр ретінде қабылдайды)
    try: # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        # CSV файлды ашу ('r' - оқу режимі)
        with open(file_path, 'r') as f: # Файлды 'f' деп ашу, 'with' файлдың автоматты жабылуын қамтамасыз етеді
            reader = csv.reader(f) # CSV файлын оқуға арналған reader нысанын жасау
            # Әр жолды оқу
            for row in reader: # Файлдағы әрбір жолды ('row') оқу циклі
                # Жолда екі баған болғанын тексеру
                if len(row) == 2: # Егер жолдағы элементтер саны 2-ге тең болса
                    # Деректерді 'contacts' кестесіне енгізу (SQL injection-нан қорғалу үшін параметрленген сұрау)
                    cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (row[0], row[1]))
                else: # Егер жолдағы элементтер саны 2-ге тең болмаса
                    print(f"Ескерту: {row} жолы дұрыс емес форматта.") # Дұрыс емес формат туралы ескерту шығару
            conn.commit()  # Барлық енгізілген деректерді дерекқорда сақтау
            print("📥 CSV деректері қосылды.") # Деректердің сәтті қосылғанын хабарлау
    except Exception as e: # Егер try блогында қате орын алса
        print(f"Қате орын алды: {e}") # Қатенің мәтінін шығару
        conn.rollback()  # Қате болған жағдайда транзакцияны бастапқы күйіне қайтару

# Қолданушыдан енгізу арқылы деректер қосу функциясы
def insert_from_input(): # 'insert_from_input' функциясын анықтау
    try: # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        name = input("Атыңызды енгізіңіз: ") # Пайдаланушыдан атты сұрау
        phone = input("Телефон нөмірі: ") # Пайдаланушыдан телефон нөмірін сұрау
        # Пайдаланушы енгізген деректерді кестеге қосу
        cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (name, phone))
        conn.commit() # Өзгерісті дерекқорда сақтау
        print("✅ Жаңа контакт қосылды.") # Контактінің сәтті қосылғанын хабарлау
    except Exception as e: # Егер try блогында қате орын алса
        print(f"Қате орын алды: {e}") # Қатенің мәтінін шығару
        conn.rollback() # Қате болған жағдайда транзакцияны бастапқы күйіне қайтару

# Контактіні жаңарту функциясы
def update_contact(): # 'update_contact' функциясын анықтау
    try: # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        contact_id = input("Қай ID жаңартасың? ") # Пайдаланушыдан жаңартылатын контактінің ID-сін сұрау
        new_name = input("Жаңа аты: ") # Пайдаланушыдан жаңа атты сұрау
        new_phone = input("Жаңа телефон: ") # Пайдаланушыдан жаңа телефон нөмірін сұрау
        # Көрсетілген ID бойынша контактінің аты мен телефонын жаңарту
        cur.execute("UPDATE contacts SET name = %s, phone = %s WHERE id = %s", (new_name, new_phone, contact_id))
        conn.commit() # Жаңартуды дерекқорда сақтау
        print("♻️ Контакт жаңартылды.") # Контактінің сәтті жаңартылғанын хабарлау
    except Exception as e: # Егер try блогында қате орын алса
        print(f"Қате орын алды: {e}") # Қатенің мәтінін шығару
        conn.rollback() # Қате болған жағдайда транзакцияны бастапқы күйіне қайтару

# Фильтрмен сұраныс жасау функциясы
def query_with_filter(): # 'query_with_filter' функциясын анықтау
    try: # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        keyword = input("Аты не номер бойынша ізде: ") # Пайдаланушыдан іздеу кілт сөзін сұрау
        # Ат немесе телефон бойынша іздеу (ILIKE - регистрге тәуелсіз іздеу, % - кез келген символдар тізбегі)
        cur.execute("SELECT * FROM contacts WHERE name ILIKE %s OR phone ILIKE %s", (f'%{keyword}%', f'%{keyword}%'))
        rows = cur.fetchall() # Сұрау нәтижесінде табылған барлық жолдарды алу
        if rows: # Егер нәтижелер (жолдар) табылса
            for row in rows: # Табылған әрбір жолды циклмен өту
                print(row) # Әрбір жолды (контакт деректерін) экранға шығару
        else: # Егер ешқандай жол табылмаса
            print("Мәлімет табылмады.") # Нәтиже жоқ екенін хабарлау
    except Exception as e: # Егер try блогында қате орын алса
        print(f"Қате орын алды: {e}") # Қатенің мәтінін шығару

# Контактіні өшіру функциясы
def delete_contact(): # 'delete_contact' функциясын анықтау
    try: # Мүмкін болатын қателерді ұстау үшін try блогын бастау
        contact_id = input("Қай ID өшіргің келеді? ") # Пайдаланушыдан өшірілетін контактінің ID-сін сұрау
        # Көрсетілген ID бойынша контактіні кестеден өшіру (үтір бір элементті кортеж жасау үшін қажет)
        cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
        conn.commit() # Өшіру операциясын дерекқорда сақтау
        print("❌ Контакт өшірілді.") # Контактінің сәтті өшірілгенін хабарлау
    except Exception as e: # Егер try блогында қате орын алса
        print(f"Қате орын алды: {e}") # Қатенің мәтінін шығару
        conn.rollback() # Қате болған жағдайда транзакцияны бастапқы күйіне қайтару

# Негізгі меню
def menu(): # 'menu' функциясын анықтау
    run = True # Циклдің жұмысын басқаратын айнымалыны 'True' деп орнату
    check_table_exists()  # Бағдарлама басталғанда кестенің бар-жоғын тексеру (және қажет болса жасау)

    while run: # 'run' айнымалысы 'True' болғанша цикл жалғасады
        print("\n📱 PHONEBOOK MENU:") # Меню тақырыбын шығару
        print("1 - insert csv")          # 1-ші опцияны көрсету
        print("2 - from input")        # 2-ші опцияны көрсету
        print("3 - update contact")    # 3-ші опцияны көрсету
        print("4 - query with filter") # 4-ші опцияны көрсету
        print("5 - delete contact")    # 5-ші опцияны көрсету
        print("6 - break")             # 6-шы опцияны (шығу) көрсету

        # Пайдаланушыдан таңдау сұрау
        choice = input("Таңдаңыз (1–6): ") # Пайдаланушының таңдауын 'choice' айнымалысына сақтау

        # Таңдалған әрекетке байланысты функцияларды орындау
        if choice == '1': # Егер таңдау '1' болса
            file_path = input("CSV файлдың толық жолын енгізіңіз: ") # CSV файл жолын сұрау
            insert_from_csv(file_path) # CSV-дан енгізу функциясын шақыру

        elif choice == '2': # Егер таңдау '2' болса
            insert_from_input() # Қолмен енгізу функциясын шақыру

        elif choice == '3': # Егер таңдау '3' болса
            update_contact() # Жаңарту функциясын шақыру

        elif choice == '4': # Егер таңдау '4' болса
            query_with_filter() # Іздеу функциясын шақыру

        elif choice == '5': # Егер таңдау '5' болса
            delete_contact() # Өшіру функциясын шақыру

        elif choice == '6': # Егер таңдау '6' болса
            run = False # Циклды тоқтату үшін 'run' айнымалысын 'False' ету
        else: # Егер таңдау 1-6 аралығында болмаса
            print("❗ Қате таңдау.") # Қате таңдау туралы хабарлама шығару

# Бағдарламаны іске қосу
menu() # Негізгі меню функциясын шақыру (бағдарлама осы жерден басталады)

# Курсор мен байланыс объектілерін жабу (бағдарлама аяқталғанда ресурстарды босату)
cur.close() # Курсорды жабу
conn.close() # Дерекқормен байланысты жабу