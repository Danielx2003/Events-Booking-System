import tkinter as tk
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import re
import random
from datetime import date
from datetime import datetime
import os
import hashlib
import smtplib, ssl
import requests


#BASE
class Base(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs) #inherits all tkinter module attributes

        tk.Tk.wm_title(self, "Cinnamon Photography")

        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.queue = []

        for F in (HomeScreen, LogIn, AttendantPage, CustomerPage, CustomerRegister, AttendantRegister, UserConfirmation, AttendantConfirmation, BookingForm, AttendantMenu, CustomerMenu, OwnerMenu):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(BookingForm) #shows screen passed as parameter

    def show_frame(self, cont):
        frame = self.frames[cont] #frame stores datavalue (frame) associated with the key
        frame.tkraise() #raises frame to the top

    def AddToQueue(self, cont):
        self.queue.append(cont)

    def PopFromQueue(self, cont):
        poppedFrame = self.queue[-1]
        self.queue.pop()
        self.show_frame(poppedFrame)

    def ClearQueue(self, cont): #clears queue
        self.queue.clear()


#HOME SCREEN
class HomeScreen(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent) #inherits all tkinter attributes

        self.f = font.nametofont('TkTextFont')
        welcomeText = tk.Label(self, text="Welcome To Cinnamon Photography",font=(self.f, 20))
        welcomeText.place(relx=0.05, rely=0.05)


        #BUTTONS
        OwnerButton = ttk.Button(self, text="Owner", width=18,
                                  command=lambda:[controller.AddToQueue(HomeScreen), controller.show_frame(LogIn)]) #shows log in frame and adds Homescreen to the queue
        OwnerButton.place(relx=0.2,rely=0.8,anchor=CENTER)

        AttendantButton = ttk.Button(self, text="Attendant",width=18,
                                     command=lambda: [controller.AddToQueue(HomeScreen),controller.show_frame(AttendantPage)])
        AttendantButton.place(relx=0.5,rely=0.8,anchor=CENTER)

        CustomerButton = ttk.Button(self, text="Customer",width=18,
                                    command=lambda: [controller.AddToQueue(HomeScreen),controller.show_frame(CustomerPage)])
        CustomerButton.place(relx=0.8,rely=0.8,anchor=CENTER)




#CLIENT LOG IN
class LogIn(tk.Frame): #inherts frame, which makes a blank frame to add widgets to

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #self.DropOwnersTable()
        self.CreateOwnersTable()
        #self.InsertOwnersValues()

        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.35, anchor=CENTER, width=300, height=200)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        self.f = font.nametofont('TkTextFont')
        loginTitle = tk.Label(self.textFrame, text="Owner Login", font=(self.f, 14))
        loginTitle.place(relx=0.40, rely=0.02)

        usernameLabel = ttk.Label(self.textFrame, text="Username ", font=(self.f, 11))
        usernameLabel.place(relx=0.05, rely=0.25)

        passwordLabel = ttk.Label(self.textFrame, text="Password ", font=(self.f, 11))
        passwordLabel.place(relx=0.05, rely=0.4)


        #BUTTONS
        loginButton = ttk.Button(self, text="Login",
                            command=lambda: self.CheckDetails(self.userEntry.get(), self.passEntry.get(), controller), width=12)
        loginButton.place(relx=0.5,rely=0.8,anchor=CENTER)

        homeButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:[self.ClearEntries(),controller.ClearQueue(LogIn),controller.show_frame(HomeScreen)])
        homeButton.place(relx=0.05, rely=0)

        backButton = ttk.Button(self, text="<-", width=2,
                                command=lambda:[self.ClearEntries(),controller.PopFromQueue(LogIn)])
        backButton.place(relx=0, rely=0)

        #ENTRYS

        self.userEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.userEntry.place(relx=0.35, rely=0.25)

        self.passEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.passEntry.place(relx=0.35, rely=0.4)

    def GetHashedPassword(self, password, userSalt):
        try:
            hashedValue = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),userSalt, 310000) #hashes password with the usersalt in db
            return hashedValue
        except:
            return "Error"


    def CheckDetails(self, username, password, controller):
        confirmed = False
        assert len(password) != 0, "Password length is 0." #informs that the password is of length 0
        result = self.GetOwnerDetails()
        assert len(result) != 0, "No owner details are stored." #informs that no owner details are stored

        for details in result:
            hashedPassword = self.GetHashedPassword(password,details[2]) #passes password and salt from db
            if username == details[0] and hashedPassword == details[1]: #if password stored = hashedpassword
                confirmed = True

        if confirmed:
            result= self.GetOwnerEmail(username) #gets owner email associated with that username
            self.GenerateCode(result) #generates 6 digit code, and stores in db in owner username record
            self.WriteOwnerUsernameToFile(username) #writes owner username to file
            self.ClearEntries()
            controller.AddToQueue(LogIn)
            controller.show_frame(UserConfirmation)
        else:
            messagebox.showerror("Details", "Details do not match.")

    def WriteOwnerUsernameToFile(self, username):
        file = open("UsernameInUse.txt","w")
        file.write(username)
        file.close()


    def GetOwnerDetails(self):
        #gets owner details
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT owner_username, owner_password, owner_salt FROM Owners
            """

            cursor.execute(sql)
            result = cursor.fetchall()
        return result

    def GetOwnerEmail(self, username):
        #gets owner email associated with owner username
        with sqlite3.connect("NEA_Customer.db")as db:#establish connection with db
            cursor = db.cursor()
            values = (username,)
            sql = """SELECT owner_email FROM Owners
            WHERE owner_username = ?;
            """

            cursor.execute(sql, values)
            result = cursor.fetchall()
        return result

    def InsertOwnersValues(self):
        #inserts owner details into db, must be done manually because no owner reg option
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            salt, hashedPassword = self.GetHashedPassword("TestPass01")
            sql = """INSERT INTO Owners(owner_fname, owner_lname, owner_username, owner_email, owner_password, owner_salt)
                    VALUES(?, ?, ?, ?, ?, ?)"""

            cursor.execute(sql, ("TestName", "Lastname", "TLastname123456", "testemail@gmail.com", hashedPassword, salt))
            db.commit()

    def GenerateCode(self, email):
        #Generate 6 numbers
        numbers = ""
        for i in range(6):
            numbers += str(random.randint(0, 9))
        self.UpdateOwnerCode(numbers) #updates owner_code attribute with the new code
        self.SendCodeForOwner(numbers, email) #emails code to email

    def UpdateOwnerCode(self, code):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            ownerUsername = self.GetClientUsernameFromFile()
            values = (code, ownerUsername)
            sql = """UPDATE Owners
            SET owner_code = ?
            WHERE owner_username = ?;
            """
            db.commit()
            cursor.execute(sql, values)

    def GetClientUsernameFromFile(self):
        file = open("OwnerUsernameFile.txt", "r")
        ownerUsername = file.read()
        file.close()

        return ownerUsername


    def SendCodeForOwner(self, code, reciever_email):
        port = 465  # For SSL
        smtpServer = "smtp.gmail.com" #email sent from gmail
        subject = 'Code for Cinnamon Photography'
        body = f'Your code for Cinnamon Photography is : {code}'

        message = f'Subject: {subject}\n\n{body}'
        file = open("EmailPassword.txt","r")
        emailPassword = file.read()
        file.close()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtpServer, port, context=context) as server: #connect to smtp server
                server.login("noreplycinnamonphotography@gmail.com", emailPassword) #log into email
                server.sendmail("noreplycinnamonphotography@gmail.com", reciever_email, message) #send email
        except:
            pass

    def CreateOwnersTable(self):
        #creates owners table for the database
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """CREATE TABLE IF NOT EXISTS Owners
            (
            owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_email TEXT NOT NULL,
            owner_fname TEXT,
            owner_lname TEXT,
            owner_username TEXT,
            owner_password TEXT,
            owner_code INTEGER,
            owner_salt TEXT
            );
  """
            cursor.execute(sql)

    def DropOwnersTable(self):
        #drops owners table
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            try:
                sql = """DROP TABLE Owners;
                      """
                cursor.execute(sql)
            except:
                pass

    def ClearEntries(self):
        #deletes values in the entries
        try:
            self.userEntry.delete(0, END)
        except:
            pass
        try:
            self.passEntry.delete(0, END)
        except:
            pass



#CUSTOMER PAGE
class CustomerPage(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.35, anchor=CENTER, width=300, height=200)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        self.f = font.nametofont('TkTextFont')
        loginTitle = tk.Label(self.textFrame, text="Customer Login", font=(self.f, 14))
        loginTitle.place(relx=0.40, rely=0.02)

        usernameLabel = ttk.Label(self.textFrame, text="Username ", font=(self.f, 11))
        usernameLabel.place(relx=0.05, rely=0.25)

        passwordLabel = ttk.Label(self.textFrame, text="Password ", font=(self.f, 11))
        passwordLabel.place(relx=0.05, rely=0.4)

        #BUTTONS
        loginButton = ttk.Button(self, text="Login",
                            command=lambda: self.CheckDetails(self.userEntry.get(), self.passEntry.get(), controller), width=12)
        loginButton.place(relx=0.4,rely=0.8,anchor=CENTER)

        registerButton = ttk.Button(self, text="Register",
                                    command=lambda: [self.ClearEntries(),controller.AddToQueue(CustomerPage),controller.show_frame(CustomerRegister)])
        registerButton.place(relx=0.6, rely=0.8, anchor=CENTER)

        homeButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:[self.ClearEntries(),controller.ClearQueue(CustomerPage),controller.show_frame(HomeScreen)])
        homeButton.place(relx=0.05, rely=0)

        backButton = ttk.Button(self, text="<-", width=2,
                                command=lambda:[self.ClearEntries(),controller.PopFromQueue(CustomerPage)])
        backButton.place(relx=0, rely=0)

        #ENTRYS
        self.userEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.userEntry.place(relx=0.35, rely=0.25)

        self.passEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.passEntry.place(relx=0.35, rely=0.4)

    def ClearEntries(self):
        #deletes all values in entries
        self.userEntry.delete(0, END)
        self.passEntry.delete(0, END)

    def GetHashedPassword(self, password, userSalt):
        try:
            hashedValue = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),userSalt, 310000) #hashes pasword with usersalt to see if they match
            return hashedValue
        except:
            return "Error"

    def CheckDetails(self, username, password, controller):
        confirmed = False
        result = self.GetCustomerDetails(username)

        for details in result:
            hashedPassword = self.GetHashedPassword(password,details[1])
            if details[0] == hashedPassword: #if password in db = hashed password
                confirmed = True

        if confirmed:
            self.WriteUsernameToFile(username)
            controller.show_frame(CustomerMenu)
        else:
            messagebox.showerror("Details", "Details do not match.")

    def GetCustomerDetails(self, username):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (username,)
            sql = """SELECT customer_password, customer_salt FROM Customers
            WHERE customer_username = ?
                """
            cursor.execute(sql, values)
            result = cursor.fetchall()

        return result

    def WriteUsernameToFile(self, username):
        file = open("UsernameInUse.txt","w")
        file.write(username)
        file.close()



#ATTENDANT PAGE
class AttendantPage(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.35, anchor=CENTER, width=300, height=200)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        self.f = font.nametofont('TkTextFont')
        loginTitle = tk.Label(self.textFrame, text="Attendant Login", font=(self.f, 14))
        loginTitle.place(relx=0.40, rely=0.02)

        usernameLabel = ttk.Label(self.textFrame, text="Username ", font=(self.f, 11))
        usernameLabel.place(relx=0.05, rely=0.25)

        passwordLabel = ttk.Label(self.textFrame, text="Password ", font=(self.f, 11))
        passwordLabel.place(relx=0.05, rely=0.4)

        #BUTTONS
        loginButton = ttk.Button(self, text="Login",
                                 command=lambda: self.CheckDetails(self.userEntry.get(), self.passEntry.get(), controller), width=12)
        loginButton.place(relx=0.4,rely=0.8,anchor=CENTER)

        registerButton = ttk.Button(self, text="Register",
                                    command=lambda: [self.ClearEntries(),controller.AddToQueue(AttendantPage),controller.show_frame(AttendantRegister)])
        registerButton.place(relx=0.6, rely=0.8,anchor=CENTER)

        homeButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:[self.ClearEntries(),controller.ClearQueue(AttendantPage),controller.show_frame(HomeScreen)])
        homeButton.place(relx=0.05, rely=0)

        backButton = ttk.Button(self, text="<-", width=2,
                                command=lambda:[self.ClearEntries(),controller.PopFromQueue(AttendantPage)])
        backButton.place(relx=0, rely=0)

        #ENTRYS

        self.userEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.userEntry.place(relx=0.35, rely=0.25)

        self.passEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.passEntry.place(relx=0.35, rely=0.4)

    def ClearEntries(self):
        #deletes all values in these entries
        try:
            self.userEntry.delete(0, END)
        except:
            pass
        try:
            self.passEntry.delete(0, END)
        except:
            pass

    def GetHashedPassword(self, password, userSalt):
        try:
            hashedValue = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),userSalt, 310000) #hashes passowrd with the user salt
            return hashedValue
        except:
            return "Error"

    def CheckDetails(self, username, password, controller):
        confirmed = False
        result = self.GetAttendantDetails()

        for details in result: #loops through attendant details
            hashedPassword = self.GetHashedPassword(password,details[2]) #hash password with salt in db
            if username == details[0] and hashedPassword == details[1]: #if username matches stored username, and password matches stored password
                confirmed = True

        if confirmed:
            result = self.GetAttendantEmail(username)
            self.WritAttendantUsernameToFile(username)
            self.GenerateCode(result, username)
            self.ClearEntries()
            controller.show_frame(AttendantConfirmation)
        else:
            messagebox.showerror("Details", "Details do not match.")

    def WritAttendantUsernameToFile(self, username):
        file = open("UsernameInUse.txt","w")
        file.write(username)
        file.close()

    def GetAttendantDetails(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT attendant_username, attendant_password, attendant_salt FROM Attendants
            """

            cursor.execute(sql)
            result = cursor.fetchall()
        return result

    def GetAttendantEmail(self, username):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (username,)
            sql = """SELECT attendant_email FROM Attendants
                        WHERE attendant_username = ?;
                        """

            cursor.execute(sql, values)
            result = cursor.fetchall()
        return result


    def GenerateCode(self, email, username):
        #Generate numbers
        numbers = ""
        for i in range(6):
            numbers += str(random.randint(0, 9))
        self.UpdateAttendantCode(numbers, username)
        self.SendCodeForVerification(email, numbers)

    def UpdateAttendantCode(self, numbers, username):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            global attendantUsernameGlobal #fix this soon by using the file that stores the current username in use
            attendantUsernameGlobal = username
            values = (numbers, attendantUsernameGlobal)
            sql = """UPDATE Attendants
            SET attendant_code = ?
            WHERE attendant_username = ?;
            """
            db.commit()
            cursor.execute(sql, values)

    def SendCodeForVerification(self, reciever_email, code):
        port = 465  # For SSL
        smtpServer = "smtp.gmail.com"
        subject = 'Code for Cinnamon Photography'
        body = f'Your code for Cinnamon Photography is : {code}'

        message = f'Subject: {subject}\n\n{body}'
        file = open("EmailPassword.txt","r")
        emailPassword = file.read()
        file.close()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtpServer, port, context=context) as server: #connect to smpt server
                server.login("noreplycinnamonphotography@gmail.com", emailPassword) #log into email
                server.sendmail("noreplycinnamonphotography@gmail.com", reciever_email, message) #send email to recpient
                return True
        except:
            return False


