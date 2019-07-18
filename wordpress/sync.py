#TODO->Line 54 and 55: Gateway and jwt token
#TODO->Line 33: jwt token

import logging
import requests
import json
from configparser import ConfigParser
import re
from file_handler import IpfsHandler


class syncToKauri():

    global status

    def __init__(s,article, token):
        s.article = article
        s.token = token
        s.loadArticle = s.loadArticle()
        # s.ipfs_upload = s.ipfs_upload()
        s.importer = s.importer()

    def loadArticle(s):
        global wp_json_object
        #converts to object form
        wp_string = s.__str__(s.article)
        wp_json_object = json.loads(wp_string)

    #takes all images and uploads them to kauri ipfs
    def ipfs_upload(s):
        token = s.token
        # searches for images
        pattern = re.compile(r'\!\[\]\([a-z:,/.\-_?=&%0-9A-Z]*\)')
        src = pattern.findall(wp_json_object['content'])
        #removes tags and creates a string of just the link
        for r in range(len(src)):
            # gets rid of brackets to find the link
            print('within for statement' + r)
            src[r]=src[r].replace('![]', '')
            src[r]=src[r].replace('(', '')
            src[r]=src[r].replace(')','')
            #sends it to the ipfs handler to upload
            ipfs = IpfsHandler(src[r],token)
            ipfs_link = ipfs.ipfs_url
            #replaces the link with the new ipfs link
            wp_json_object['content']= wp_json_object['content'].replace(src[r],ipfs_link)

    def importer(s):
        global status
        # grabs token, gateway, and header
        token = s.token
        gateway = 'https://api.kauri.io/graphql'
        headers = {"Content-Type": "application/json"}
        headers['X-Auth-Token'] = 'Bearer %s' % token
        md_output= []
        #creates the article to send
        newArticle = {
            "query" : "mutation submitNewArticle($title: String, $description: String, $content: String, $attributes: Map_String_StringScalar) { submitNewArticle (title: $title, description: $description, content: $content, attributes: $attributes) {hash} }",
            "variables" : {
                "title": wp_json_object['title'],
                "content" : json.dumps({'markdown': wp_json_object['content']}, separators=(',', ':')),
                "attributes" : {
                    "origin_name" : "wordpress",
                    "origin_url" : wp_json_object['link'],
                },

            },
            "operationName" : "submitNewArticle"
            }
        #sends the article
        p = requests.post(gateway, headers = headers, data = json.dumps(newArticle))

        #basic logging of successes and failures

        if p.ok:
            # if it was successful, logs the success and saves status as true
            logging.basicConfig(filename = 'sync.log', filemode = 'a', format='%(name)s -%(process)d - %(asctime)s - %(levelname)s - %(message)s', level = logging.INFO)
            logging.info( "title of article: " + wp_json_object['title'] + "Success : True")
            status = True

        else:
            #if it was not successful -> also prints an error message to the console
            logging.basicConfig(filename = 'sync.log', filemode = 'a', format='%(name)s -%(process)d - %(asctime)s - %(levelname)s - %(message)s',level = logging.ERROR)
            logging.error( "title of article: " + wp_json_object['title'] + "Success : False")
            print ("Error, article: " + wp_json_object['title'] + " could not be synced to Kauri.")
            status = False


    # makes sure the string is in the proper format
    def __str__(s,string):
        string = json.dumps(string)
        return string

    # makes sure the string is in the proper format
    def __repr__(s,string):
        string = json.dumps(string)
        return string
