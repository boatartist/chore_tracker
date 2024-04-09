from flask import Flask, render_template, flash, request, redirect, url_for
import string
import os
from datetime import datetime

'''The Child class imports chores from the specific file for a given child, 
calculating how much is owed and allowing the file data to be accessed and modified,
It is only referenced by the Parent class, with methods to change the amount owed, assign and complete chores, 
return a list of all chores, and save data back to the file'''
class Child:
    def __init__(self, name, parent):
        self.owed = 0
        #chores are stored in a dictionary, with the name as the key and other info in a list: [cost, dateassigned, status]
        self.chores = {}
        self.name = name
        self.parent = parent
        chores = []
        #if the child doesn't have a file, it creates one
        try:
            f = open(f'users/{parent}/{name}.txt', 'x')
            self.save()
        #otherwise the information is read and stored in a list before being put in the self.chores dict
        except FileExistsError:
            with open(f'users/{parent}/{name}.txt', 'r') as f:
                f = f.read().strip('\n').split('\n')
                self.owed = float(f[0].rstrip(string.punctuation))
                chores.extend(f[1:])
        for chore in chores:
            things = chore.split('@')
            self.chores[things[0]] = things[1:]
    
    #this function writes all data to a file, with the amount owed to the child on the first line, and the chores on subsequent lines
    def save(self):
        to_write = ''
        to_write += f'{self.owed}\n'
        for chore, info in self.chores.items():
            to_write += f'{chore}@{"@".join(info)}\n'
        with open(f'users/{self.parent}/{self.name}.txt', 'w') as f:
            f.write(to_write)

    #this decreases the amount owed
    def get_payed(self, amount):
        self.owed -= amount
        self.save()
    
    #this will add a new chore to the child's file/dictionary of chores
    def assign_new(self, chore, cost, dateassigned):
        self.chores[chore] = [cost, dateassigned, 'incomplete']
        self.save()

    #changes a chore's status from incomplete to complete
    def complete_chore(self, chore):
        cost, dateassigned, status = self.chores.get(chore, ['N/A', 'N/A', 'incomplete'])
        self.chores[chore] = [cost, dateassigned, 'complete']
        self.owed += float(cost.rstrip(string.punctuation).lstrip('$'))
        self.save()
    
    #returns a list of chores to be displayed on the webpage
    def list_chores(self):
        listed = []
        for chore, info in self.chores.items():
            mini = []
            mini.append(chore)
            mini.extend(info)
            listed.append(mini)
        #sorts list so that items are grouped by status and incomplete items are on top
        listed.sort(key=lambda item: item[-1])
        listed.reverse()
        return listed

'''The parent class takes an existing user and finds all children files, initialising and storing them'''
class Parent:
    def __init__(self, name):
        self.name = name
        self.children = {}
        #finds all existing files for children and loads data, os module used to avoid risk of compound error from children being stored in multiple places.
        files = os.listdir(f'users/{name}')
        for f in files:
            if f.endswith('.txt'):
                self.children[f.strip('.txt')] = Child(f.strip('.txt'), self.name)

    #runs the get_payed function on the given child, decreasing the amount owed
    def pay(self, amount, child):
        self.children[child].get_payed(amount)

    #assigns a chore to the given child
    def assign_new(self, child, chore, cost, dateassigned):
        self.children[child].assign_new(chore, cost, dateassigned)
    
    #mark chore as complete
    def complete_chore(self, child, chore):
        self.children[child].complete_chore(chore)

    #creates a new child
    def new_child(self, child):
        self.children[child] = Child(child, self.name)

    #returns how much a child is owed
    def owed(self):
        owed = {}
        for key, child in self.children.items():
            owed[key] = child.owed
        return owed

    #returns a dictionary of all chores for each child
    def all_tasks(self):
        all_tasks = {}
        for key, child in self.children.items():
            all_tasks[key] = child.list_chores()
        return all_tasks


#flask setup stuff
app = Flask(__name__)
#I need this somehow, something to do with being logged in i think
app.secret_key = "secret key"

