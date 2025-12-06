# -*- coding: utf-8 -*-


import sqlite3

conn = sqlite3.connect("Bilticket2.2.db", timeout=10)
cur = conn.cursor()



import FreeSimpleGUI as sg
# Başlangıçta seçenek sor
choice = sg.popup_yes_no("Sign up(yes) or if you already have an account log in(no)")

if choice == "Yes": 
    layout = [
        [sg.Text('e_mail:',size=(15,1)), sg.Input(key='e_mail',size=(15,1))],
        [sg.Text('Password:', size=(15,1)), sg.Input(key='password', size=(15,1))],
        [sg.Text('Name:', size=(15,1)), sg.Input(key='first_name', size=(15,1))],
        [sg.Text('Last Name:', size=(15,1)), sg.Input(key='last_name', size=(15,1))],
        [sg.Button('Send')]
        ]

    window = sg.Window('Sign Up', layout)

    while True:
        event, values = window.read()

    

        if event == 'Send':
            parameters = (values['e_mail'], values['password'], values['first_name'], values['last_name'])

            if parameters[0] == '':
                sg.popup('E-mail cannot be empty')
            elif parameters[1] == '':
                sg.popup('Password cannot be empty')
            elif parameters[2] == '':
                sg.popup('Name cannot be empty')
            elif parameters[3] == '':
                sg.popup('Last Name cannot be empty')
            else: #AYNI E-MAİL OLMAMASI İŞİ???
                cur.execute('SELECT * FROM User WHERE e_mail = ?',parameters[0])
                row = cur.fetchone()
                if row == None:
                    # we can insert it
                    cur.execute('INSERT INTO User VALUES(?,?,?,?)', parameters)
                    sg.popup('Successfully inserted')
                else:
                    sg.popup('e_mail is already assigned')
                
        if event == sg.WIN_CLOSED:
            break
if choice == "No":
    # Login ekranı
    layout_login = [
        [sg.Text('E-mail:'), sg.Input(key='e_mail')],
        [sg.Text('Password:'), sg.Input(key='password')],
        [sg.Button('Login')]
        ]

    window_login = sg.Window('Login', layout_login)
    event, values = window_login.read()
  
    
    login_id = -1
    while True:
        event, values = window_login.read()
        if event == 'Login':
            e_mail = values['e_mail']
            password = values['password']
        
            if e_mail == '':
                sg.popup('Missin user e_mail')
            elif password == '':
                sg.popup('Missing user password')
            else:
                cur.execute("SELECT e_mail FROM User WHERE e_mail = ? AND password = ?", (e_mail, password))
                row = cur.fetchone()
                if row is None:
                    sg.popup('No such User')
                else:
                    login_id = row[0]
                    layoutt = [
                    [sg.Button('Profile')],
                    [sg.Button('Search Plays')],
                    ]

                window_main = sg.Window('Main Menu', layoutt)

                # start event loop for the next window
                while True:
                    event2, _ = window_main.read()
                    if event2 == sg.WIN_CLOSED:
                        break
                window_main.close()
                break
                




                    
            
        
    

    

 

        


            
         

window.close()
conn.close()



            










