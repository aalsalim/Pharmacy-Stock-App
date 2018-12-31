from functools import wraps
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash  # noqa
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Medication, Pharmacy, User
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Pharmacy Stock Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///pharmacy.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


# --------------------------------------
# CRUD for pharmacies
# --------------------------------------
# CREATE - New pharmacy
@app.route('/pharmacies/new', methods=['GET', 'POST'])
@login_required
def newPharmacy():
    """Allows user to create new pharmacy"""
    if request.method == 'POST':
        print login_session
        if 'user_id' not in login_session and 'email' in login_session:
            login_session['user_id'] = getUserID(login_session['email'])
        newPharmacy = Pharmacy(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(newPharmacy)
        session.commit()
        flash("New pharmacy created!", 'success')
        return redirect(url_for('showHome'))
    else:
        return render_template('new_pharmacy.html')


# READ - home page, show latest medications and pharmacies
@app.route('/')
@app.route('/pharmacies/')
def showHome():
    """Returns page with all pharmacies and recently added medications"""
    pharmacies = session.query(Pharmacy).all()
    medications = session.query(Medication).order_by(Medication.id.desc())
    quantity = medications.count()
    if 'username' not in login_session:
        return render_template(
            'public_home.html',
            pharmacies=pharmacies, medications=medications, quantity=quantity)
    else:
        return render_template(
            'home.html',
            pharmacies=pharmacies, medications=medications, quantity=quantity)


# DELETE a pharmacy
@app.route('/pharmacies/<int:pharmacy_id>/delete/', methods=['GET', 'POST'])
@login_required
def deletePharmacy(pharmacy_id):
    """Allows user to delete an existing pharmacy"""
    pharmacyToDelete = session.query(
        Pharmacy).filter_by(id=pharmacy_id).one()
    if pharmacyToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        session.delete(pharmacyToDelete)
        flash('%s Successfully Deleted' % pharmacyToDelete.name, 'success')
        session.commit()
        return redirect(
            url_for('showHome', pharmacy_id=pharmacy_id))
    else:
        return render_template(
            'delete_pharmacy.html', pharmacy=pharmacyToDelete)


# EDIT a pharmacy
@app.route('/pharmacies/<int:pharmacy_id>/edit/', methods=['GET', 'POST'])
@login_required
def editPharmacy(pharmacy_id):
    """Allows user to edit an existing pharmacy"""
    editedPharmacy = session.query(
        Pharmacy).filter_by(id=pharmacy_id).one()
    if editedPharmacy.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        if request.form['name']:
            editedPharmacy.name = request.form['name']
            flash(
                'Pharmacy Successfully Edited %s' % editedPharmacy.name,
                'success')
            return redirect(url_for('showHome'))
    else:
        return render_template(
            'edit_pharmacy.html', pharmacy=editedPharmacy)


# --------------------------------------
# CRUD for medications
# --------------------------------------
# READ - show medications
@app.route('/pharmacies/<int:pharmacy_id>/')
@app.route('/pharmacies/<int:pharmacy_id>/medications/')
def showMedications(pharmacy_id):
    """returns Medications in pharmacy"""
    pharmacy = session.query(Pharmacy).filter_by(id=pharmacy_id).one()
    pharmacies = session.query(Pharmacy).all()
    creator = getUserInfo(pharmacy.user_id)
    medications = session.query(
        Medication).filter_by(
            pharmacy_id=pharmacy_id).order_by(Medication.id.desc())
    quantity = medications.count()
    return render_template(
        'medication_menu.html',
        pharmacies=pharmacies,
        pharmacy=pharmacy,
        medications=medications,
        quantity=quantity,
        creator=creator)


# CREATE Medication
@app.route('/pharmacies/medication/new', methods=['GET', 'POST'])
@login_required
def newMedication():
    """return "This page will be for making a new medication" """
    pharmacies = session.query(Pharmacy).all()
    if request.method == 'POST':
        addNewMedication = Medication(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            pharmacy_id=request.form['pharmacy'],
            user_id=login_session['user_id'])
        session.add(addNewMedication)
        session.commit()
        flash("New medication created!", 'success')
        return redirect(url_for('showHome'))
    else:
        return render_template('new_medication.html', pharmacies=pharmacies)


# READ Medication - selecting medication show specific information about it
@app.route('/pharmacies/<int:pharmacy_id>/medication/<int:medication_id>/')
def showMedication(pharmacy_id, medication_id):
    """returns medication"""
    pharmacy = session.query(Pharmacy).filter_by(id=pharmacy_id).one()
    medication = session.query(
        Medication).filter_by(id=medication_id).one()
    creator = getUserInfo(pharmacy.user_id)
    return render_template(
        'medication_menu_item.html',
        pharmacy=pharmacy, medication=medication, creator=creator)


# DELETE Medication
@app.route(
    '/pharmacies/<int:pharmacy_id>/medication/<int:medication_id>/delete',
    methods=['GET', 'POST'])
@login_required
def deleteMedication(pharmacy_id, medication_id):
    """return "This page will be for deleting a Medication" """
    medicationToDelete = session.query(
        Medication).filter_by(id=medication_id).one()
    if medicationToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        session.delete(medicationToDelete)
        session.commit()
        flash('Medication Successfully Deleted', 'success')
        return redirect(url_for('showHome'))
    else:
        return render_template(
            'delete_medication.html', medication=medicationToDelete)


# UPDATE Medication
@app.route(
    '/pharmacies/<int:pharmacy_id>/medication/<int:medication_id>/edit',
    methods=['GET', 'POST'])
@login_required
def editMedication(pharmacy_id, medication_id):
    """return "This page will be for making a updating medication" """
    editedMedication = session.query(
        Medication).filter_by(id=medication_id).one()
    if editedMedication.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        if request.form['name']:
            editedMedication.name = request.form['name']
        if request.form['description']:
            editedMedication.description = request.form['description']
        if request.form['price']:
            editedMedication.price = request.form['price']
        if request.form['pharmacy']:
            editedMedication.pharmacy = request.form['pharmacy']
        session.add(editedMedication)
        session.commit()
        flash("Medication updated!", 'success')
        return redirect(url_for('showHome'))
    else:
        pharmacies = session.query(Pharmacy).all()
        return render_template(
            'edit_medication.html',
            pharmacies=pharmacies,
            medication=editedMedication)


# --------------------------------------
# Login Handling
# --------------------------------------

# Login route, create anit-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# CONNECT - Google login get token
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if not create new user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    flash("you are now logged in as %s" % login_session['username'], 'success')
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # reset the user's session
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # token given is invalid
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# User helper functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    print login_session
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            if 'gplus_id' in login_session:
                del login_session['gplus_id']
            if 'credentials' in login_session:
                del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.", 'success')
        return redirect(url_for('showHome'))
    else:
        flash("You were not logged in", 'danger')
        return redirect(url_for('showHome'))


# --------------------------------------
# JSON APIs to show Medication information
# --------------------------------------
@app.route('/api/v1/medication.json')
def showMedicationJSON():
    """Returns JSON of all medications in pharmacy"""
    medications = session.query(Medication).order_by(Medication.id.desc())
    return jsonify(Medication=[i.serialize for i in medications])


@app.route(
    '/api/v1/pharmacies/<int:pharmacy_id>/medication/<int:medication_id>/JSON')
def MedicationJSON(pharmacy_id, medication_id):
    """Returns JSON of selected medication in pharmacy"""
    Medication = session.query(
        Medication).filter_by(id=medication_id).one()
    return jsonify(Medication=Medication.serialize)


@app.route('/api/v1/pharmacies/JSON')
def pharmaciesJSON():
    """Returns JSON of all pharmacies"""
    pharmacies = session.query(Pharmacy).all()
    return jsonify(pharmacies=[r.serialize for r in pharmacies])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