#login page
@app.route('/', methods=('GET', 'POST'))
def login():
    users = {}
    #finds all existing users/passwords from file and stores in dictionary
    with open('users.txt', 'r') as f:
        f = f.read().strip('\n').split('\n')
        for line in f:
            person, pwd = line.split('/')
            users[person] = pwd
    #if the user submits the form with a username and password
    if request.method == 'POST':
        print(request.form)
        print('Accessing variables')
        user = request.form['user'].lower()
        print('got user')
        password = request.form['password']
        print('got password')
        #if the user has indicated that they want to create a new username and password this will not be none
        new_user = request.form.get('new_user', None)
        #if they want there to be a new user, by checking the checkbox
        if new_user == 'on' and user not in users.keys():
            #adds a new user to the dictionary
            users[user] = password
            #adds to end of file
            with open('users.txt', 'a') as f:
                f.write(f'\n{user}/{password}')
            os.mkdir(f'users/{user}/')
            #redirects to main page
            return redirect(url_for('main', user=user))
        #if the user is not an existing user
        elif not user in users.keys():
            print('There\'s a new user')
            flash('No user with this username')
            #reloads login page with option to tick checkbox and unhide user
            return render_template('login.html', hidden='')
        #if they successfully login
        elif users[user] == password:
            print('logged in, redirecting')
            #redirects to main page
            return redirect(url_for('main', user=user))
        #if the password is just wrong
        else:
            print('you\'re wrong')
            flash('Incorrect password for user')
    #html template for login page
    return render_template('login.html', hidden='hidden')

#main page
@app.route('/main/<user>', methods=('GET', 'POST'))
def main(user, to_flash=[]):
    '''the flash() function gives a list of updates that are displayed at the top of the website, 
    indicating recent actions, this takes an optional list from other functions that may update the site, 
    such as adding a new chore'''
    for i in to_flash:
        flash(i)
    user = user.lower()
    #confirms that user exists in the program, otherwise redirects to login page, this prevents unauthorised access
    exists = False
    with open('users.txt', 'r') as f:
        real = f.read().strip('\n').split('\n')
        for line in real:
            if '/' in line:
                if line.split('/')[0] == user:
                    exists = True
                    break
    if exists:
        parent = Parent(user)
    else:
        return redirect(url_for('login'))
    #dictionary of how much the parent owes each child
    owed = parent.owed()
    #dictionary of chores assigned to each child
    all_tasks = parent.all_tasks()
    return render_template('home.html', owed=owed, user=user, all_chores=all_tasks)

'''When the relevant form is submitted within the html, 
It redirects to this page, before redirecting back to the main page
This function retrieves form data and temporarily creates a parent object to manage functions and save new data
'''
@app.route('/paychild/<user>', methods=['POST'])
def paychild(user):
    child = request.form['child']
    amount = request.form.get('amount', 0)
    parent = Parent(user)
    parent.pay(float(amount), child)
    return redirect(url_for('main', user=user, to_flash=[f'Payed ${amount} to {child}']))

'''Creates a new child for the user from a form submission, before redirecting to main page'''
@app.route('/newchild/<user>', methods=['POST'])
def newchild(user):
    name = request.form['name']
    print(user)
    parent = Parent(user)
    parent.new_child(name)
    return redirect(url_for('main', user=user, to_flash=[f'Created new child: {name}']))

'''Assigns a new chore to a given child,
takes child name, chore name, value of chore and user from html data, 
finds date automatically with datetime module
redirects to main page'''
@app.route('/assign/<user>', methods=['POST'])
def assign(user):
    child = request.form['assign_to']
    chore = request.form['chore_name']
    value = request.form['money']
    date = datetime.now().strftime('%d/%m/%Y')
    parent = Parent(user)
    parent.assign_new(child, chore, value, date)
    return redirect(url_for('main', user=user, to_flash=[f'Assigned {child} chore: {chore} for ${value}']))

'''Marks given chore as completed, then redirects back'''
@app.route('/complete_chore/<user>', methods=['POST'])
def complete_chore(user):
    print('starting thingo')
    child = request.form['child']
    print('child got')
    chore = request.form['chore_name']
    print('chore got')
    parent = Parent(user)
    print('has parent')
    parent.complete_chore(child, chore)
    print('completed chore')
    return redirect(url_for('main', user=user, to_flash=[f'{child} completed chore {chore}']))

app.run()
