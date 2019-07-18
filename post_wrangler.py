import requests
import json
import logging
import datetime
import re

remove = '])}while(1);</x>' 
headers = {"Accept": "application/json"} 

def get_publ_list(url):
    r = requests.get(url, headers=headers)
    if r.ok:
        raw_json = json.loads(r.text.replace(remove, ''))
        
        try:
            years_list = get_year_posts(raw_json, url) 
        except:
            logging.warning('failed obtaining publication years')
        
        try:
            url_list = get_month_posts(years_list, url)
        except:
            logging.warning('failed obtaining posts per month')
        
        try:
            article_list = pull_publication_list(url_list, url)
        except:
            logging.warning('failed pulling entire article list')

    else:
        logging.warning('https request is failing 1')

    return article_list

def get_year_posts(raw_json, url):
    years_list = [] 
    archIndex = raw_json['payload']['archiveIndex']['yearlyBuckets']
    for year in archIndex:
        if year['hasStories']:
            year_url = url + '/' + year['year']
            years_list.append(year_url)
        else:
            logging.warning('could not find years')
    
    if len(years_list) == 0:
        year_url = url + '/' + str(datetime.datetime.now().year)
        years_list.append(year_url)

    return years_list

def get_month_posts(years_list, url):
    url_list = []
    
    for each in years_list:
        r = requests.get(each, headers=headers)
        if r.ok:
            data = json.loads(r.text.replace(remove, ''))
            months = data['payload']['archiveIndex']
            if len(months['monthlyBuckets']) == 0:
                url_list.append(each) 
            elif months['monthlyBuckets']:
                for month in months['monthlyBuckets']:
                    new_url = url + '/' + month['year'] + '/' + month['month']
                    url_list.append(new_url)
        
    return url_list

def pull_publication_list(url_list, url):
    complete_list = []
    seen = set()
    
    for each in url_list:
        r = requests.get(each, headers=headers) 

        if r.ok:
            data = json.loads(r.text.replace(remove, ''))
            posts_raw = data['payload']['references']['Post']
        
            for k,v in posts_raw.items():
                post_dict = {
                    "id": posts_raw[k]["id"],
                    "article_title": posts_raw[k]["title"],
                    "article_subtitle": posts_raw[k]["previewContent"]["subtitle"],
                    "article_slug": posts_raw[k]["uniqueSlug"]
                    }
                if post_dict["id"] not in seen:
                    seen.add(post_dict["id"])
                    complete_list.append(post_dict)
                else:
                    logging.info('duplication found, will not be included in array')
        else:
            logging.warning('https request is failing in pull_entire_list')

    return complete_list

def pull_user_list(url2):
    url = url2 + '/latest?format=json&limit=1000'

    user_list = []

    r = requests.get(url, headers=headers)
    if r.ok:
        articles = r.text.replace(remove, '')
        data = json.loads(articles)
        post_json = data["payload"]["references"]["Post"]
        for key in post_json:
            data_dict = {
                    "id": post_json[key]["id"],
                    "article_title": post_json[key]["title"],
                    "article_subtitle": post_json[key]["previewContent"]["subtitle"],
                    "article_slug": post_json[key]["uniqueSlug"]
            }
            user_list.append(data_dict)
    else:
        logging.warning('https request to pull user list is failing')
    return user_list

def get_solo_article(data):
    solo_article = []
    data_dict = {
        "id": data["value"]["id"],
        "article_title": data["value"]["title"],
        "article_subtitle": data["value"]["content"]["subtitle"],
        "article_slug": data["value"]["uniqueSlug"]
    }
    solo_article.append(data_dict)
    return solo_article 

def is_single_article(arti_url):
    rgx = re.search(r'([a-zA-Z0-9]{12})', arti_url[-12:])
    r = requests.get(arti_url, headers=headers)
    if r.ok and rgx:
        data = json.loads(r.text.replace(remove, ''))
    else:
        return False
    try:
        payload = data["payload"]["value"]["id"]
    except KeyError:
        return False
    if payload == rgx.group():
        return (data["payload"])
    