#CUSTOMER REGISTER
class CustomerRegister(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #self.DropCustomersTable()
        self.CreateCustomersTable()


        #BACK/FORWARD BUTTON
        homeButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:[self.ClearEntries(),controller.ClearQueue(CustomerRegister),controller.show_frame(HomeScreen)])
        homeButton.place(relx=0.05, rely=0)

        backButton = ttk.Button(self, text="<-", width=2,
                                command=lambda:[self.ClearEntries(),controller.PopFromQueue(CustomerRegister)])
        backButton.place(relx=0, rely=0)


        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.35, anchor=CENTER, width=400, height=250)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        f = font.nametofont('TkTextFont')
        loginTitle = tk.Label(self.textFrame, text= "Customer Registration",font=(f, 14))
        loginTitle.place(relx=0.35, rely=0.1)

        emailLabel = ttk.Label(self.textFrame, text="             Email ",font=(f, 11))
        emailLabel.place(relx=0.1, rely=0.25)

        firstNameLabel = ttk.Label(self.textFrame, text="    First Name ",font=(f, 11))
        firstNameLabel.place(relx=0.1, rely=0.4)

        lastNameLabel = ttk.Label(self.textFrame, text="    Last Name ",font=(f, 11))
        lastNameLabel.place(relx=0.1, rely=0.55)

        passwordLabel = ttk.Label(self.textFrame, text="     Password ",font=(f, 11))
        passwordLabel.place(relx=0.1, rely=0.7)

        password2Label = ttk.Label(self.textFrame, text="Re-enter Password",font=(f, 11))
        password2Label.place(relx=0.01, rely=0.85)

        #BUTTONS
        registerButton = ttk.Button(self, text="Register",
                            command=lambda: self.CheckPasswordsMatch(self.fNameEmtry.get(), self.lNameEntry.get(), self.emailEntry.get()
                            ,self.pass1Entry.get(), self.pass2Entry.get(), controller),
                                    width=12)
        registerButton.place(relx=0.5,rely=0.8,anchor=CENTER)

        #ENTRYS

        self.emailEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.emailEntry.place(relx=0.35, rely=0.25)

        self.fNameEmtry = tk.Entry(self.textFrame, width=30, bd=2)
        self.fNameEmtry.place(relx=0.35, rely=0.4)

        self.lNameEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.lNameEntry.place(relx=0.35, rely=0.55)

        self.pass1Entry = tk.Entry(self.textFrame, width=30, bd=2)
        self.pass1Entry.place(relx=0.35, rely=0.7)

        self.pass2Entry = tk.Entry(self.textFrame, width=30, bd=2)
        self.pass2Entry.place(relx=0.35, rely=0.85)

        #INPUT ERRORS

        self.passwordError = tk.Label(self, text="", fg="red")
        self.passwordError.place(relx=0.35, rely=0.63)

    def ClearEntries(self):
        #delete any values in these enteries
        self.emailEntry.delete(0, END)
        self.fNameEmtry.delete(0, END)
        self.lNameEntry.delete(0, END)
        self.pass1Entry.delete(0, END)
        self.pass2Entry.delete(0, END)

    def helpWindow(self, parent):
        #creates a help window that guides the user on what their registration form should contain
        newWindow = Toplevel(parent)
        newWindow.geometry("350x200")
        newWindow.title("Help")
        label = ttk.Label(newWindow, text="Please enter a valid email.\n\nAll names must be correctly capitalised.\n\n")
        label.place(relx=0.1, rely=0.2)

    def CheckPasswordLength(self, pass1):
        if len(pass1) < 6:
            messagebox.showerror("Password Length", "Passwords must be atleast 6 characters.")
            return 1
        return 0

    def CheckPasswordMatch(self, pass1, pass2):
        if pass1 != pass2:
            messagebox.showerror("Passwords", "Passwords must match.")
            return 1
        else:
            return 0

    def CheckNameLength(self, fname, lname):
        if re.search(r"[0-9]", fname) is not None: #if no numbers in fname
            return 1
        if re.search(r"[0-9]", lname) is not None: #if no numbers in lname
            return 1

        if len(fname) < 1 or len(lname) < 1: #if fname or lname has been left blank
            messagebox.showerror("Name", "Name cannot be left blank.")
            return 1
        else:
            return 0

    def CheckEmailIsValid(self, email):
        isEmailValid = self.isvalidEmail(email) #stores result on if email is a valid format
        if isEmailValid == False:
            messagebox.showerror("Email", "This email is not allowed.")
            return 1
        result = self.GetCustomerEmail()

        for details in result: #loops through customer emails in db
            if email == details[0]:
                emailExists = True
        try:
            if emailExists:
                messagebox.showerror("Email", "Email already in use.")
                return 1
        except:
            pass
        return 0

    def isvalidEmail(self, email):
        pattern = "^\S+@\S+\.\S+$"
        object = re.search(pattern, email)
        try:
            if object.string == email:
                return True
        except:
            return False

    def CheckPasswordsMatch(self, fname, lname, email, pass1, pass2, controller):
        count = 0
        count += self.CheckPasswordLength(pass1)
        count += self.CheckPasswordMatch(pass1, pass2)
        count += self.CheckNameLength(fname, lname)
        count += self.CheckEmailIsValid(email)

        passStrength = self.CheckPasswordStrength(pass1)
        if not passStrength: #if password does not contain capital letter or number
            self.passwordError.configure(text="Your password is not secure.")
        else:
            self.passwordError.configure(text="")

        if count == 0 and passStrength:
            fname = fname.title() #make first letter of fname capital
            lname = lname.title() #make first letter of lname capital
            username = self.GenerateCustomerUsername(fname, lname)
            messagebox.showinfo("Username","Check your email for your username.")
            self.SendCustomerEmail(email, username)

            #checks if email exists
            self.InsertCustomersInfo(fname, lname, email, pass1, username)
            controller.AddToQueue(CustomerRegister)
            controller.show_frame(HomeScreen)

    def GenerateCustomerUsername(self, fname, lname):
        numbers = ""
        for i in range(6):
            numbers += str(random.randint(0, 9))
        username = "C-" + fname[0] + lname + numbers #makes username in customer format
        return username

    def GetCustomerEmail(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT customer_email FROM Customers
            """

            cursor.execute(sql)
            result = cursor.fetchall()
        return result

    def SendCustomerEmail(self, email, username):
        result = self.sendEmailFunction(email, username)
        return result

    def sendEmailFunction(self, reciever_email, username):
        port = 465  # For SSL
        smtpServer = "smtp.gmail.com"
        subject = 'Username for Cinnamon Photography'
        body = f'Your username for Cinnamon Photography is : {username}'

        message = f'Subject: {subject}\n\n{body}'
        file = open("EmailPassword.txt","r")
        emailPassword = file.read()
        file.close()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtpServer, port, context=context) as server: #connects to smpt server
                server.login("noreplycinnamonphotography@gmail.com", emailPassword) #logs into email
                server.sendmail("noreplycinnamonphotography@gmail.com", reciever_email, message) #sends email to recipient
                return True
        except:
            return False

    def CheckPasswordStrength(self, password):
        count = 0
        if re.search(r"[A-Z]", password) is None: #Checks if the password has an capital letters
            count += 1

        if re.search(r"[a-z]", password) is None: #Checks if the password has any lower case letters
            count += 1

        if re.search(r"\d", password) is None: #Checks if the password has any numbers
            count += 1

        if count == 0:
            return True
        else:
            return False



    def CreateCustomersTable(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """CREATE TABLE IF NOT EXISTS Customers
              (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_email TEXT NOT NULL,
                customer_fname TEXT,
                customer_lname TEXT,
                customer_username TEXT,
                customer_password TEXT,
                customer_salt TEXT
              );
              """
            #
            cursor.execute(sql)

    def GetHashedPassword(self, password):
        salt = os.urandom(32) #generate random 32 length string
        try:
            hashedValue = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),salt, 310000) #hash password with salt generated
            return salt, hashedValue
        except:
            return "Error", "Error"

    def InsertCustomersInfo(self, fname, lname, email, password, username):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            salt, hashed = self.GetHashedPassword(password)
            sql = """INSERT INTO Customers(customer_fname, customer_lname, customer_username, customer_email, customer_password, customer_salt)
            VALUES(?, ?, ?, ?, ?, ?)"""

            cursor.execute(sql, (fname, lname, username, email, hashed, salt))

    def DropCustomersTable(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            try:
                sql = """DROP TABLE Customers;
                      """
                cursor.execute(sql)
            except:
                pass




#ATTENDATNT REGISTER
class AttendantRegister(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #self.DropAttendantsTable()
        self.CreateAttendantsTable()

        #BACK/FORWARD BUTTON
        homeButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:[self.ClearEntries(),controller.ClearQueue(AttendantRegister),controller.show_frame(HomeScreen)])
        homeButton.place(relx=0.05, rely=0)

        backButton = ttk.Button(self, text="<-", width=2,
                                command=lambda:[self.ClearEntries(),controller.PopFromQueue(AttendantRegister)])
        backButton.place(relx=0, rely=0)

        helpButton = ttk.Button(self, text="?", width=2,
                                command=lambda:self.helpWindow(parent))
        helpButton.place(relx=0.96, rely=0)


        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.4, anchor=CENTER, width=400, height=350)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        f = font.nametofont('TkTextFont')
        loginTitle = tk.Label(self.textFrame, text= "Attendant Registration",font=(f, 14))
        loginTitle.place(relx=0.38, rely=0.02)

        emailLabel = ttk.Label(self.textFrame, text="             Email ",font=(f, 11))
        emailLabel.place(relx=0.1, rely=0.15)

        firstNameLabel = ttk.Label(self.textFrame, text="     First Name ",font=(f, 11))
        firstNameLabel.place(relx=0.1, rely=0.28)

        lastNameLabel = ttk.Label(self.textFrame, text="     Last Name ",font=(f, 11))
        lastNameLabel.place(relx=0.1, rely=0.41)

        passwordLabel = ttk.Label(self.textFrame, text="      Password ",font=(f, 11))
        passwordLabel.place(relx=0.1, rely=0.54)

        password2Label = ttk.Label(self.textFrame, text="Re-enter Password",font=(f, 11))
        password2Label.place(relx=0.01, rely=0.67)

        postcodeLabel = ttk.Label(self.textFrame, text="      Postcode", font=(f,11))
        postcodeLabel.place(relx=0.09, rely=0.8)

        codeLabel = ttk.Label(self.textFrame, text="                      Code",font=(f, 11))
        codeLabel.place(relx=0.01, rely=0.93)

        #BUTTONS
        registerButton = ttk.Button(self, text="Register",
                            command=lambda: self.CheckPasswordsMatch(self.fNameEmtry.get(), self.lNameEntry.get(), self.emailEntry.get()
                            ,self.pass1Entry.get(), self.pass2Entry.get(), controller, self.codeEntry.get(), self.postcodeEntry.get()),
                                    width=16)
        registerButton.place(relx=0.5,rely=0.84,anchor=CENTER)

        generateCodeButton = ttk.Button(self, text="Generate Code",
                                  command=lambda: self.GenerateCode())
        generateCodeButton.place(relx=0.5, rely=0.78, anchor=CENTER)

        #ENTRYS

        self.emailEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.emailEntry.place(relx=0.35, rely=0.15)

        self.fNameEmtry = tk.Entry(self.textFrame, width=30, bd=2)
        self.fNameEmtry.place(relx=0.35, rely=0.28)

        self.lNameEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.lNameEntry.place(relx=0.35, rely=0.41)

        self.pass1Entry = tk.Entry(self.textFrame, width=30, bd=2)
        self.pass1Entry.place(relx=0.35, rely=0.54)

        self.pass2Entry = tk.Entry(self.textFrame, width=30, bd=2)
        self.pass2Entry.place(relx=0.35, rely=0.67)

        self.postcodeEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.postcodeEntry.place(relx=0.35, rely=0.8)

        self.codeEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.codeEntry.place(relx=0.35, rely=0.93)

        #INPUT ERRORS

        self.passwordError = tk.Label(self, text="", fg="red")
        self.passwordError.place(relx=0.35, rely=0.95)

    def ClearEntries(self):
        #deletes all values from all the entries
        self.emailEntry.delete(0, END)
        self.fNameEmtry.delete(0, END)
        self.lNameEntry.delete(0, END)
        self.pass1Entry.delete(0, END)
        self.pass2Entry.delete(0, END)
        self.codeEntry.delete(0, END)
        self.postcodeEntry.delete(0, END)

    def helpWindow(self, parent):
        #creates help window that guides the user through what to enter for attendant reg form
        newWindow = Toplevel(parent)
        newWindow.geometry("350x200")
        newWindow.title("Help")
        label = ttk.Label(newWindow, text="Please enter a valid email.\n\nAll names must be correctly capitalised.\n\nPressing 'Generate Code' Button will send an email\nwith a code to allow you to register.\n\nThe code will be emailed to your supervisor,\nand this code will be used to verify your registration.\n\nYour supervisor should be on hand to give\nyou this code.")
        label.place(relx=0.1, rely=0.05)

    def CheckPasswordLength(self, pass1):
        if len(pass1) < 6:
            messagebox.showerror("Password Length", "Passwords must be atleast 6 characters.")
            return 1
        else:
            return 0

    def CheckPasswordMatch(self, pass1,pass2):
        if pass1 != pass2:
            messagebox.showerror("Passwords", "Passwords must match.")
            return 1
        else:
            return 0

    def CheckNameLength(self, fname, lname):
        if re.search(r"[0-9]", fname) is not None: #if no numbers in fname
            return 1
        if re.search(r"[0-9]", lname) is not None: #if no nunbers in lname
            return 1

        if len(fname) < 1 or len(lname) < 1:
            messagebox.showerror("Name", "Name cannot be left blank.")
            return 1
        else:
            return 0

    def CheckEmailExists(self, result, count, email):
        for details in result: #loops through emails
            if email == details[0]: #if email is in db
                count += 1
                emailExists = True
        try:
            if emailExists:
                messagebox.showerror("Email", "Email already in use.")
        except:
            pass

        return count

    def ShowNextFrame(self, result, fname, lname, email, pass1, username, controller, postcode):
        # checks if email exists
        if result == True:
            self.InsertAttendantsValues(fname, lname, email, pass1, username, postcode)
            messagebox.showinfo("Username", "Check your emails for your username.")
            controller.AddToQueue(AttendantRegister)
            controller.show_frame(HomeScreen)
        else:
            messagebox.showerror("Email", "Email does not exist.")

    def CheckPostcodeIsValid(self, postcode):
        with open("apiKey.txt") as file:
            apikey = file.read()  # gets api key

        url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"
        # link generated
        r = requests.get(url + "origins=" + "CM133SB" + "&destinations=" + postcode + "&key=" + apikey)
        status = r.json()["rows"][0]["elements"][0]["status"]
        if status != "OK":
            messagebox.showerror("Postcode", "Please enter a valid postcode.")
            return 1
        else:
            return 0

    def CheckPasswordsMatch(self, fname, lname, email, pass1, pass2, controller, code, postcode):
        count = 0
        count += self.CheckPasswordLength(pass1)
        count += self.CheckPasswordMatch(pass1, pass2)
        count += self.CheckNameLength(fname, lname)
        count += self.CheckPostcodeIsValid(postcode)
        result = self.GetAttendantEmail()
        count = self.CheckEmailExists(result, count, email)

        passStrength = self.CheckPasswordStrength(pass1)
        if not passStrength:
            self.passwordError.configure(text="Your password is not secure.")
        else:
            self.passwordError.configure(text="")


        codeCorrect = self.CheckCodeMatches(code)

        if count == 0 and passStrength == True and codeCorrect == True:
            fname = fname.title() #adds capital letter to first letter in fname
            lname = lname.title() #adds capital letter to first letter in lname

            username = self.GenerateAttendantUsername(fname, lname)
            result = self.SendAttendantEmail(email, username)
            self.ShowNextFrame(result, fname, lname, email, pass1, username, controller, postcode)

    def GetAttendantEmail(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT attendant_email FROM Attendants
            """

            cursor.execute(sql)
            result = cursor.fetchall()
        return result #returns all attendant emails in db

    def SendAttendantEmail(self, email, username):
        result = self.sendEmailFunction(email, username)
        return result

    def sendEmailFunction(self, reciever_email, username):
        port = 465  # For SSL
        smtpServer = "smtp.gmail.com"
        subject = 'Username for Cinnamon Photography'
        body = f'Your username for Cinnamon Photography is : {username}'

        message = f'Subject: {subject}\n\n{body}'

        file = open("EmailPassword.txt","r")
        emailPassword = file.read()
        file.close()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtpServer, port, context=context) as server: #connects to smpt server
                server.login("noreplycinnamonphotography@gmail.com", emailPassword) #logs into email
                server.sendmail("noreplycinnamonphotography@gmail.com", reciever_email, message) #sends email
                return True
        except:
            return False

    def GenerateAttendantUsername(self, fname, lname):
        numbers = ""
        for i in range(6):
            numbers += str(random.randint(0, 9))
        username = "A-" + fname[0] + lname + numbers
        return username

    def CheckPasswordStrength(self, password):
        count = 0
        if re.search(r"[A-Z]", password) is None: #Checks if the password has an capital letters
            count += 1

        if re.search(r"[a-z]", password) is None: # Checks if the password has any lower case letters
            count += 1

        if re.search(r"\d", password) is None: #Checks if the password has any numbers
            count += 1

        if count == 0:
            return True
        else:
            return False

    def CheckCodeMatches(self, code):
        result = self.GetOwnerCode()

        if str(result[0]) == str(code): #if code in entry matches code in db
            return True
        else:
            return False

    def GetOwnerCode(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT owner_code FROM Owners
            """
            cursor.execute(sql)
            result = cursor.fetchone()
        return result

    def CreateAttendantsTable(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """CREATE TABLE IF NOT EXISTS Attendants
              (
                attendant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendant_email TEXT NOT NULL,
                attendant_fname TEXT,
                attendant_lname TEXT,
                attendant_username TEXT,
                attendant_password TEXT,
                attendant_code INTEGER,
                attendant_salt TEXT,
                attendant_postcode TEXT,
                attendant_supervisor INTEGER,
                FOREIGN KEY(attendant_supervisor) REFERENCES Owners(owner_id)
              );
              """
            #
            cursor.execute(sql)

    def GetHashedPassword(self, password):
        try:
            salt = os.urandom(32) #generate random 32 long string
            hashedValue = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),salt, 310000) #hashes password with salt
            return salt, hashedValue
        except:
            return "Error", "Error"


    def InsertAttendantsValues(self, fname, lname, email, password, username, postcode):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            salt, hashedPassword = self.GetHashedPassword(password)
            supervisorID = self.GetSupervisorID()
            sql = """INSERT INTO Attendants(attendant_fname, attendant_lname, attendant_username, attendant_email, attendant_password, attendant_salt, attendant_postcode, attendant_supervisor)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)"""

            cursor.execute(sql, (fname, lname, username, email, hashedPassword, salt, postcode, supervisorID))
            db.commit()

    def GetSupervisorID(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT COUNT(owner_id) FROM Owners;
                  """
            cursor.execute(sql)
            result = cursor.fetchall()
        supervisorID = random.randint(1,result[0][0])
        return supervisorID

    def DropAttendantsTable(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            try:
                sql = """DROP TABLE Attendants;
                      """
                cursor.execute(sql)
            except:
                pass

    def GetOwnerEmail(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT owner_email FROM Owners
            """
            cursor.execute(sql)
            result = cursor.fetchone()

        return result[0] #return owner emails in db

    def GenerateCode(self):
        messagebox.showinfo("Code","Code sent to supervisors email.")
        emailReciever = self.GetOwnerEmail()
        numbers = self.GetNumbers()
        self.UpdateOwnerCode(numbers)

        self.SendEmail(emailReciever, numbers)

    def GetNumbers(self):
        numbers = str(random.randint(1,9))
        for i in range(5):
            numbers += str(random.randint(0, 9))
        return numbers

    def UpdateOwnerCode(self, numbers):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            values = (numbers,)
            sql = """UPDATE Owners
            SET owner_code = ?;
            """
            cursor.execute(sql, values)

    def SendEmail(self, emailReciever, numbers):
        self.sendCodeToSupervisor(emailReciever, numbers)

    def sendCodeToSupervisor(self, reciever_email, code):
        port = 465  # For SSL
        smtpServer = "smtp.gmail.com"
        subject = 'Attendant code Cinnamon Photography for registration.'
        body = f'Your attendant is requesting a code to register.\nThe code is: {code}'

        message = f'Subject: {subject}\n\n{body}'
        file = open("EmailPassword.txt","r")
        emailPassword = file.read()
        file.close()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtpServer, port, context=context) as server: #connect to smpt server
                server.login("noreplycinnamonphotography@gmail.com", emailPassword) #log into email
                server.sendmail("noreplycinnamonphotography@gmail.com", "XXXXXXX", message) #send email to recipient
            return True
        except:
            return False



#USER CONFIMRATION SECTION
class UserConfirmation(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #BACK/FORWARD BUTTON
        backButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:controller.show_frame(HomeScreen))
        backButton.place(relx=0, rely=0)

        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.35, anchor=CENTER, width=400, height=250)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        codeLabel = ttk.Label(self.textFrame, text="Code")
        codeLabel.place(relx=0.15, rely=0.55)

        #BUTTONS
        confirmButton = ttk.Button(self, text="Confirm",width=12,
                                   command=lambda: self.CheckCode(self.codeEntry.get(), controller))
        confirmButton.place(relx=0.5,rely=0.8,anchor=CENTER)

        #ENTRY
        self.codeEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.codeEntry.place(relx=0.35, rely=0.55)

    def ClearEntries(self):
        #clear code entry
        try:
            self.codeEntry.delete(0, END)
        except:
            pass

    def CheckCode(self, value, controller):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            ownerUsername = self.GetClientUsernameFromFile()
            values = (ownerUsername,)
            sql = """SELECT owner_code FROM Owners
            WHERE owner_username = ?;
            """
            cursor.execute(sql, values)
            result = cursor.fetchone()

        if str(result[0]) == str(value): #if code matches code in db
            self.ClearEntries()
            controller.show_frame(OwnerMenu)

    def GetClientUsernameFromFile(self):
        file = open("UsernameInUse.txt", "r")
        ownerUsername = file.read()
        file.close()

        return ownerUsername


#ATTENDANT CONFIRMATION
class AttendantConfirmation(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #BACK/FORWARD BUTTON

        backButton = ttk.Button(self, text="⌂", width=2,
                                command=lambda:[self.ClearEntries(),controller.show_frame(HomeScreen)])
        backButton.place(relx=0, rely=0)

        #TEXT FRAME
        self.textFrame = tk.LabelFrame(self)
        self.textFrame.place(relx=0.5, rely=0.35, anchor=CENTER, width=400, height=250)
        self.textFrame.grid_rowconfigure(0, weight=5)
        self.textFrame.grid_columnconfigure(0, weight=5)

        #LABELS
        f = font.nametofont('TkTextFont')


        codeLabel = ttk.Label(self.textFrame, text="Code")
        codeLabel.place(relx=0.15, rely=0.55)

        helpLabel = ttk.Label(self, text="Check your emails for this code.",font=(f, 14))
        helpLabel.place(relx=0.24, rely=0.63)

        #BUTTONS
        confirmButton = ttk.Button(self, text="Confirm",width=12,
                                   command=lambda: self.CheckCode(self.codeEntry.get(), controller))
        confirmButton.place(relx=0.5,rely=0.8,anchor=CENTER)

        #ENTRY
        self.codeEntry = tk.Entry(self.textFrame, width=30, bd=2)
        self.codeEntry.place(relx=0.35, rely=0.55)

    def ClearEntries(self):
        #clear code entry
        try:
            self.codeEntry.delete(0, END)
        except:
            pass

    def CheckCode(self, value, controller):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            values = (attendantUsernameGlobal,)
            sql = """SELECT attendant_code FROM Attendants
            WHERE attendant_username = ?;
            """
            cursor.execute(sql, values)
            result = cursor.fetchone()

        if str(result[0]) == str(value): #if  code in db matches code in entry
            self.ClearEntries()
            controller.show_frame(AttendantMenu)


#BOOKING FORM
class BookingForm(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #self.DropVenuesTable()
        self.CreateVenuesTable()
        #self.DropBookingsTable()
        self.CreateBookingsTable()
        self.f = font.nametofont('TkTextFont')
        bookingTitle = tk.Label(self, text="Photo Booth Hire Booking Form", font=(self.f, 17))
        bookingTitle.place(relx=0.50, rely=0.05,anchor=CENTER)

        helpButton = ttk.Button(self, text="?", width=2,
                                command=lambda:self.helpWindow(parent))
        helpButton.place(relx=0.96, rely=0)

        homeButton = ttk.Button(self, text="<-", width=2,
                                command=lambda:[self.ClearEntries(),controller.ClearQueue(LogIn),controller.show_frame(CustomerMenu)])
        homeButton.place(relx=0.01, rely=0)


        #Basic Details
        basicDetails = ttk.Label(self,text="Enter The Following Details:",font=(self.f,14))
        basicDetails.place(relx=0.23, rely=0.14)


        phoneNumberLabel = ttk.Label(self,text="Phone Number    +44")
        phoneNumberLabel.place(relx=0.22, rely=0.21)

        self.phoneNumberEntry = ttk.Entry(self)
        self. phoneNumberEntry.place(relx=0.47, rely=0.21)

        dateOfEventLabel = ttk.Label(self, text="Date Of Event")
        dateOfEventLabel.place(relx=0.23,rely=0.28)

        #date of event
        dayVar = StringVar(self)
        dayVar.set("01")

        monthVar = StringVar(self)
        monthVar.set("01")

        yearVar = StringVar(self)
        yearVar.set("01")

        #time of event
        startHrVar = StringVar(self)
        startHrVar.set("01")

        startMinVar = StringVar(self)
        startMinVar.set("01")

        endHrVar = StringVar(self)
        endHrVar.set("01")

        endMinVar = StringVar(self)
        endMinVar.set("01")

        #date of event menu
        dayMenu = ttk.OptionMenu(self,dayVar,"DAY","01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31")
        dayMenu.place(relx=0.39, rely=0.28)

        monthMenu = ttk.OptionMenu(self, monthVar,"MONTH","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
        monthMenu.place(relx=0.48, rely=0.28)

        yearMenu = ttk.OptionMenu(self, yearVar, "YEAR", "2022","2023","2024")
        yearMenu.place(relx=0.6, rely=0.28)


        #time of event menue
        boothStartTimeLabel = ttk.Label(self,text="Start Time Of Hire")
        boothStartTimeLabel.place(relx=0.22, rely=0.36)

        boothStartHour = ttk.OptionMenu(self,startHrVar,"HOUR","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23")
        boothStartHour.place(relx=0.48, rely=0.36)

        boothStartMin = ttk.OptionMenu(self,startMinVar,"MIN","00","15","30","45")
        boothStartMin.place(relx=0.6, rely=0.36)

        boothEndTimeLabel = ttk.Label(self,text="End Time Of Hire")
        boothEndTimeLabel.place(relx=0.22, rely=0.43)

        boothEndHour = ttk.OptionMenu(self,endHrVar,"HOUR","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24")
        boothEndHour.place(relx=0.48, rely=0.43)

        boothEndMin = ttk.OptionMenu(self,endMinVar,"MIN","00","15","30","45")
        boothEndMin.place(relx=0.6, rely=0.43)

        #address entries
        venueNumberLabel = ttk.Label(self,text="Venue House\n    Number")
        venueNumberLabel.place(relx=0.06, rely=0.67)

        self.venueHouseNumberEntry = ttk.Entry(self,width=5)
        self.venueHouseNumberEntry.place(relx=0.24, rely=0.69)

        venueRoadNameLabel = ttk.Label(self,text="Venue Street or \n   Road Name")
        venueRoadNameLabel.place(relx=0.04, rely=0.76)

        self.venueRoadNameEntry = ttk.Entry(self,width=20)
        self.venueRoadNameEntry.place(relx=0.24, rely=0.77)

        venueTownNameLabel = ttk.Label(self,text="        Venue County")
        venueTownNameLabel.place(relx=0.02, rely=0.85)

        self.venueCountyNameEntry = ttk.Entry(self,width=20)
        self.venueCountyNameEntry.place(relx=0.24, rely=0.85)

        venuePostCodeLabel = ttk.Label(self,text="Venue Postcode")
        venuePostCodeLabel.place(relx=0.04, rely=0.91)

        self.venuePostCodeEntry = ttk.Entry(self,width=10)
        self.venuePostCodeEntry.place(relx=0.24, rely=0.91)

        #guest count label and entry
        peopleAttendingLabel = ttk.Label(self,text="Number Of Guests")
        peopleAttendingLabel.place(relx=0.02, rely=0.62)

        peopleAttendingEntry = ttk.Entry(self, width = 5)
        peopleAttendingEntry.place(relx=0.24, rely=0.62)


        #no prints label
        noOfPrintsLabel = ttk.Label(self,text="Number Of Prints: ")
        noOfPrintsLabel.place(relx=0.65, rely=0.62)

        noOfPrintsResult = ttk.Label(self, text ="3")
        noOfPrintsResult.place(relx=0.88, rely=0.62)

        packageLabel = ttk.Label(self,text="Choose Your Package:",font=(self.f,14))
        packageLabel.place(relx=0.28, rely=0.49)

        packageVar = StringVar(self)
        packageVar.set("01")

        packageMenu = ttk.OptionMenu(self, packageVar,"PACKAGE","Basic","Birthday","Business","Wedding")
        packageMenu.place(relx=0.37, rely=0.56)

        guestbookLabel = ttk.Label(self,text="Guestbook: ")
        guestbookLabel.place(relx=0.65, rely=0.7)

        bookVar = BooleanVar(self)
        guestBookCheckBox = tk.Checkbutton(self, variable=bookVar)
        guestBookCheckBox.place(relx=0.8, rely=0.69)

        skinVar = StringVar(self)
        skinVar.set("01")

        skinMenu = ttk.OptionMenu(self, skinVar,"SKIN", "Black","White","Champange","VW Campervan","Custom")
        skinMenu.place(relx=0.74,rely=0.77)

        skinMenuLabel = ttk.Label(self,text="Skins: ")
        skinMenuLabel.place(relx=0.65, rely=0.77)



        submitButton = ttk.Button(self, text="Submit"
                            ,command=lambda: self.CalculateBookingCost(packageVar.get(), self.venuePostCodeEntry.get(), peopleAttendingEntry.get(), startHrVar.get(), startMinVar.get(), endHrVar.get(), endMinVar.get(), bookVar.get(),dayVar.get(), monthVar.get(), yearVar.get(), skinVar.get(), self.phoneNumberEntry.get(), self.venueRoadNameEntry.get(), self.venueCountyNameEntry.get(), self.venueHouseNumberEntry.get()))
        submitButton.place(relx=0.82,rely=0.93)

    def ClearEntries(self):
        #entries may be empty, so need try and except
        try:
            self.venuePostCodeEntry.delete(0, END)
        except:
            pass
        try:
            self.venueCountyNameEntry.delete(0, END)
        except:
            pass
        try:
            self.venueRoadNameEntry.delete(0, END)
        except:
            pass
        try:
            self.venueHouseNumberEntry.delete(0, END)
        except:
            pass

    def helpWindow(self, parent):
        #help window to help user on what to write in each entry/dropdown of the booking form
        newWindow = Toplevel(parent)
        newWindow.geometry("350x200")
        newWindow.geometry("350x200")
        newWindow.title("Help")
        label = ttk.Label(newWindow, text="Enter your phone number to be used to contact you.\n\nEnter the address where the photobooth\nwill be set up.\n\nEnter the approximate start time of the hire.\nAttendants arrive 1Hr before the start of hire.\n\nEnter the approximate number of guests at the event.\n\nAll bookings must end before midnight.")
        label.place(relx=0.1, rely=0.05)

    def CreateBookingsTable(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            sql = """CREATE TABLE IF NOT EXISTS Bookings
            (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_startTime TIME,
            booking_endTime TIME,
            booking_date DATE,
            customer_id INTEGER,
            attendant_id INTEGER,
            booking_price FLOAT,
            venue_id INTEGER,
            booking_type TEXT,
            booking_skin TEXT,
            booking_guests INTEGER,
            FOREIGN KEY(venue_id) REFERENCES Venues(venue_id),
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id),
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id),
            FOREIGN KEY(attendant_id) REFERENCES Attendants(attendant_id)
            );
            """
            cursor.execute(sql)


    def CreateVenuesTable(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            sql = """CREATE TABLE IF NOT EXISTS Venues
            (
            venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_houseNumber TEXT,
            booking_roadName TEXT,
            booking_county TEXT,
            booking_postcode TEXT,
            venue_distance FLOAT
            );
            """
            cursor.execute(sql)

    def DropVenuesTable(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            try:
                sql = """DROP TABLE Venues;
                      """
                cursor.execute(sql)
            except:
                pass

    def DropBookingsTable(self):
        with sqlite3.connect("NEA_Customer.db") as db: #establish connection with db
            cursor = db.cursor()
            try:
                sql = """DROP TABLE Bookings;
                      """
                cursor.execute(sql)
            except:
                pass

    def CheckVenueIsNew(self, addressLine1, addressLine2, houseNumber):
        ID = 0
        addressList = [houseNumber, addressLine1, addressLine2]
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT booking_houseNumber, booking_roadName, booking_county FROM Venues

            """

            cursor.execute(sql)
            result = cursor.fetchall()
            if len(result) < 1: #if addresses in db
                return True
            else:
                totalPercent = 0
                perecentDictionary = {}
                for address in result: #loop through addresses
                    ID += 1
                    count = -1
                    totalPercent = 0
                    score = 0
                    closeEnough = True
                    if address[0] == houseNumber: #if house number in db matches house number in entry
                        for each in address: #loop through address values
                            count += 1
                            a = each.upper()
                            b = addressList[count].upper()
                            a = " ".join(a.split())
                            b = " ".join(b.split())
                            lenA = len(a)
                            lenB = len(b)
                            a = a.split(" ")
                            b = b.split(" ")
                            if closeEnough == True:
                                for i in range(max(len(a), len(b))): #loop through longest string
                                    try:
                                        score += (self.levenshtein(a[i], b[i], 0))#gets edit distance betweem string a and b, sets score to 0 when itialised
                                    except:
                                        if lenA > lenB:
                                            score += len(a[i])
                                        else:
                                            score += len(b[i])
                                if max(lenA, lenB) == 0:
                                    totalPercent += 1
                                else:
                                    percent = (1 - (score / max(lenA, lenB))) #calculates the similarity percentage

                                    if score == 0: #if score is 0, 100% matches otherwise it errors
                                        percent = 1
                                    if percent > 0.7: #considered similar enough
                                        totalPercent += percent
                                    else:
                                        closeEnough = False

                    perecentDictionary[ID] = totalPercent
            if max(perecentDictionary.values()) > 2.58: #if addresses are considered similar enough
                return max(perecentDictionary, key=perecentDictionary.get) #return attendant ID with highest match rate
            else:
                return True

    def levenshtein(self,a, b, score):
        if not a:  # if a is empty, return len b
            return int(score) + len(b)
        if not b:  # if b is empty, return len a
            return int(score) + len(a)

        if a[0] == b[0]:
            return self.levenshtein(a[1:], b[1:], score)

        else:
            return min(self.levenshtein(a[1:], b[1:], score + 1),
                       self.levenshtein(a, b[1:], score + 1),
                       self.levenshtein(a[1:], b, score + 1))



    def GetVenueID(self, road, postcode):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (postcode.upper().replace(" ",""),)
            sql = """SELECT booking_roadName, venue_id FROM Venues
            WHERE booking_postcode = ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchall()
            for each in result: #loop through addresses where postcodes match
                if road.upper().replace(" ","") in each[0]: #if any spaces in road name, remove them
                    return each[1]

    def InsertIntoVenueTable(self, road, county, postcode, distance, houseNumber):
        new = self.CheckVenueIsNew(road, county, houseNumber)
        if isinstance(new, bool): #if address is considered new
            with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
                cursor = db.cursor()
                distance = round(distance,2)
                if len(houseNumber) == 0: #if no house number
                    houseNumber = ""
                values = (road.upper(), postcode.upper().replace(" ",""), distance, houseNumber, county.upper())
                sql = """INSERT INTO Venues(booking_roadName, booking_postcode, venue_distance, booking_houseNumber, booking_county)
                VALUES (?,?,?,?,?);
                """
                cursor.execute(sql, values)
                db.commit()
                return self.GetHighestVenueID()
        return new

    def GetHighestVenueID(self,):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT venue_id FROM Venues
                    ORDER BY venue_id DESC
                    """
            cursor.execute(sql)
            result = cursor.fetchall()
            return result[0][0] #return only 1 venue id


    def GetSkinCost(self, skin):
        skins = {"Black":25,"White":25,"VW Campervan":50,"Champange":50,"Custom":100} #maps the skin cost to each skin
        skin = skins[skin] #gets skin cost for given skin
        return skin

    def GetPackageCosts(self, package):
        #returns rate, costPerMile, pricePerGuest in that order for each package type
        if package == "Basic":
            return 80, 2, 0.25
        elif package == "Birthday":
            return 95, 1.5, 0.5
        elif package == "Wedding":
            return 70, 1, 0.75
        elif package == "Business":
            return 100, 0.5, 0.25

    def ConvertDayToFormat(self, day, month, year):
        month = self.GetMonthValue(month)
        valid = self.CheckDateIsPossible(month, day)
        if valid: #if date is exists
            eventDate = date(int(year),int(month),int(day))
            dateToday = str(date.today())
            dateTodaySplit = dateToday.split("-")
            dateToday = date(int(dateTodaySplit[0]),int(dateTodaySplit[1]),int(dateTodaySplit[2]))
            return dateToday, eventDate
        else:
            return False, False

    def CheckDateIsPossible(self, month, day):
        if month == "02":
            if int(day) > 28: #feb cannot have a date higher than 28th
                return False
        if month == "04" or month == "06" or month == "09" or month == "11":
            if int(day) > 30: #april, june, sept and nov cannot have more than 30 days
                return False
        return True

    def GetMonthValue(self, month):
        #maps numerical month value to each month
        months = {"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06","Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}
        try:
            month = months[month] #gets numerical value from month chosen
        except:
            pass

        return month

    def CheckValuesAreNotNull(self, package, guests, day, month, year, startHr, startMin, endHr, endMin, skin, phone, addressLine1, addressLine2):
        count = 0
        #if any of these are true, the infomration is incomplete
        if package == "PACKAGE":
            count += 1
        if len(guests) < 1:
            count += 1
        if day == "DAY":
            count += 1
        if month == "MONTH":
            count += 1
        if year == "YEAR":
            count += 1
        if startHr == "HOUR":
            count += 1
        if startMin == "MIN":
            count +=1
        if endHr == "HOUR":
            count +=1
        if endMin == "MIN":
            count += 1
        if skin == "SKIN":
            count += 1
        if len(phone) != 11:
            count +=1
        if addressLine1 is None:
            count += 1
        if addressLine2 is None:
            count += 1

        if count != 0: #one of the if statements is true, form is not complete
            messagebox.showerror("Booking Form","Please complete the booking form.")
            return False
        else:
            return True

    def CalculateBookingCost(self, package, postcode, guests, startHr, startMin, endHr, endMin, book, day, month, year, skin, phone, road, county, houseNumber):
        phone = "0" + phone #form valid uk phone number
        valuesCompleted = self.CheckValuesAreNotNull(package, guests, day, month, year, startHr, startMin, endHr,
                                                     endMin, skin, phone, road, county)
        if valuesCompleted: #is form completed
            temp, eventDate = self.ConvertDayToFormat(day, month, year)
            if temp != False:
                todaysDate, eventDate = self.ConvertDayToFormat(day, month, year)
                daysTillEvent = self.GetDaysTillEvent(todaysDate, eventDate)
                if daysTillEvent > 1: #if event is not today
                    dateOfEvent = (day,month,year)
                    bookingCostPerHour = 0
                    rate, costPerMile, pricePerGuest = self.GetPackageCosts(package)
                    isValidTime = self.CheckTimesAreValid(startHr, startMin, endHr, endMin)
                    if isValidTime: #is startTime < endTime
                        validVenue ,distance = self.GetDistanceToVenue(postcode)
                        if validVenue: #is venue a valid place
                            distance = distance/1609 #convert distance from meters to miles
                            bookingCostPerHour += (costPerMile * distance)
                            bookingCostPerHour += (pricePerGuest * int(guests))
                            bookingDuration = self.CalculateBookingDuration(startHr, startMin, endHr, endMin)
                            bookingCostPerHour += rate
                            bookingCost = round(bookingCostPerHour* bookingDuration,2)
                            if book: #if guest book is wanted
                                bookingCost += 25
                            bookingCost += self.GetSkinCost(skin)
                            if daysTillEvent < 8: #close bookings are penalised for the lack of preperation
                                bookingCost = bookingCost * 1.15
                            elif daysTillEvent > 365: #future bookings are rewarded
                                bookingCost = bookingCost * 0.9

                            if bookingCost < 350: #min booking cost is 350, otherwise isnt worth the time
                                bookingCost = 350
                            attendantID = self.ChooseAttendantForEvent(postcode, eventDate)
                            if attendantID is None:
                                messagebox.showerror("Date","Please select a different date, as we are fully booked.")
                            else:
                                text = "Cost of booking is", round(bookingCost,2)
                                messagebox.showinfo("Price",text)
                                customerName = self.GetCustomerDetails()
                                recieverEmail = self.GetSupervisorEmail(attendantID)
                                self.sendBookingFormEamil("noreplycinnamonphotography@gmail.com", recieverEmail, customerName, bookingCost, guests, postcode,dateOfEvent,skin)
                                venueID = self.InsertIntoVenueTable(road, county, postcode, distance, houseNumber)
                                self.InsertIntoBookings(startHr, startMin, endHr, endMin, eventDate, attendantID, bookingCost, venueID, skin, guests, package)

                        elif distance > 40: #is venue close enough for the business to go to
                            messagebox.showerror("Venue location","The venue is too far away. We only offer bookings within a 40 mile radius.")
                else:
                    messagebox.showerror("Date","Please enter a valid date.")
            else:
                messagebox.showerror("Date","Date is not valid.")

    def GetSupervisorEmail(self, ID):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (ID,)
            sql = """SELECT owner_email FROM Owners
            INNER JOIN Attendants
            ON Owners.owner_id = Attendants.attendant_supervisor
            WHERE attendant_id = ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchall()
        return result[0][0]


    def GetCustomerDetails(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            username = self.GetUsernameFromFile()
            values = (username, )
            sql = """SELECT customer_fname, customer_lname FROM CUSTOMERS
            WHERE customer_username = ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchall()
            fname = result[0][0]
            lname = result[0][1]
        customerName = (fname,lname)
        return customerName


    def sendBookingFormEamil(self, sender_email, reciever_email, name, price, guests, address, date, skin):
        port = 465  # For SSL
        smtpServer = "smtp.gmail.com"
        subject = 'A successful booking has been made. Details are below'
        body = f'{name[0]} {name[1]} has made a booking.\nDate: {date[0]} {date[1]} {date[2]}\nLocation: {address}\nThere will be {guests} guests.\nSkin: {skin}\nThe total price is {price}'

        message = f'Subject: {subject}\n\n{body}'
        file = open("EmailPassword.txt","r")
        emailPassword = file.read()
        file.close()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtpServer, port, context=context) as server: #connect to smtp server
                server.login(sender_email, emailPassword) #log into email
                server.sendmail(sender_email, reciever_email, message) #send email
            return True
        except:
            return False

    def GetDaysTillEvent(self, today, dateOfEvent):
      difference = dateOfEvent - today #gets difference between days to see how close the event is
      return difference.days

    def GetDistanceToVenue(self, postcode):
        with open("apiKey.txt") as file:
            apikey = file.read() #gets api key

        url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"
        try:
            # link generated
            r = requests.get(url + "origins=" + "CM133SB" + "&destinations=" + postcode + "&key=" + apikey)
            distance = r.json()["rows"][0]["elements"][0]["distance"]["value"]
            return True, distance
        except:
            messagebox.showerror("Address","Please enter a valid address.")
            return False, 0

    def CheckTimesAreValid(self, startHr, startMin, endHr, endMin):
        totalStart = (startHr*100) + startMin
        totalEnd = (endHr*100) + endMin
        if totalStart >= totalEnd: #endTime is before startTime
            messagebox.showerror("Times","Enter a valid time end time.")
            return False
        else:
            return True

    def CalculateBookingDuration(self, startHr, startMin, endHr, endMin):
        startHr = int(startHr)
        startMin = int(startMin)
        endMin = int(endMin)
        endHr = int(endHr)

        if startMin > startHr:
            endHr = int(endHr-1)
            endMin = int(endMin +60)
        minDifference = int(endMin) - int(startMin)
        hrDifference = int(endHr) - int(startHr)
        hrDifference = hrDifference *60
        difference = int(hrDifference) + int(minDifference)
        difference = difference/60

        return difference

    def GetUsernameFromFile(self):
        file = open("UsernameInUse.txt","r")
        username = file.read()
        file.close()
        return username

    def GetDistanceFromAttendant(self, postcode, venuePostcode):
        with open("apiKey.txt") as file:
            apikey = file.read() #gets api key

        url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"
        try:
            # link generated
            r = requests.get(url + "origins=" + postcode + "&destinations=" + venuePostcode + "&key=" + apikey)
            distance = r.json()["rows"][0]["elements"][0]["distance"]["value"]
            return distance
        except:
            messagebox.showerror("Address","Please enter a valid address.")

    def ChooseAttendantForEvent(self, postcode, date):
        attendants = self.GetAttendantIDs()

        attendantScores = self.CreateAttendantDictionary(attendants)
        attendantScores = self.IsDayOccupied(attendants, attendantScores, date) #checks if attendant has job on that day
        attendantScores = self.GetClosestAttendant(attendants, attendantScores, postcode) #gets distance from attendant to venue
        attendantScores = self.GetMonthlyEarnings(attendantScores, date, attendants) #gets last months earnings
        attendantScores = self.GetMonthlyJobs(attendantScores, date, attendants) #gets last months job count
        attendantID = max(attendantScores, key=attendantScores.get)
        if attendantScores[attendantID] < 1:
            return None
        else:
            return attendantID

    def GetMonthlyJobs(self, attendantScores, date, attendants):
        last30Days = self.Minus30DaysFromDate(date)
        attendantJobs = []
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            for each in attendants:
                values = (each[0], date, last30Days)
                sql = """SELECT COUNT(Bookings.booking_id) FROM Bookings
                INNER JOIN Attendants 
                ON Bookings.attendant_id = Attendants.attendant_id
                WHERE Attendants.attendant_id = ?
                AND Bookings.booking_date < ?
                AND Bookings.booking_date > ?
                """

                cursor.execute(sql, values)
                result = cursor.fetchall()
                toAppend = [str(result[0][0]), each[0]] #append no. bookings attendant has, and their attendant ID
                attendantJobs.append(toAppend)

        attendantJobsSorted = self.MergeSortList(attendantJobs) #sort list by highest  number of jobs last month
        attendantScores = self.ScoreForJobs(attendantScores, attendantJobsSorted) #add score to dict
        return attendantScores

    def ScoreForJobs(self, attendantScores, attendantJobs):
        n = 7
        for each in attendantJobs: #loop through attendants
            n = n - 2
            if n > 0:
                attendantScores[each[1]] += n

        return attendantScores

    def GetMonthlyEarnings(self, attendantScores, date, attendants):
        last30Days = self.Minus30DaysFromDate(date)
        attendantEarnings = []
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            for each in attendants: #loop through attendants
                values = (each[0],date,last30Days)
                sql = """SELECT SUM(Bookings.booking_price) FROM Bookings
                INNER JOIN Attendants 
                ON Bookings.attendant_id = Attendants.attendant_id
                WHERE Attendants.attendant_id = ?
                AND Bookings.booking_date < ?
                AND Bookings.booking_date > ?
                """

                cursor.execute(sql, values)
                result = cursor.fetchall()
                toAppend = [str(result[0][0]), each[0]] #append earnings and ID
                attendantEarnings.append(toAppend)

        attendantEarningsSorted = self.MergeSortList(attendantEarnings) #sort by highest earnings
        attendantScores = self.ScoreForEarnings(attendantScores, attendantEarningsSorted)
        return attendantScores

    def ScoreForEarnings(self, attendantScores, attendantEarnings):
        attendantEarnings = attendantEarnings[::-1] #flip list so lowest earnings is first
        n = 7
        for each in attendantEarnings: #loop through list
            n = n- 2
            if n > 0:
                attendantScores[each[1]] += n

        return attendantScores

    def Minus30DaysFromDate(self, date):
        date = str(date)
        date = date.split("-")
        if str(date[1]) == "01":
            date[1] = "12"
            date[0] = int(date[0])-1
        else:
            toAdd = int(date[1]) - 1
            if date[1] == "11" or date[1] == "12":
                date[1] = toAdd
            else:
                date[1] = "0" + str(toAdd)

        if str(date[1]) == "04" or str(date[1]) == "06" or str(date[1]) == "09" or str(date[1]) =="11":
            if date[2] == "31":
                date[2] = "30"

        elif str(date[1]) == "02":
            date[2] = "28"

        newDate = (str(date[0])+"-"+str(date[1])+"-"+str(date[2]))
        newDate1 = datetime.fromisoformat(newDate)

        return newDate1

    def GetClosestAttendant(self, attendants, attendantScores, venuePostcode):
        listOfDistances = []
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            for each in attendants:
                values = (each[0],)
                sql = """SELECT attendant_postcode FROM Attendants
                WHERE attendant_id = ?
                """

                cursor.execute(sql, values)
                result = cursor.fetchone()

                distance = self.GetDistanceFromAttendant(result[0], venuePostcode)
                distance = round(distance/1609, 2) #convert distance from meters to miles
                toAppend = [distance,each[0]] #append distance and attendant id
                listOfDistances.append(toAppend)

            listOfDistancesSorted = self.MergeSortList(listOfDistances) #sort by highest distance
            attendantScores = self.ScoreForCloseness(attendantScores,listOfDistancesSorted)

        return attendantScores

    def ScoreForCloseness(self, attendantScores, listOfDistances):
        n = 10
        for each in listOfDistances:
            n = n- 3
            if n > 0:
                attendantScores[each[1]] += n

        return attendantScores


    def MergeSortList(self, list):
        size = len(list)
        if size > 1:
            middle = size // 2
            leftList = list[:middle]
            rightList = list[middle:]

            self.MergeSortList(leftList)
            self.MergeSortList(rightList)

            l = 0
            r = 0
            m = 0

            leftSize = len(leftList)
            rightSize = len(rightList)

            while l < leftSize and r < rightSize:
                if leftList[l] < rightList[r]:
                    list[m] = leftList[l]
                    l += 1
                else:
                    list[m] = rightList[r]
                    r += 1

                m += 1

            while l < leftSize:
                list[m] = leftList[l]
                l += 1
                m += 1

            while r < rightSize:
                list[m] = rightList[r]
                r += 1
                m += 1

        return list

    def IsDayOccupied(self, attendants, attendantScores, date):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            for each in attendants:
                values = (each[0],str(date))
                sql = """SELECT Bookings.booking_date FROM Bookings
                INNER JOIN Attendants 
                ON Bookings.attendant_id = Attendants.attendant_id
                WHERE Attendants.attendant_id = ?
                AND Bookings.booking_date = ?
                """

                cursor.execute(sql, values)
                result = cursor.fetchall()
                if len(result) == 0:
                    attendantScores[each[0]] += 1
                else:
                    attendantScores[each[0]] -= 100

        return attendantScores


    def CreateAttendantDictionary(self, attendantIDs):
        attendantScores = {}
        for each in attendantIDs:
            attendantScores[each[0]] = 0

        return attendantScores


    def GetAttendantIDs(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT attendant_id FROM Attendants
            """

            cursor.execute(sql)
            result = cursor.fetchall()
        return result

    def InsertIntoBookings(self, startHr, startMin, endHr, endMin, date, attendantID, bookingPrice, venueID, skin, guests, type):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            if endHr == "24":
                endHr = "00"
            customerID = self.GetCustomerID()
            cursor = db.cursor()
            startTime = (startHr+":"+startMin)
            endTime = (endHr + ":" + endMin)
            values = (startTime, endTime, date, customerID, attendantID, bookingPrice, venueID, skin, guests, type)
            sql = """INSERT INTO Bookings(booking_startTime, booking_endTime, booking_date, customer_id, attendant_id, booking_price, venue_id, booking_skin, booking_guests, booking_type)     
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            cursor.execute(sql, values)
            db.commit()

    def GetCustomerID(self):
        file = open("UsernameInUse.txt", "r")
        username = file.read()
        file.close()
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (username,)
            sql = """SELECT customer_ID FROM Customers
            WHERE customer_username = ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchone()
        return result[0]

    def InsertIntoAttendants(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = ("testemail4@gmail.com","Attendant4","Lastname4","A-ALastname4123456","cm133sb")
            sql = """INSERT INTO Attendants(attendant_email, attendant_fname, attendant_lname, attendant_username, attendant_postcode)
            VALUES(?, ?, ?, ?, ?)"""

            cursor.execute(sql,values)
            db.commit()

#ATTENDANT MENU
class AttendantMenu(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


        self.f = font.nametofont('TkTextFont')
        self.nextBookingFrame = tk.LabelFrame(self)
        self.nextBookingFrame.place(relx=0.75, rely=0.35, anchor=CENTER, width=230, height=250)
        self.nextBookingFrame.grid_rowconfigure(0, weight=5)
        self.nextBookingFrame.grid_columnconfigure(0, weight=5)

        self.monthlyStats = tk.LabelFrame(self)
        self.monthlyStats.place(relx=0.25, rely=0.35, anchor=CENTER, width=230, height=250)
        self.monthlyStats.grid_rowconfigure(0, weight=5)
        self.monthlyStats.grid_columnconfigure(0, weight=5)

        self.attendantInformation = tk.LabelFrame(self)
        self.attendantInformation.place(relx=0.5, rely=0.8, anchor=CENTER, width=480, height=170)
        self.attendantInformation.grid_rowconfigure(0, weight=5)
        self.attendantInformation.grid_columnconfigure(0, weight=5)

        nextJobTitle = ttk.Label(self, text="Next Job:", font=(self.f,18))
        nextJobTitle.place(relx=0.63, rely=0.03)

        #Next job address
        nextJobAddy = ttk.Label(self.nextBookingFrame, text="Address: ", font=(self.f, 11))
        nextJobAddy.place(relx=0.05, rely=0.05)
        nextJobList = self.GetNextJobAddress()
        nextJobAddress = ttk.Label(self.nextBookingFrame, text=nextJobList[0], font=(self.f, 11))
        nextJobAddress.place(relx=0.45, rely=0.05)

        #next job date
        nextJobDate = ttk.Label(self.nextBookingFrame, text="Date: ", font=(self.f, 11))
        nextJobDate.place(relx=0.05, rely=0.2)
        nextJobDateText = ttk.Label(self.nextBookingFrame, text=nextJobList[3], font=(self.f, 11))
        nextJobDateText.place(relx=0.45, rely=0.2)

        #next job start time
        nextJobStart = ttk.Label(self.nextBookingFrame, text="Start Time: ", font=(self.f, 11))
        nextJobStart.place(relx=0.05, rely=0.35)
        nextJobStartText = ttk.Label(self.nextBookingFrame, text=nextJobList[1], font=(self.f, 11))
        nextJobStartText.place(relx=0.45, rely=0.35)

        #next job end time
        nextJobEnd = ttk.Label(self.nextBookingFrame, text="End Time: ", font=(self.f, 11))
        nextJobEnd.place(relx=0.05, rely=0.5)
        nextJobEndText = ttk.Label(self.nextBookingFrame, text=nextJobList[2], font=(self.f, 11))
        nextJobEndText.place(relx=0.45, rely=0.5)

        #next job type
        nextJobType = ttk.Label(self.nextBookingFrame, text="Type: ", font=(self.f, 11))
        nextJobType.place(relx=0.05, rely=0.65)
        nextJobTypeText = ttk.Label(self.nextBookingFrame, text=nextJobList[5], font=(self.f, 11))
        nextJobTypeText.place(relx=0.45, rely=0.65)

        #next job skin used
        nextJobSkin = ttk.Label(self.nextBookingFrame, text="Skin: ", font=(self.f, 11))
        nextJobSkin.place(relx=0.05, rely=0.8)
        nextJobSkinText = ttk.Label(self.nextBookingFrame, text=nextJobList[4], font=(self.f, 11))
        nextJobSkinText.place(relx=0.45, rely=0.8)


        monthlyJobTitle = ttk.Label(self, text="Next Month Stats:", font=(self.f,18))
        monthlyJobTitle.place(relx=0.05, rely=0.03)

        monthlyStatsText = self.GetTextDetails()
        #jobs next month
        monthlyJobCount = ttk.Label(self.monthlyStats, text="Jobs: ", font=(self.f, 11))
        monthlyJobCount.place(relx=0.05, rely=0.1)
        monthlyJobCountText = ttk.Label(self.monthlyStats, text=monthlyStatsText[0], font=(self.f, 11))
        monthlyJobCountText.place(relx=0.45, rely=0.1)

        #earnings next month
        monthlyEarningCount = ttk.Label(self.monthlyStats, text="Earnings: ", font=(self.f, 11))
        monthlyEarningCount.place(relx=0.05, rely=0.25)
        monthlyEarningCountText = ttk.Label(self.monthlyStats, text=monthlyStatsText[1], font=(self.f, 11))
        monthlyEarningCountText.place(relx=0.45, rely=0.25)

        #hours to work next month
        monthlyHoursCount = ttk.Label(self.monthlyStats, text="Earnings Per Job: ", font=(self.f, 11))
        monthlyHoursCount.place(relx=0.05, rely=0.4)
        monthlyHoursCountText = ttk.Label(self.monthlyStats, text=monthlyStatsText[2], font=(self.f, 11))
        monthlyHoursCountText.place(relx=0.65, rely=0.4)

        #earnings per hour next month
        monthlyTotalHrsWorked = ttk.Label(self.monthlyStats, text="Total Hours Worked: ", font=(self.f, 11))
        monthlyTotalHrsWorked.place(relx=0.05, rely=0.55)
        monthlyTotalHrsWorkedText = ttk.Label(self.monthlyStats, text=monthlyStatsText[3], font=(self.f, 11))
        monthlyTotalHrsWorkedText.place(relx=0.7, rely=0.55)

        monthlyEarningsPerHour = ttk.Label(self.monthlyStats, text="Earnings Per Hour: ", font=(self.f, 11))
        monthlyEarningsPerHour.place(relx=0.05, rely=0.7)
        monthlyEarningsPerHourText = ttk.Label(self.monthlyStats, text=monthlyStatsText[4], font=(self.f, 11))
        monthlyEarningsPerHourText.place(relx=0.7, rely=0.7)


        text = "As an attendant, you should aim to leave with plenty of margin for error. From\nexperience, leaving with the aim to reach the venue 1.5 hours before the booking starts\nis optimal. This leaves lots of time which makes the process less stressful.\n\nWhen you reach the venue, find the customer and ask them where the booth can be set\nup. Consider whether it is feesable to get it to that position, and if there are sufficient\nplug sockets avaliable. Before leaving, check you have all equiptment, and backups\nincase anything goes wrong. If there are any issues, please do not hesitate to call me\nvia my mobile phone number"
        informationText = ttk.Label(self.attendantInformation, text = text)
        informationText.place(relx=0.01, rely=0.05)

    def GetNextJobAddress(self):
        username = self.GetAttendantUsername()
        ID = self.GetAttendantID(username)

        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(ID),)
            sql = """SELECT Venues.booking_postcode, Bookings.booking_startTime, Bookings.booking_endTime, Bookings.booking_date, Bookings.booking_skin, Bookings.booking_type FROM Venues
                INNER JOIN Bookings 
                ON Venues.venue_id = Bookings.venue_id
                WHERE Bookings.attendant_id = ?
                ORDER BY Bookings.booking_date ASC;
            """

            cursor.execute(sql, values)
            result = cursor.fetchall()
        if len(result) < 1: #if no bookings where this venue ID exists
            return ["None", "None", "None", "None","None","None"]
        else:
            return result[0]

    def GetAttendantUsername(self):
        try:
            file = open("UsernameInUse.txt","r")
            username = file.read()
            file.close()
            return username
        except FileNotFoundError:
            pass

    def GetAttendantID(self, username):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (username,)
            sql = """SELECT attendant_id FROM Attendants
            WHERE attendant_username = ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchone()
        if result == None:
            return "None"
        else:
            return result[0]

    def GetTextDetails(self):
        text = []
        username = self.GetAttendantUsername()
        ID = self.GetAttendantID(username)
        text.append(self.GetNextMonthsJobCount(ID))
        text.append(self.GetNext30DayEarnings(ID))
        text.append(self.GetAvgJobPrice(ID))
        text.append(self.GetNextMonthHrsWorked(ID))
        text.append(self.GetEarningsPerHour(ID))

        return text

    def GetEarningsPerHour(self, ID):
        earnings = self.GetNext30DayEarnings(ID)
        hrsWorked = self.GetNextMonthHrsWorked(ID)

        try:
            earningsPerHr = int(earnings/hrsWorked)
            return earningsPerHr
        except:
            return 0

    def GetNextMonthHrsWorked(self, ID):
        todaysDate = self.GetTodaysDate()
        prev30Days = self.Add30DaysToDate(todaysDate)
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(todaysDate), ID, str(prev30Days))
            sql = """SELECT Bookings.booking_startTime, booking_endTime FROM Bookings
            WHERE Bookings.booking_date > ?
            AND attendant_id = ?
            AND Bookings.booking_date < ?
            """
            cursor.execute(sql, values)
            result = cursor.fetchall()
            totalHrs = 0
            for each in result:
                startTime = each[0].split(":")
                endTime = each[1].split(":")
                startHr = startTime[0]
                startMin = startTime[1]
                endHr = endTime[0]
                endMin = endTime[1]
                if endHr == "00":
                    endHr = "24"
                totalHrs += self.CalculateBookingDuration(startHr, startMin, endHr, endMin)
        return totalHrs


    def Add30DaysToDate(self, date):
        date = str(date)
        date = date.split("-")
        if str(date[1]) == "12":
            date[1] = "01"
            date[0] = int(date[0])+1
        else:
            toAdd = int(date[1]) +1
            if date[1] == "10" or date[1] == "11" or date[1] == "09":
                date[1] = toAdd
            else:
                date[1] = "0" + str(toAdd)

        if str(date[1]) == "04" or str(date[1]) == "06" or str(date[1]) == "09" or str(date[1]) =="11":
            if date[2] == "31":
                date[2] = "30"

        elif str(date[1]) == "01":
            date[2] = "28"


        newDate = (str(date[0])+"-"+str(date[1])+"-"+str(date[2]))
        newDate1 = datetime.fromisoformat(newDate)

        return newDate1

    def GetNext30DayEarnings(self, ID):
        todaysDate = self.GetTodaysDate()
        next30Days = self.Add30DaysToDate(todaysDate)
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(todaysDate), ID, str(next30Days))
            sql = """SELECT SUM(Bookings.booking_price) FROM Bookings
            WHERE Bookings.booking_date > ?
            AND attendant_id = ?
            AND Bookings.booking_date < ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchone()
        if result[0] is None: #if no bookings in the next 30 days for this attendant
            return 0
        return int(result[0] * 0.15) #attendants earn 15% of each booking

    def GetTodaysDate(self):
        return str(date.today())

    def GetNextMonthsJobCount(self, ID):
        todaysDate = self.GetTodaysDate()
        prev30Days = self.Add30DaysToDate(todaysDate)

        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(todaysDate), ID, str(prev30Days))
            sql = """SELECT COUNT(Bookings.booking_id) FROM Bookings
            WHERE Bookings.booking_date > ?
            AND attendant_id = ?
            AND Bookings.booking_date < ?
            """
            cursor.execute(sql, values)
            result = cursor.fetchone()
        return result[0]

    def GetAvgJobPrice(self, ID):
        jobs = self.GetNextMonthsJobCount(ID)
        earnings = self.GetNext30DayEarnings(ID)

        try:
            avgPrice = round(earnings/jobs, 2)
            return avgPrice
        except:
            return 0

    def CalculateBookingDuration(self, startHr, startMin, endHr, endMin):
        startHr = int(startHr)
        startMin = int(startMin)
        endMin = int(endMin)
        endHr = int(endHr)

        if startMin > startHr:
            endHr = int(endHr-1)
            endMin = int(endMin +60)
        minDifference = int(endMin) - int(startMin)
        hrDifference = int(endHr) - int(startHr)
        hrDifference = hrDifference *60
        difference = int(hrDifference) + int(minDifference)
        difference = difference/60
        return difference


#CUSTOMER MENU
class CustomerMenu(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


        self.f = font.nametofont('TkTextFont')
        self.nextBookingFrame = tk.LabelFrame(self)
        self.nextBookingFrame.place(relx=0.75, rely=0.35, anchor=CENTER, width=230, height=250)
        self.nextBookingFrame.grid_rowconfigure(0, weight=5)
        self.nextBookingFrame.grid_columnconfigure(0, weight=5)

        self.informationFrame = tk.LabelFrame(self)
        self.informationFrame.place(relx=0.25, rely=0.35, anchor=CENTER, width=230, height=250)
        self.informationFrame.grid_rowconfigure(0, weight=5)
        self.informationFrame.grid_columnconfigure(0, weight=5)

        self.informationFrame2 = tk.LabelFrame(self)
        self.informationFrame2.place(relx=0.5, rely=0.85, anchor=CENTER, width=480, height=130)
        self.informationFrame2.grid_rowconfigure(0, weight=5)
        self.informationFrame2.grid_columnconfigure(0, weight=5)

        nextJobTitle = ttk.Label(self, text="Your Next Booking:", font=(self.f,18))
        nextJobTitle.place(relx=0.55, rely=0.03)

        #Next job address
        nextBookingAddy = ttk.Label(self.nextBookingFrame, text="Address: ", font=(self.f, 11))
        nextBookingAddy.place(relx=0.05, rely=0.05)
        nextBookingList = self.GetNextJobAddress()
        nextJobAddress = ttk.Label(self.nextBookingFrame, text=nextBookingList[0], font=(self.f, 11))
        nextJobAddress.place(relx=0.45, rely=0.05)

        #next job date
        nextBookingDate = ttk.Label(self.nextBookingFrame, text="Date: ", font=(self.f, 11))
        nextBookingDate.place(relx=0.05, rely=0.2)
        nextBookingDateText = ttk.Label(self.nextBookingFrame, text=nextBookingList[3], font=(self.f, 11))
        nextBookingDateText.place(relx=0.45, rely=0.2)

        #next job start time
        nextBookingStart = ttk.Label(self.nextBookingFrame, text="Start Time: ", font=(self.f, 11))
        nextBookingStart.place(relx=0.05, rely=0.35)
        nextBookingStartText = ttk.Label(self.nextBookingFrame, text=nextBookingList[1], font=(self.f, 11))
        nextBookingStartText.place(relx=0.45, rely=0.35)

        #next job end time
        nextBookingEnd = ttk.Label(self.nextBookingFrame, text="End Time: ", font=(self.f, 11))
        nextBookingEnd.place(relx=0.05, rely=0.5)
        nextBookingEndText = ttk.Label(self.nextBookingFrame, text=nextBookingList[2], font=(self.f, 11))
        nextBookingEndText.place(relx=0.45, rely=0.5)

        #next job type
        nextBookingType = ttk.Label(self.nextBookingFrame, text="Type: ", font=(self.f, 11))
        nextBookingType.place(relx=0.05, rely=0.65)
        nextBookingTypeText = ttk.Label(self.nextBookingFrame, text=nextBookingList[5], font=(self.f, 11))
        nextBookingTypeText.place(relx=0.45, rely=0.65)

        #next job skin used
        nextBookingPrice = ttk.Label(self.nextBookingFrame, text="Price: ", font=(self.f, 11))
        nextBookingPrice.place(relx=0.05, rely=0.8)
        nextBookingPriceText = ttk.Label(self.nextBookingFrame, text=nextBookingList[4], font=(self.f, 11))
        nextBookingPriceText.place(relx=0.45, rely=0.8)


        informationAboutBookings = ttk.Label(self, text="About Us:", font=(self.f,17))
        informationAboutBookings.place(relx=0.15, rely=0.03)

        importantInfoTitle = ttk.Label(self, text="Important things to know before booking:", font=(self.f,17))
        importantInfoTitle.place(relx=0.09, rely=0.65)

        text = "Photobooths are a fun way for \nyour friends, family and collegues \nto spend their time during an event.\n\nWe aim to provide excellent\ncustomer service, to ensure your event \ngoes smoothly.\n\nOperating in the events industry for the\npast 15 years means we have expertise\nin the field.\n\nWith prices starting from £350, you \nwill struggle to find anywhere cheaper."
        informationText = ttk.Label(self.informationFrame, text = text)
        informationText.place(relx=0.01, rely=0.05)

        makeBooking = ttk.Button(self,text="Make Booking",
                                 command=lambda:controller.show_frame(BookingForm))
        makeBooking.place(relx=0.42,rely=0.6)

        text="It is important that the photobooth can be placed close to a plug socket as it requires\nelectiricty to run. The booth is also extremely heavy, so if wanted upstairs, there must be\nsome easy access, such as a lift.\n\nAttendants will arrive approximately 1 hour before the start time. This will be used to\nbring in and setup the booth. The booth can be used for outside events, but we require\nsheltering incase there is rainfall. Rain will interfere with the functionality of the booth."
        bookingInformationLabel = ttk.Label(self.informationFrame2,text=text)
        bookingInformationLabel.place(relx=0.01,rely=0.02)


    def GetNextJobAddress(self):
        username = self.GetCustomerUsername()
        ID = self.GetCustomerID(username)

        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(ID),)
            sql = """SELECT Venues.booking_postcode, booking_startTime, booking_endTime, booking_date, booking_price, booking_type FROM Venues
                INNER JOIN Bookings 
                ON Venues.venue_id = Bookings.venue_id
                WHERE Bookings.customer_id = ?
                ORDER BY booking_date ASC;
            """

            cursor.execute(sql, values)
            result = cursor.fetchall()
        if len(result) < 1: #if no bookings for customer
            return ["None", "None", "None", "None","None","None"]
        else:
            return result[0]

    def GetCustomerUsername(self):
        try:
            file = open("UsernameInUse.txt","r")
            username = file.read()
            file.close()
            return username
        except FileNotFoundError:
            pass

    def GetCustomerID(self, username):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (username,)
            sql = """SELECT customer_id FROM Customers
            WHERE customer_username = ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchone()

        if result == None: #if no customers with username provided
            return "None"
        else:
            return result[0]


