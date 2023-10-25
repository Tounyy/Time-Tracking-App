from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import psycopg2
import time
import os

try:
    DATABASE_URL = os.environ['DATABASE_URL']
except:
    load_dotenv()
    DATABASE_URL = os.environ['DATABASE_URL']

connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

st.header('Tony Bi Be De Va Chim Be va Be Hung')
tab1, tab2, tab3 = st.tabs(["Přidat task", "Sledování časových úkolů", "Zobrazit tabulku s časem"])
    
with tab1:
    with st.form("Add_task_form", clear_on_submit=True):
        st.title("Přidat task")
        task_name = st.text_input("Název tasku")

        if st.form_submit_button("Uložit do databáze"):
            if task_name.strip() == "":
                warning_mess = st.warning("Název tasku je povinný. Prosím, doplňte ho.")
                time.sleep(3)
                warning_mess.empty()
            else:
                # Zkontrolujte, zda úkol již existuje v databázi
                check_query = "SELECT COUNT(*) FROM public.tasks WHERE \"Tasks\" = %s;"
                cursor.execute(check_query, (task_name,))
                task_exists = cursor.fetchone()[0]

                if task_exists > 0:
                    error_mess = st.error(f"Task '{task_name}' již existuje v databázi.")
                    time.sleep(3)
                    error_mess.empty()
                else:
                    # Pokud úkol neexistuje, vložte ho do databáze
                    sql_query = "INSERT INTO public.tasks (\"Tasks\") VALUES (%s);"
                    cursor.execute(sql_query, (task_name,))
                    connection.commit()
                    success_mess = st.success(f"Task '{task_name}' byl úspěšně uložen do databáze.")
                    time.sleep(3)
                    success_mess.empty()

    with st.form("Delete_task_from", clear_on_submit=True):
        st.title("Smazat task a zobrazit tabulku")

        # Získání všech úkolů z databáze
        select_query = "SELECT * FROM public.tasks;"
        cursor.execute(select_query)
        tasks_data = cursor.fetchall()

        # Vytvoření DataFrame z dat
        column_names = ["Task","Tracking_time_tasks"]
        tasks_df = pd.DataFrame(tasks_data, columns=column_names)
        selected_task = st.selectbox("Vyberte task", tasks_df["Task"])

        if st.form_submit_button("Smazat"):
            if selected_task:
                delete_query = "DELETE FROM tasks WHERE (\"Tasks\") = %s"
                cursor.execute(delete_query, (selected_task,))
                # Commit změn do databáze
                connection.commit()
                success_mess = st.success(f"task ''{selected_task} je smazáno z databáze.")
                time.sleep(2)
                success_mess.empty()
                st.experimental_rerun()
            else:
                warning_mess = st.warning("Není žádný task k smazání.")
                time.sleep(3)
                warning_mess.empty()
        
        if st.form_submit_button("Zobrazit tabulku"):
            tasks_df.drop(columns=['Tracking_time_tasks'], inplace=True)
            st.dataframe(tasks_df, hide_index=True, use_container_width=True)

with tab2:
    select_querys = "SELECT * FROM public.tasks;"
    cursor.execute(select_querys)
    tasks_data_2 = cursor.fetchall()
    column_names_2 = ["Task","Tracking_time_tasks"]
    tasks_df_1 = pd.DataFrame(tasks_data_2, columns=column_names_2)
    tasks_df_2 = tasks_df_1[tasks_df_1["Tracking_time_tasks"].isna()]

    selected_task = st.selectbox("Vyberte task", tasks_df_2["Task"])
    start_button = st.button('Start')
    stop_button = st.button('Stop')

    if st.button("Reset"):
        st.session_state.start_time = None
        st.session_state.elapsed_time = timedelta()
        time.sleep(3)
        st.experimental_rerun()

    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

    if 'elapsed_time' not in st.session_state:
        st.session_state.elapsed_time = timedelta()

    if start_button:
        st.session_state.start_time = datetime.now()

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

        # Vytvořte prázdný kontejner
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

            # Aktualizujte prázdný kontejner s novým časem
            time_container.text(f'Časovač běží: {formatted_time}')
            time.sleep(1)

    if selected_task:
        if st.button("Uložit čas do databáze"):
            # Smazání starých dat spojených s vybraným úkolem
            delete_query = "DELETE FROM public.tasks WHERE \"Tasks\" = %s;"
            cursor.execute(delete_query, (selected_task,))
            connection.commit()

            # Získejte změřený čas a převeďte ho na žádaný formát
            measured_time = st.session_state.elapsed_time
            formatted_time = f"{measured_time.seconds // 3600:02d}:{(measured_time.seconds // 60) % 60:02d}:{measured_time.seconds % 60:02d}"

            # Přidejte kód pro uložení vybraného úkolu a změřeného času do databáze
            insert_query = "INSERT INTO public.tasks (\"Tasks\", \"Tracking_time_tasks\") VALUES (%s, %s);"
            cursor.execute(insert_query, (selected_task, formatted_time))
            connection.commit()
            success_mess = st.success(f"Čas byl uložen k úkolu '{selected_task}' s hodnotou {formatted_time}.")

            # Ručně resetujte hodnoty v session_state
            st.session_state.start_time = None
            st.session_state.elapsed_time = timedelta()

            # Obnovte aplikaci po 3 sekundách
            time.sleep(3)
            st.experimental_rerun()

with tab3:
    # Fetch data from the database
    select_query = "SELECT * FROM public.tasks;"
    cursor.execute(select_query)
    tasks_data = cursor.fetchall()
    column_names = ["Task", "Tracking_time_tasks"]
    tasks_df = pd.DataFrame(tasks_data, columns=column_names)

    tasks_df['Tracking_time_tasks'] = tasks_df['Tracking_time_tasks'].apply(lambda x: str(x).split()[-1])
    st.dataframe(tasks_df, use_container_width=True, hide_index=True)
    
cursor.close()
connection.close()