from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import psycopg2
import time
import yaml
import os

try:
    DATABASE_URL = os.environ['DATABASE_URL']
except:
    load_dotenv()
    DATABASE_URL = os.environ['DATABASE_URL']

connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

with open('password.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

selected_tab = st.sidebar.radio("Login/Register", ["Login", "Register"])

if selected_tab == "Login":
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status == False:
        warning_message = st.warning('Uživatelské jméno/heslo je nesprávné nebo je prázdné')
        time.sleep(1.2)
        warning_message.empty()

    elif authentication_status == None:
        warning_message = st.warning('Zadejte prosím své uživatelské jméno a heslo.')
        time.sleep(1.2)
        warning_message.empty()

    if authentication_status:
        select_query = "SELECT * FROM public.\"user\""
        cursor.execute(select_query)
        user_data = cursor.fetchall()
        column_names = ["ID", "Username", "Name", "Type_User","Password", "Email", "Registration_Date"]
        user_df = pd.DataFrame(user_data, columns=column_names)
        user_df["Username_lower"] = user_df["Username"].str.lower()

        if (user_df["Username_lower"] == username.lower()).any():
            user_type = user_df.loc[user_df["Username_lower"] == username.lower(), "Type_User"].values[0]
        else:
            warning_message = st.warning('Uživatel nebyl nalezen')
            time.sleep(1.2)
            warning_message.empty()

        if username == 'admin':
            tab1, tab2, tab3, tab4 = st.tabs(["Přidat task", "Sledování časových úkolů", "Zobrazit tabulku s časem", "admin"])
        elif user_type == 'Agency' or 'Customer':            
            tab1, tab2 = st.tabs(["Přidat task", "Zobrazit tabulku s časem"])
        else:
            tab1, tab2  = st.tabs(["Sledování časových úkolů", "Zobrazit tabulku s časem"])
    
        user_type == 'Agency' or 'Customer'
        with tab1:
            with st.form("Add_task_form", clear_on_submit=True):
                st.title("Přidat task")
                task_name = st.text_input("Název tasku")

                if st.form_submit_button("Uložit do databáze"):
                    if task_name.strip() == "":
                        warning_mess = st.warning("Název tasku je povinný. Prosím, doplňte ho.")
                        time.sleep(2)
                        warning_mess.empty()
                    else:
                        check_query = "SELECT COUNT(*) FROM public.tasks WHERE \"Tasks\" = %s AND \"User\" = %s;"
                        cursor.execute(check_query, (task_name, username))
                        task_exists = cursor.fetchone()[0]

                        if task_exists > 0:
                            error_mess = st.error(f"Task '{task_name}' již existuje pro aktuálního uživatele.")
                            time.sleep(2)
                            error_mess.empty()
                        else:
                            sql_query = "INSERT INTO public.tasks (\"Tasks\", \"User\") VALUES (%s, %s);"
                            cursor.execute(sql_query, (task_name, username))
                            connection.commit()
                            success_mess = st.success(f"Task '{task_name}' byl úspěšně uložen do databáze.")
                            time.sleep(1)
                            success_mess.empty()

            with st.form("Delete_task_form", clear_on_submit=True):
                st.title("Smazat task a zobrazit tabulku")

                select_query = "SELECT * FROM public.tasks"
                cursor.execute(select_query,)
                tasks_data = cursor.fetchall()

                column_names = ["ID", "Task", "Tracking_time_tasks", "Start_time_of_tracking", "Stop_time_of_tracking", "User"]
                tasks_df = pd.DataFrame(tasks_data, columns=column_names)
                admin_tasks_df = tasks_df[tasks_df['User'] == username]
                selected_task = st.selectbox("Vyberte task", admin_tasks_df["Task"])

                if st.form_submit_button("Smazat"):
                    if selected_task:
                        delete_query = "DELETE FROM tasks WHERE (\"Tasks\") = %s"
                        cursor.execute(delete_query, (selected_task,))
                        connection.commit()
                        success_mess = st.success(f"task ''{selected_task} je smazáno z databáze.")
                        time.sleep(1)
                        success_mess.empty()
                        st.experimental_rerun()
                    else:
                        warning_mess = st.warning("Není žádný task k smazání.")
                        time.sleep(2)
                        warning_mess.empty()

                if st.form_submit_button("Zobrazit tabulku"):
                    tasks_df.drop(columns=['Tracking_time_tasks'], inplace=True)
                    tasks_df.drop(columns=['Start_time_of_tracking'], inplace=True)
                    tasks_df.drop(columns=['Stop_time_of_tracking'], inplace=True)
                    admin_tasks_df_1 = tasks_df[tasks_df['User'] == username]
                    admin_tasks_df_1.drop(columns=['User'], inplace=True)
                    st.dataframe(admin_tasks_df_1, hide_index=True, use_container_width=True)

                if st.form_submit_button("Smazat celou tabulku"):
                    delete_user_query = f"DELETE FROM public.tasks WHERE (\"User\") = '{username}';"
                    cursor.execute(delete_user_query)
                    connection.commit()

                    if cursor.rowcount > 0:
                        success_mess = st.success("Celá tabulka uživatelů byla smazána.")
                        time.sleep(2)
                        success_mess.empty()
                        st.experimental_rerun()
                    else:
                        warning_message = st.warning("Nebyla nalezena žádná tabulka uživatelů k smazání.")
                        time.sleep(2)
                        warning_message.empty()
                        st.experimental_rerun()

        with tab2:
            select_querys = "SELECT * FROM public.tasks;"
            cursor.execute(select_querys)
            tasks_data_2 = cursor.fetchall()
            column_names_2 = ["ID", "Task", "Tracking_time_tasks", "Start_time_of_tracking", "Stop_time_of_tracking", "User"]
            tasks_df_1 = pd.DataFrame(tasks_data_2, columns=column_names_2)
            tasks_df_2 = tasks_df_1[tasks_df_1["Tracking_time_tasks"].isna()]
            admin_tasks_df_1 = tasks_df_2[tasks_df_2['User'] == username]

            selected_task = st.selectbox("Vyberte task", admin_tasks_df_1["Task"])
            start_button = st.button('Start')
            stop_button = st.button('Stop')

            if st.button("Reset"):
                st.session_state.start_time = None
                st.session_state.elapsed_time = timedelta()
                time.sleep(0.5)
                st.experimental_rerun()

            task_name = selected_task

            if 'start_time' not in st.session_state:
                st.session_state.start_time = None

            if 'elapsed_time' not in st.session_state:
                st.session_state.elapsed_time = timedelta()

            if start_button:
                if task_name.strip() == "":
                    warning_mess = st.warning("Neexistuje žádný task.")
                    time.sleep(0.5)
                    warning_mess.empty()
                else:
                    st.session_state.start_time = datetime.now()
                    current_time = datetime.now()
                    formatted_start_time = current_time.strftime("%d-%m-%Y %H:%M:%S")

                    st.session_state.date_obj = datetime.strptime(formatted_start_time, "%d-%m-%Y %H:%M:%S")

            if stop_button:
                if st.session_state.start_time:
                    end_time = datetime.now()
                    elapsed_time = end_time - st.session_state.start_time
                    st.session_state.elapsed_time += elapsed_time
                    st.session_state.start_time = None

            if st.session_state.start_time:
                current_time = datetime.now() - st.session_state.start_time + st.session_state.elapsed_time
                hours, remainder = divmod(current_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = f'{hours:02}:{minutes:02}:{seconds:02}'

                time_container = st.empty()
                time_container.text(f'{formatted_time}')

            if not st.session_state.start_time:
                st.text('Časovač zastaven.')
                if st.session_state.elapsed_time.total_seconds() > 0:
                    elapsed_time = st.session_state.elapsed_time
                    hours, remainder = divmod(elapsed_time.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_elapsed_time = f'{hours:02}:{minutes:02}:{seconds:02}'
                    st.text(f'Uplynulý čas: {formatted_elapsed_time}')

            if st.session_state.start_time:
                while True:
                    if not st.session_state.start_time:
                        break
                    current_time = datetime.now() - st.session_state.start_time + st.session_state.elapsed_time
                    hours, remainder = divmod(current_time.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_time = f'{hours:02}:{minutes:02}:{seconds:02}'

                    time_container.text(f'Časovač běží: {formatted_time}')
                    time.sleep(1)

            if selected_task:
                if st.button("Uložit čas do databáze"):
                    current_stop_time = datetime.now()
                    adjusted_stop_time = current_stop_time - timedelta(seconds=2)
                    formatted_stop_time = adjusted_stop_time.strftime("%d-%m-%Y %H:%M:%S")

                    st.session_state.date_stop = datetime.strptime(formatted_stop_time, "%d-%m-%Y %H:%M:%S")
                    delete_query = "DELETE FROM public.tasks WHERE \"Tasks\" = %s AND \"User\" = %s;"
                    cursor.execute(delete_query, (selected_task, username))
                    connection.commit()

                    measured_time = st.session_state.elapsed_time
                    formatted_time = f"{measured_time.seconds // 3600:02d}:{(measured_time.seconds // 60) % 60:02d}:{measured_time.seconds % 60:02d}"
                    insert_query = "INSERT INTO public.tasks (\"Tasks\", \"Tracking_time_tasks\", \"Start_time_of_tracking\", \"Stop_time_of_tracking\", \"User\") VALUES (%s, %s, %s, %s, %s);"
                    cursor.execute(insert_query, (selected_task, formatted_time, st.session_state.date_obj, st.session_state.date_stop, username))
                    connection.commit()
                    success_mess = st.success(f"Čas byl uložen k úkolu '{selected_task}' s hodnotou {formatted_time}.")

                    st.session_state.start_time = None
                    st.session_state.elapsed_time = timedelta()

                    time.sleep(0.1)
                    st.experimental_rerun()

        with tab3:
            select_query = "SELECT * FROM public.tasks"
            cursor.execute(select_query,)
            tasks_data = cursor.fetchall()
            column_names = ["ID", "Task", "Tracking_time_tasks", "Start_time_of_tracking", "Stop_time_of_tracking", "User"]

            tasks_df = pd.DataFrame(tasks_data, columns=column_names)
            tasks_df['Tracking_time_tasks'] = tasks_df['Tracking_time_tasks'].apply(lambda x: str(x).split()[-1])

            admin_tasks_df = tasks_df[tasks_df['User'] == username]
            df = st.dataframe(admin_tasks_df, use_container_width=True, hide_index=True)
            csv = admin_tasks_df.to_csv(index=False) 

            st.download_button(
                label="Stáhnout data jako CSV",
                data=csv.encode('utf-8'),
                file_name='large_df.csv',
                mime='text/csv',
            )

        if username == 'admin':
            with tab4:
                with st.form("table_user_form", clear_on_submit=True):
                    st.title("Zobrazit a smazat tabulku všech uživatelů")
                    select_query = "SELECT * FROM public.tasks"
                    cursor.execute(select_query,)
                    tasks_data = cursor.fetchall()
                    column_names = ["ID", "Task", "Tracking_time_tasks", "Start_time_of_tracking", "Stop_time_of_tracking", "User"]

                    tasks_df = pd.DataFrame(tasks_data, columns=column_names)
                    tasks_df['Tracking_time_tasks'] = tasks_df['Tracking_time_tasks'].apply(lambda x: str(x).split()[-1])
                    df = st.dataframe(tasks_df, use_container_width=True, hide_index=True)

                    if st.form_submit_button("Smazat celou tabulku všech uživatelů"):
                        delete_user_query = f"DELETE FROM public.tasks;"
                        cursor.execute(delete_user_query)
                        connection.commit()

                        if cursor.rowcount > 0:
                            success_mess = st.success("Celá tabulka uživatelů byla smazána.")
                            time.sleep(2)
                            success_mess.empty()
                            st.experimental_rerun()
                        else:
                            warning_message = st.warning("Nebyla nalezena žádná tabulka uživatelů k smazání.")
                            time.sleep(2)
                            warning_message.empty()
                            st.experimental_rerun()

                    select_query = "SELECT * FROM public.tasks"
                    cursor.execute(select_query,)
                    tasks_data = cursor.fetchall()
                    column_names = ["ID", "Task", "Tracking_time_tasks", "Start_time_of_tracking", "Stop_time_of_tracking", "User"]
                    unique_users = tasks_df["User"].unique()
                    selected_task = st.selectbox("Vyberte tabulku", unique_users)

                    if st.form_submit_button(f"Smazat celou tabulku uživatelů"):
                        delete_user_query = f"DELETE FROM public.tasks WHERE (\"User\") = '{selected_task}';"
                        cursor.execute(delete_user_query)
                        connection.commit()

                        if cursor.rowcount > 0:
                            success_mess = st.success(f"Záznamy pro uživatele '{selected_task}' byly smazány.")
                            time.sleep(2)
                            success_mess.empty()
                            st.experimental_rerun()
                        else:
                            warning_message = st.warning(f"Nebyly nalezeny žádné záznamy pro uživatele '{selected_task}' k smazání.")
                            time.sleep(2)
                            warning_message.empty()
                            st.experimental_rerun()

                csv = tasks_df.to_csv(index=False)

                st.download_button(
                    label="Stáhnout data jako CSV",
                    data=csv.encode('utf-8'),
                    file_name='df.csv',
                    mime='text/csv',
                )

                with st.form("Delete_table_all_user_form", clear_on_submit=True):
                    st.title("Smazat ůkol všech uživatelů")
                    select_query = "SELECT * FROM public.tasks"
                    cursor.execute(select_query)
                    user_data = cursor.fetchall()
                    column_names = ["ID", "Task", "Tracking_time_tasks", "Start_time_of_tracking", "Stop_time_of_tracking", "User"]

                    tasks_df = pd.DataFrame(tasks_data, columns=column_names)
                    tasks_df['Tracking_time_tasks'] = tasks_df['Tracking_time_tasks'].apply(lambda x: str(x).split()[-1])

                    selected_task = st.selectbox("Vyberte task", tasks_df["Task"] + " - " + tasks_df["User"])

                    if st.form_submit_button("Smazat"):
                        if selected_task:
                            selected_task, username = selected_task.split(" - ")
                            delete_query = "DELETE FROM tasks WHERE (\"Tasks\") = %s AND (\"User\") = %s"
                            cursor.execute(delete_query, (selected_task, username))
                            connection.commit()
                            success_mess = st.success(f"Úkol '{selected_task}' byl úspěšně smazán z databáze uživatelem '{username}'.")
                            time.sleep(1)
                            success_mess.empty()
                            st.experimental_rerun()
                        else:
                            warning_mess = st.warning("Není žádný task k smazání.")
                            time.sleep(2)
                            warning_mess.empty()

                with st.form("Delete_user_form", clear_on_submit=True):
                    st.title("Smazat uživatel")
                    select_query = "SELECT * FROM public.\"user\""
                    cursor.execute(select_query)
                    user_data = cursor.fetchall()
                    column_names = ["ID", "Username", "Name", "Type_User","Password", "Email", "Registration_Date"]

                    user_df = pd.DataFrame(user_data, columns=column_names)
                    user_df['Registration_Date'] = user_df['Registration_Date'].apply(lambda x: str(x).split()[-1])
                    selected_user = st.selectbox("Vyberte uživatel", user_df["Username"])

                    if st.form_submit_button("Smazat uživatel"):
                        if selected_user:
                            delete_tasks_query = f"DELETE FROM public.tasks WHERE \"User\" = '{selected_user}';"
                            cursor.execute(delete_tasks_query)
                            connection.commit()

                            delete_user_query = "DELETE FROM public.\"user\" WHERE (\"Username\") = %s"
                            cursor.execute(delete_user_query, (selected_user,))
                            connection.commit()

                            success_mess = st.success(f"Uživatel '{selected_user}' byl úspěšně smazán z databáze.")
                            time.sleep(1)
                            success_mess.empty()
                            st.experimental_rerun()
                        else:
                            warning_mess = st.warning("Není vybrán žádný uživatel k smazání.")
                            time.sleep(2)
                            warning_mess.empty()

        authenticator.logout('Logout', 'main', key='unique_key')
        st.write(f"Username: {username}")

        select_query = "SELECT * FROM public.\"user\""
        cursor.execute(select_query)
        user_data = cursor.fetchall()
        column_names = ["ID", "Username", "Name", "Type_User","Password", "Email", "Registration_Date"]
        user_df = pd.DataFrame(user_data, columns=column_names)
        user_df["Username_lower"] = user_df["Username"].str.lower()

        if (user_df["Username_lower"] == username.lower()).any():
            user_type = user_df.loc[user_df["Username_lower"] == username.lower(), "Type_User"].values[0]
            st.write(f"Type user: {user_type}")
        elif username == "admin":
            st.write(f"Type user: admin")
        else:
            st.write("Uživatel nebyl nalezen")

    cursor.close()
    connection.close()

if selected_tab == "Register":
    with st.form("Registration_form", clear_on_submit=True):
        st.header("Register")
        username = st.text_input("Username*")
        name = st.text_input("Name*")
        email = st.text_input("Email*")
        password = st.text_input("Password*", type="password")
        hashed_passwords = stauth.Hasher([password]).generate()
        submit_button = st.form_submit_button("Registrovat")
        user_type = st.radio("Select User Type", ["Customer", "Agency", "Worker"])

        delka = len(password) >= 8
        mala_pismena = any(char.islower() for char in password)
        velka_pismena = any(char.isupper() for char in password)
        cislo = any(char.isdigit() for char in password)

        if submit_button:
            cursor.execute("SELECT COUNT(*) FROM public.\"user\" WHERE \"Username\" = %s OR \"Email\" = %s;", (username, email))
            existing_user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM public.\"user\" WHERE \"Email\" = %s;", (email,))
            existing_email_count = cursor.fetchone()[0]

            if not username or not name or not password or not email:
                warning = st.warning('Všechna pole jsou povinná. Prosím, vyplňte všechny údaje.')
                time.sleep(1.2)
                warning.empty()
            elif existing_user_count > 0:
                warning = st.warning('Tento uživatel již existuje.')
                time.sleep(1.2)
                warning.empty()
            elif "@" not in email:
                warning = st.warning("Email musí obsahovat znak '@'. Prosím, zadejte platný e-mail.")
                time.sleep(1.2)
                warning.empty()
            elif "." not in email.split("@")[1]:
                warning = st.warning("Email by měl obsahovat něco jako doménu (např. 'gmail.com').")
                time.sleep(1.2)
                warning.empty()
            elif existing_email_count > 0:
                warning = st.warning('Tento e-mail již existuje.')
                time.sleep(1.2)
                warning.empty()
            elif not delka:
                warning = st.warning('Heslo musí obsahovat alespoň 8 znaků.')
                time.sleep(1.2)
                warning.empty()
            elif not mala_pismena:
                warning = st.warning('Heslo musí obsahovat alespoň jedno malé písmeno.')
                time.sleep(1.2)
                warning.empty()
            elif not velka_pismena:
                warning = st.warning('Heslo musí obsahovat alespoň jedno velké písmeno.')
                time.sleep(1.2)
                warning.empty()
            elif not cislo:
                warning = st.warning('Heslo musí obsahovat alespoň jedno číslo.')
                time.sleep(1.2)
                warning.empty()
            else:
                registration_date = datetime.now()
                formatted_registration_date = registration_date.strftime("%Y-%m-%d %H:%M:%S")
                hashed_passwords = stauth.Hasher([password]).generate()
                insert_user_query = "INSERT INTO public.\"user\" (\"Username\", \"Name\", \"Type_User\", \"Password\", \"Email\", \"Registration_Date\") VALUES (%s, %s, %s, %s, %s, %s);"
                cursor.execute(insert_user_query, (username, name, user_type, hashed_passwords, email, formatted_registration_date))
                connection.commit()
                success = st.success('Registrace uživatele proběhla úspěšně')
                time.sleep(0.5)
                success.empty()

                select_user_query = "SELECT * FROM public.\"user\" WHERE \"Username\" = %s;"
                cursor.execute(select_user_query, (username,))
                user_data = cursor.fetchone()

                password = user_data[4].strip('{}').strip("''")

                new_user_data = {
                    'email': user_data[5],
                    'name': user_data[2],
                    'password': password,
                }

                with open('password.yaml', 'r') as file:
                    credentials = yaml.safe_load(file)

                credentials['credentials']['usernames'][username] = {
                    'email': new_user_data['email'],
                    'name': new_user_data['name'],
                    'password': new_user_data['password']
                }

                with open('password.yaml', 'w') as file:
                    yaml.dump(credentials, file)