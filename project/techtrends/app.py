import sqlite3
import traceback
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

global total_posts
total_posts = 0

global total_database_conections
total_database_conections = 0

global health_flag
health_flag = 1

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    global health_flag
    try:
        post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
        global total_database_conections
        total_database_conections = total_database_conections + 1
        health_flag = 1
        app.logger.info('Post Fetch Successfull')
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
        health_flag = 0
        app.logger.info('Post Fetch Unsuccessfull')
    finally:
        connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    global health_flag
    try:
        posts = connection.execute('SELECT * FROM posts').fetchall()
        global total_database_conections
        total_database_conections = total_database_conections + 1
        health_flag = 1
        app.logger.info('Index Fetch Successfull')
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
        health_flag = 0
        app.logger.info('Index Fetch Unsuccessfull')
    finally:
        connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    global health_flag
    if post is None:
      app.logger.info('Attempt Made TO Reads A NON Existing POST')
      health_flag = 0
      return render_template('404.html'), 404
    else:
      app.logger.info('Post Read with Title = '+ post['title'] + ' , Successfull' ) 
      health_flag = 1
      return render_template('post.html', post=post)

# Define the About Us page 
@app.route('/about')
def about():
    app.logger.info('One Request to Read About US Page Successfull')
    return render_template('about.html')

# Define the Healthcheck endpoint
@app.route('/healthz')
def healthz():
    global health_flag
    if health_flag == 1 :
        response = app.response_class(
                response=json.dumps({"result":"OK - healthy"}),
                status=200,
                mimetype='application/json')
    else:
        response = app.response_class(
                response=json.dumps({"result":"ERROR - unhealthy"}),
                status=500,
                mimetype='application/json')

    app.logger.info('Healthcheckpoint Request Successfull')
    return response

# Define the Metrics endpoint
@app.route('/metrics')
def metrics():
    response = app.response_class(
            response=json.dumps({"status":"success","code":0,"data":{"db_connection_count":total_database_conections,"post_count": total_posts}}),
            status=200,
            mimetype='application/json'
    )

    app.logger.info('Metrics Request Successfull')
    return response

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global health_flag
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            try:
                connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                            (title, content))
                connection.commit()
                global total_posts
                total_posts = total_posts + 1
                global total_database_conections
                total_database_conections = total_database_conections + 1
                health_flag = 1
                app.logger.info('One Post Creation Request With Tittle = '+ title +', Is Successfull' )
            except sqlite3.Error as er:
                print('SQLite error: %s' % (' '.join(er.args)))
                print("Exception class is: ", er.__class__)
                print('SQLite traceback: ')
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))
                health_flag = 0
                app.logger.info('Post Fetch Unsuccessfull')
            finally:
                connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111', debug=True)

