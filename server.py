"""Server for bibliotech app"""

from flask import (Flask, render_template, redirect, request, 
    jsonify, session, make_response)

from model import connect_to_db
from crud import *

# was using this to parse decimal but now it's not there anymore....maybe only in seed_db file
import simplejson as json

import util

from jinja2 import StrictUndefined

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = "1123513"
app.jinja_env.undefined = StrictUndefined

# find wildcard to make reload always take you home
@app.route('/')
def homepage():
    """View homepage."""

    # if user logged in show homepage, otherwise redirect to login screen
    return render_template('index.html')


@app.route('/userLogin', methods=['POST'])
def login():
    """Log In user."""

    req = request.get_json()

    username = req['username']
    pwd = req['pwd']

    user = get_user(username)

    login_resp = {
        'message': None,
        'error': None,
        'user_id': None,
        'username': None,
    }

    user_id = None
    username = None

    if user is not None:
        # check password
        if pwd == user.password:
            login_resp['user_id'] = user.id
            login_resp['username'] = user.username
            login_resp['message'] = 'OK'
            status_code = 200
            user_id = str(user.id)
            username = user.username
        else:
            login_resp['error'] = 'Password is incorrect'
            login_resp['message'] = 'Unauthorized'
            status_code = 401
    else:
        login_resp['error'] = 'User does not exists'
        login_resp['message'] = 'Unauthorized'
        status_code = 401

    resp = make_response(jsonify(login_resp), status_code)
    resp.set_cookie('user_id', user_id)
    resp.set_cookie('username', username)
    return resp


@app.route('/createAccount', methods=['POST'])
def create_account():
    """Create Account"""

    req = request.get_json()

    username = req['username']
    pwd = req['pwd']
    pwd_dup = req['pwdDup']

    # see if user exists
    user = get_user(username)

    response = {
        'message': None,
        'error': None,
        'user_id': None,
        'username': None,
    }

    if user is None:
        # check password
        if pwd == pwd_dup:
            # create user, if successful
            user = create_user(username, pwd)
            if user is not None:
                response['message'] = 'OK'
                status_code = 200
            else:
                response['message'] = 'Could not create new user'
                status_code = 422
        else:
            response['error'] = 'Password is inconsistent'
            response['message'] = 'Unauthorized'
            status_code = 401
    else:
        response['error'] = 'User already exists'
        response['message'] = 'Unauthorized'
        status_code = 422

    return (jsonify(response), status_code)


@app.route('/api/search', methods=['POST'])
def perform_search():
    """Perform simple search and return results as list"""

    # needed to return which books belong to user 
    logged_in_user_id = request.cookies["user_id"]
    
    req = request.get_json()

    # strings are None if not considered in search
    title_string = req['titleString']
    author_lname_string = req['authorLnameString']
    tag_string = req['tagListString']       # comma separated string of tags
    isbn_string = req['isbnString']
    search_type = req['searchType']         # advanced, basic
    user_id = req['userId']
    

    tag_list = util.string_to_list(tag_string) if tag_string != None else None
    
    response = {
        'message': None,
        'error': None,
        'book_list': None,
        'user_id': user_id,
    }

    # if advanced search, get fuzzy/exact search booleans 
    if search_type == 'advanced':
        # extra fields for advanced search
        author_fname_string = req['authorFnameString']

        # search specifiers (fuzzy/exact)
        exact_title = req['exactTitle']
        exact_fname = req['exactFname']
        exact_lname = req['exactLname']
    
        books = get_books_by_various_advanced(title=title_string, 
                                            author_fname=author_fname_string,
                                            author_lname=author_lname_string, 
                                            tag_list=tag_list, 
                                            user_id=user_id,
                                            exact_title=exact_title,
                                            exact_fname=exact_fname,
                                            exact_lname=exact_lname)
    # basic search
    else:
        books = get_books_by_various(title=title_string, 
                                    author_lname=author_lname_string, 
                                    tag_list=tag_list, 
                                    isbn=isbn_string,
                                    user_id=user_id)

    response['book_list'] = util.books_to_dictionary(books, logged_in_user_id)
    
    status_code = 200
    if response['book_list'] == []:
        status_code = 204 
        

    return (jsonify(response), status_code)


@app.route('/book/<bookId>')
def get_book(bookId):
    """Get single book data to populate /book/{id} page"""

    book_id = bookId

    # needed to return if book belongs to user 
    logged_in_user_id = request.cookies["user_id"]

    response = {
        'message': None,
        'error': None,
        'book': None,
    }

    book = get_book_by_id(book_id)

    if book != None:
        response['book'] = util.book_to_dictionary(book, logged_in_user_id)

    status_code = 204 if book == None else 200

    return (jsonify(response), status_code)
    

@app.route('/user/<bookId>/add', methods=['PUT'])
def add_book_user(bookId):
    """Add a user from a specific book"""

    book_id = bookId

    # get logged in user
    logged_in_user_id = request.cookies["user_id"]

    book_record = get_book_by_id(book_id)
    user_record = get_user_by_id(logged_in_user_id)

    # add in check that user and book exist

    create_users_books_relationship(book_record, user_record)

    response = {
        'type': 'add',
        'book_id': book_id,
        'user_id': logged_in_user_id
    }

    return (jsonify(response), 200)


@app.route('/user/<bookId>/delete', methods=['DELETE'])
def delete_book_user(bookId):
    """Add or remove a user from a specific book"""

    book_id = bookId

    # get logged in user
    logged_in_user_id = request.cookies["user_id"]

    book_record = get_book_by_id(book_id)
    user_record = get_user_by_id(logged_in_user_id)

    # add in check that user and book exist

    remove_users_books_relationship(book_record, user_record)
    remove_users_books_rating(book_id, logged_in_user_id)

    # update avg_rating
    util.calculate_update_avg_rating(book_id)

    response = {
        'type': 'delete',
        'book_id': book_id,
        'user_id': logged_in_user_id
    }

    return (jsonify(response), 200)


@app.route('/book/api/rating', methods=['POST'])
def update_rating():
    """Update Rating.score and Rating.review based on request"""

    req = request.get_json()

    new_score = req['rating']   
    new_review = req['review']
    book_id = req['bookId']        
    user_id = req['userId']

    update_book_user_score(book_id, user_id, new_score)
    update_book_user_review(book_id, user_id, new_review)

    util.calculate_update_avg_rating(book_id)

    book = get_book_by_id(book_id)

    response = {
        'message': None,
        'error': None,
        'book': None,
    }

    if book != None:
        response['book'] = util.book_to_dictionary(book, user_id)

    status_code = 204 if book == None else 200

    return (jsonify(response), status_code)


@app.route('/api/recommend', methods=['POST'])
def get_recommendation():
    """Given a userid, return a single book recommendation"""

    req = request.get_json()
    
    user_id = req['userId']

    response = {
        'message': None,
        'error': None,
        'book': None,
    }

    book_id = util.get_book_recommendation(user_id)
    book = None
    # book_id is string if error returned
    if isinstance(book_id, str) == True:
        response['error'] = book_id
    else:
        book = get_book_by_id(book_id)

        if book != None:
            response['book'] = util.book_to_dictionary(book, user_id)

    if book == None: 
        if response['error'] == None:
            status_code = 204
        else:
            status_code = 404
    else:
        status_code = 200

    return (jsonify(response), status_code)


if __name__ == '__main__':
    connect_to_db(app)
    app.run(host='0.0.0.0', debug=True)