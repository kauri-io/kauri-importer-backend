from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
import urllib
import requests
import json
import logging
import pprint
import configparser

from wordpress.builder.backend.wordpress import WpConverter
from wordpress.sync import syncToKauri

from urllib.parse import urlparse, quote, unquote
from posixpath import join as urljoin

from my_parser import parse_post_detail
from post_wrangler import (
    get_publ_list,
    pull_user_list,
    get_solo_article,
    is_single_article,
)

user_name = 'kauri_io'

app = Flask(__name__, static_folder="public")
# load default config file
app.config.from_object('config.default')
app.config.from_envvar('APP_CONFIG_FILE') # env var needs to be absolute path 

cors = CORS(app)

@app.route('/callback/frontend', methods=['GET', 'POST'])
def authenticate():
    url = 'https://api.medium.com/v1/tokens'

    if request.args.get('state') and request.args.get('code'):
        state = request.args.get('state')
        code = request.args.get('code')
    data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": 'http://9d9c388e.ngrok.io'
            }

    headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "Content-Type": "application/x-www-form-urlencoded"
            }

    req = requests.post(url, headers=headers, data=data)

    access_token = None
    if req.ok:
        access_token = req.json()["access_token"]

    # get current user's details
    headers["Authorization"] = "Bearer %s" % access_token
    get = requests.get('https://api.medium.com/v1/me', headers=headers)
    if get.ok:
        resp = get.json()['data']
        username = resp["username"]
        url = resp["url"]
        img_url = resp["imageUrl"]
        user_id = resp["id"]
        name = resp["name"]
    else:
        print('user get request failed.')

    publist = requests.get('https://api.medium.com/v1/users/' + user_id +
            '/publications', headers=headers)

    publication_list = []
    if publist.ok:
        data = publist.json()['data']
        for each in data:
            pub_dict = {
                    "pub_id": each["id"],
                    "pub_name": each["name"],
                    "pub_desc": each["description"],
                    "pub_url": each["url"],
                    "pub_imgurl": each["imageUrl"]
                    }
            publication_list.append(each)
    response = jsonify({"publications": publication_list, "name": name, "username": username, "url": url})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/getlist', methods=['GET', 'POST'])
def get_list():
    error = False
    single_article = is_single_article(request.args.get('url'))

    if single_article:
        try:
            complete_list = get_solo_article(single_article)
        except:
            error = True
            logging.info('URL is not a single article. Continuing...')

    elif request.args.get('type') == 'publication':
        url = urlparse(request.args.get('url'))
        print(url.geturl())
        arch_url = urljoin(url.geturl(), 'archive')
        try:
            print('loading get list from post_wrangler')
            complete_list = get_publ_list(arch_url)
        except:
            error = True
            logging.warning('application did not retrieve list of PUBLICATION articles')

    elif request.args.get('type') == 'user':
        url = urlparse(request.args.get('url'))
        user_url = url.geturl()
        try:
            complete_list = pull_user_list(user_url)
        except:
            error = True
            logging.warning('application did not retrieve list of USER articles')
    else:
        logging.warning('application did not retrieve ANY articles')

    if not error:
        response = jsonify({"articles": complete_list})

        response.headers.add('Access-Control-Allow-Origin', '*')
    else:
        response = abort(400)

    return response

@app.route('/import', methods=['POST'])
def importer():
    md_output = []
    token = request.get_json()['token']
    env_url = request.get_json()['env_url']
    headers = {"Content-Type": "application/json"}
    headers['X-Auth-Token'] = 'Bearer %s' % token
    # hardcoded for right now
    # kauri_gateway = 'https://api.kauri.io/graphql'
    # username = 'kauri_io'
    url = request.get_json()['url']
    articles_to_build = request.get_json()['articles']
    for each in articles_to_build:
        single_article = is_single_article(url)
        if not single_article:
            print('Multiple article')
            print(url)
            markdown = parse_post_detail(url.rstrip('/') + '/' + each['article_slug'], token)
        else:
            print('Single article')
            print(url)
            markdown = parse_post_detail(url, token)
        subNewArticle_req = {
                "query":"mutation submitNewArticle($title: String, $content: String, $attributes: Map_String_StringScalar) { submitNewArticle (title: $title, content: $content, attributes: $attributes    ) {hash}   }",
                "variables": {
                    "title": each["article_title"],
                    "content": json.dumps({"markdown":markdown}, separators=(',', ':')),
                    "attributes": {
                        "origin_name": "medium",
                        "origin_url": url,
                    },
                },
                "operationName": "submitNewArticle"
                }
        print(subNewArticle_req['variables']['content'])
        p = requests.post(KAURI_GATEWAY, headers=headers, data=json.dumps(subNewArticle_req))
        if p.ok:
            post_success = {"article_id": each["id"], "success": "True"}
            md_output.append(post_success)
            #TODO: error handling
            #TODO: maybe some logging here
        else:
            post_failure = {"article_id": each["id"], "success": "False"}
            md_output.append(post_failure)
    response = jsonify({'success': True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

#recieves the wordpress file, converts, it and sends it back
@app.route('/importwp', methods =['GET', 'POST'])
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


# recieves the wordpress file and sends it to kauri article by article
@app.route('/syncwp', methods = ['POST'])
def send_articles():

    articles = request.get_json()['selected']
    token = request.get_json()['token']
    config = configparser.RawConfigParser()
    config.read('config.ini')
    jwt = config['GATEWAY']['JWT_TOKEN']
    token = token if token  is not None else jwt 
    #individually send the articles
    for a in articles:
        try:
            print("Trying")
            syncToKauri(a, token)
        except:
            print("Failed")
            #if an article doesn't send, return error right away
            response = jsonify({'success': False})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    #return response
    response = jsonify({'success': True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

#if the user imports through a wordpress link, the link
# is recieved and the article is converted
# the converted article is then sent back to wordpress-choose-article.js
@app.route('/importwpLink', methods = ['POST'])
def wp_link():

    # the link is recieved in a request
    link = request.get_json('body')
    articles = []
    x = 1

    #loops through each rss feed page
    while x != "!":

        # a new link is generated each time to loop through the pages
        newLink = "%s%s%i" %(link,"/feed/?paged=",x)

        #request gets page source
        r = requests.get(newLink)
        page_source = r.text

        # sends to be converted to markdown
        wp_article_list = WpConverter(page_source)
        wp_string = str(wp_article_list)
        wp_json_object = json.loads(wp_string)

        #checks to see if it is the last page and ends the loop
        if(wp_json_object == []):
            x = "!"
        #if it is not the last page..
        else:
            # adds the articles to a list to send back as the response
            for y in range(len(wp_json_object)):
                articles.append(wp_json_object[y])
            x +=1


    #change the response to the article list and send it back
    response = jsonify({'data': articles})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/')
def main():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
  return send_from_directory('public', path)

if __name__ == '__main__':
    app.run(debug=True)
