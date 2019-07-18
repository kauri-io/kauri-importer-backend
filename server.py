from flask import Flask, request
import configparser
from tasks import convertMarkdown
import urllib
import requests
from medclient import exchangeAuth
from medium import Client
import tomd

# hard coded variables for right now
config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['DEFAULT']['CLIENT_ID'] # medium api client id
client_secret = config['DEFAULT']['CLIENT_SECRET'] # medium api client secret
callback_url = 'http://127.0.0.1:5000/callback/medium'

user_name = 'kauri_io'

client = Client(application_id=client_id, application_secret=client_secret)

app = Flask(__name__)

@app.route('/callback/frontend', methods=['GET', 'POST'])
def medium_callback():
    if request.args.get('state') and request.args.get('code'):
        state = request.args.get('state')
        code = request.args.get('code')
    
    data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_url,
            }

    # client actions
    auth = client.exchange_authorization_code(code, callback_url)
    user_dict = client.get_current_user()
    username = user_dict["username"]
    user_url = user_dict["url"]
    user_id = user_dict["id"]

    # serve html, create another endpoint
    return user_url

@app.route('/getlist', methods=['GET', 'POST']) 
def get_list():
    article_list = []
    headers = {"Accept": "application/json"}
    
    if request.args.get('type') == 'publication':
        #TODO: publication article parser script here
        url = request.args.get('url') + '/archive'
        r = request.get(url, headers=headers)
        if r.ok:
            articles = r.text.replace('])}while(1);</x>', '')
            data = json.loads(articles)
            years = data['payload']['archiveIndex']['yearlyBuckets']
            for year in years:
                if year['hasStories']:
                    year_url = url + '/' + year['year']
                    for x in range(1,13):
                        num = x if x < 10 else '0' + str(x)
                        r = requests.get(year_url + '/' + str(x), headers=headers)
                        if r.ok:
                            raw = r.text
                            raw_json = json.loads(r.text.replace('])}while(1);</x>', ''))
                            posts_raw = raw_json['payload']['references']['Post']
                            for key in posts_raw.items():
                                post_dict = {
                                        "id": posts_raw[key]["id"],
                                        "article_title": posts_raw[key]["title"],
                                        "article_subtitle": posts_raw[key]["previewContent"]["subtitle"],
                                        "article_slug": posts_raw[key]["uniqueSlug"]
                                        }
                                article_list.append(post_dict)

    elif request.args.get('type') == 'user':
        #TODO: normal username parser script here
        url = 'https://medium.com/@' + username + '/latest?format=json&limit=1000'
        r = requests.get(url, headers=headers)
        if r.ok:
            articles = r.text.replace('])}while(1);</x>', '')
            data = json.loads(articles)
            post_json = data["payload"]["references"]["Post"]
            for key in post_json:
                data_dict = {
                        "id": post_json[key]["id"],
                        "article_title": post_json[key]["title"],
                        "article_subtitle": post_json[key]["previewContent"]["subtitle"],
                        "article_slug": post_json[key]["uniqueSlug"]
                        }
                article_list.append(data_dict)
    
    return article_list

@app.route('/userselection', methods=['GET', 'POST'])
def builduserselection():
    articles_to_build = []
    headers = {"Accept": "text/html"}
    articles_to_parse = request.args.get('selected_articles')
    for each in articles_to_parse:
        url = 'https://www.medium.com/' + articles_to_parse[each]['article_slug']
        r = request.get(url, headers=headers)
        a = BeautifulSoup(r.text)
        main = a.main

        for x in main.findAll('link'):
            x.extract()

        for x in main.findAll('hr'):
            x.extract()

        for x in main.findAll('nav'):
            x.extract()

        for x in main.findAll('path'):
            x.extract()
    
        soup_string = str(main)
        tomarkdown = tomd.Tomd(soup_string).markdown
        
        md_dict = {
                "article_id": articles_to_parse[each]['id'],
                "article_title": articles_to_parse[each]['title']
                "article_md": tomarkdown
                }

        articles_to_build.append(tomarkdown)

if __name__ == '__main__':
    app.run(debug=True)