import os
import sys
import json
import logging
import requests
from flask import Flask, jsonify,request
from builder.backend.wordpress import WpConverter
from sync import syncToKauri
from flask_cors import CORS


#create the flask app
app = Flask(__name__)
kauri_gateway = 'https://api.kauri.io/graphql'
cors = CORS(app)


"""
user flow:
1) determine where user is importing content from
2) user chooses and provides information: url, xml file
3) main file logic routes data to appropriate backend builder

the way we did this in the importer was using flask's request.args.get() module
see link: http://flask.pocoo.org/docs/1.0/reqcontext/
"""

#home screen
@app.route('/')
def entry_point():
    # ask user where they're importing documentation from
    return('Home page: go to /link')

#import screen
@app.route('/import', methods =['GET', 'POST'])
def retrieve_content():
    #receives the file
    file = request.get_json('body')

    # convert the file, change to a string and put it
    # in json object form to send
    if file != '':
        wp_article_list = WpConverter(file)
        wp_string = str(wp_article_list)
        wp_json_object = json.loads(wp_string)

        #change the response to the article list and send it back
        response = jsonify({'data': wp_json_object})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

#sync screen
@app.route('/sync', methods = ['GET','POST'])
def send_articles():

    articles = request.get_json('body')

    #individually send the articles
    for x in range(len(articles)):
        object = articles[x]
        try:
            syncToKauri(object)
        except:
            #if an article doesn't send, return error right away
            response = jsonify({'success': False})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response



    #return response
    response = jsonify({'success': True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response



#allows for debugging
if __name__ == '__main__':
    app.run(debug=True)