#OWNER MENU
class OwnerMenu(tk.Frame): #inherts frame, which makes a blank frame to add widgets to
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


        self.f = font.nametofont('TkTextFont')
        self.nextBookingFrame = tk.LabelFrame(self)
        self.nextBookingFrame.place(relx=0.75, rely=0.35, anchor=CENTER, width=230, height=250)
        self.nextBookingFrame.grid_rowconfigure(0, weight=5)
        self.nextBookingFrame.grid_columnconfigure(0, weight=5)

        self.lastMonthStats = tk.LabelFrame(self)
        self.lastMonthStats.place(relx=0.25, rely=0.35, anchor=CENTER, width=230, height=250)
        self.lastMonthStats.grid_rowconfigure(0, weight=5)
        self.lastMonthStats.grid_columnconfigure(0, weight=5)

        nextJobTitle = ttk.Label(self, text="Next Job:", font=(self.f,18))
        nextJobTitle.place(relx=0.63, rely=0.03)

        #Next job address
        nextJobAddy = ttk.Label(self.nextBookingFrame, text="Address: ", font=(self.f, 11))
        nextJobAddy.place(relx=0.05, rely=0.05)
        nextJobList = self.GetNextJobAddress()
        nextJobAddress = ttk.Label(self.nextBookingFrame, text=nextJobList[0], font=(self.f, 11))
        nextJobAddress.place(relx=0.45, rely=0.05)

        #next job date
        nextJobDate = ttk.Label(self.nextBookingFrame, text="Date: ", font=(self.f, 11))
        nextJobDate.place(relx=0.05, rely=0.2)
        nextJobDateText = ttk.Label(self.nextBookingFrame, text=nextJobList[3], font=(self.f, 11))
        nextJobDateText.place(relx=0.45, rely=0.2)

        #next job start time
        nextJobStart = ttk.Label(self.nextBookingFrame, text="Start Time: ", font=(self.f, 11))
        nextJobStart.place(relx=0.05, rely=0.35)
        nextJobStartText = ttk.Label(self.nextBookingFrame, text=nextJobList[1], font=(self.f, 11))
        nextJobStartText.place(relx=0.45, rely=0.35)

        #next job end time
        nextJobEnd = ttk.Label(self.nextBookingFrame, text="End Time: ", font=(self.f, 11))
        nextJobEnd.place(relx=0.05, rely=0.5)
        nextJobEndText = ttk.Label(self.nextBookingFrame, text=nextJobList[2], font=(self.f, 11))
        nextJobEndText.place(relx=0.45, rely=0.5)

        #next job type
        nextJobType = ttk.Label(self.nextBookingFrame, text="Type: ", font=(self.f, 11))
        nextJobType.place(relx=0.05, rely=0.65)
        nextJobTypeText = ttk.Label(self.nextBookingFrame, text=nextJobList[5], font=(self.f, 11))
        nextJobTypeText.place(relx=0.45, rely=0.65)

        #next job skin used
        nextJobSkin = ttk.Label(self.nextBookingFrame, text="Price: ", font=(self.f, 11))
        nextJobSkin.place(relx=0.05, rely=0.8)
        nextJobSkinText = ttk.Label(self.nextBookingFrame, text=nextJobList[4], font=(self.f, 11))
        nextJobSkinText.place(relx=0.45, rely=0.8)


        last30DaysTitle = ttk.Label(self, text="Last 30 Days Stats:", font=(self.f,18))
        last30DaysTitle.place(relx=0.05, rely=0.03)

        last30DaysJobCount = ttk.Label(self.lastMonthStats, text="Jobs: ", font=(self.f, 11))
        last30DaysJobCount.place(relx=0.05, rely=0.1)
        last30DaysJobCountText = ttk.Label(self.lastMonthStats, text=self.GetLastMonthsJobCount(), font=(self.f, 11))
        last30DaysJobCountText.place(relx=0.45, rely=0.1)

        last30DayEarnings = ttk.Label(self.lastMonthStats, text="Earnings: ", font=(self.f, 11))
        last30DayEarnings.place(relx=0.05, rely=0.25)
        last30DayEarningsText = ttk.Label(self.lastMonthStats, text=self.GetLast30DayEarnings(), font=(self.f, 11))
        last30DayEarningsText.place(relx=0.45, rely=0.25)

        last30DaysAvgPrice = ttk.Label(self.lastMonthStats, text="Avg. Job Price: ", font=(self.f, 11))
        last30DaysAvgPrice.place(relx=0.05, rely=0.4)
        last30DaysAvgPriceText = ttk.Label(self.lastMonthStats, text=self.GetAvgJobPrice(), font=(self.f, 11))
        last30DaysAvgPriceText.place(relx=0.55, rely=0.4)


    def GetNextJobAddress(self):
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            sql = """SELECT Venues.booking_postcode, booking_startTime, booking_endTime, booking_date, booking_price, booking_type FROM Venues
                INNER JOIN Bookings 
                ON Venues.venue_id = Bookings.venue_id
                ORDER BY booking_date ASC;
            """

            cursor.execute(sql)
            result = cursor.fetchall()
        if len(result) < 1: #if no bookings
            return ["None", "None", "None", "None","None","None"]
        else:
            return result[0]

    def GetLastMonthsJobCount(self):
        todaysDate = self.GetTodaysDate()
        prev30Days = self.Minus30DaysFromDate(todaysDate)

        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(todaysDate), str(prev30Days))
            sql = """SELECT COUNT(Bookings.booking_id) FROM Bookings
            INNER JOIN Attendants 
            ON Bookings.attendant_id = Attendants.attendant_id
            WHERE Bookings.booking_date < ?
            AND Bookings.booking_date > ?
            """
            cursor.execute(sql, values)
            result = cursor.fetchone()
        return result[0] #return number of attendant bookings in the last 30 days

    def Minus30DaysFromDate(self, date):
        date = str(date)
        date = date.split("-")
        if str(date[1]) == "01":
            date[1] = "12"
            date[0] = int(date[0])-1
        else:
            toAdd = int(date[1]) - 1
            if date[1] == "11" or date[1] == "12":
                date[1] = toAdd
            else:
                date[1] = "0" + str(toAdd)

        if str(date[1]) == "04" or str(date[1]) == "06" or str(date[1]) == "09" or str(date[1]) =="11":
            if date[2] == "31":
                date[2] = "30"

        elif str(date[1]) == "02":
            date[2] = "28"

        newDate = (str(date[0])+"-"+str(date[1])+"-"+str(date[2]))
        newDate1 = datetime.fromisoformat(newDate)

        return newDate1

    def GetTodaysDate(self):
        return str(date.today())

    def GetLast30DayEarnings(self):
        todaysDate = self.GetTodaysDate()
        prev30Days = self.Minus30DaysFromDate(todaysDate)
        with sqlite3.connect("NEA_Customer.db")as db: #establish connection with db
            cursor = db.cursor()
            values = (str(todaysDate), str(prev30Days))
            sql = """SELECT SUM(Bookings.booking_price) FROM Bookings
            WHERE Bookings.booking_date < ?
            AND Bookings.booking_date > ?
            """

            cursor.execute(sql, values)
            result = cursor.fetchone()
        if result[0] is None: #if no bookings in the last 30 days
            return 0
        return result[0]

    def GetAvgJobPrice(self):
        jobs = self.GetLastMonthsJobCount()
        earnings = self.GetLast30DayEarnings()

        try:
            avgPrice = round(earnings/jobs, 2)
            return avgPrice
        except:
            return 0


app = Base()
app.geometry("500x500")
app.mainloop()
