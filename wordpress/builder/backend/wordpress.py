import pprint
import tomd
import json
import re
from bs4 import BeautifulSoup
from file_handler import IpfsHandler
from markdownify import markdownify as md


class WpConverter():

    def __init__(s,file):
        s.file = file
        s.create_file = s.createFile()
        s.find_contents = s.findContents()
        s.empty_contents = s.emptyContents()
        s.format_contents = s.format()
        s.htmlParse_contents = s.htmlParse()
        s.to_markdown = s.toMarkdown()

    # open file and create soup object
    def createFile(s):
        global soup
        global my_list
        my_list = []

        content = s.file
        soup = BeautifulSoup(content,features = "xml")

    def htmlParse(s):
        for q in range(len(my_list)):
            #fixes common tag errors from html
            my_list[q]['content'] = my_list[q]['content'].replace('<em> ','<em>')
            # there are two of the following because for some reason it gltiches
            my_list[q]['content'] = my_list[q]['content'].replace(' </em>','</em>')
            my_list[q]['content'] = my_list[q]['content'].replace(' </em>', '</em>')
            my_list[q]['content'] = my_list[q]['content'].replace('<strong >','<strong>')
            my_list[q]['content'] = my_list[q]['content'].replace('<strong> ','<strong>')
            my_list[q]['content'] = my_list[q]['content'].replace(' </strong>','</strong>')

    #delete any blank articles from list
    def emptyContents(s):
        count = 0
        while(count!= len(my_list)):
            #searches to make sure there's no new line empty articles
            pattern = re.compile(r'[^\n]')
            find = pattern.search(my_list[count]['content'])
            # it finds a new line empty article
            if (find == None):
                del my_list[count]
            #deletes other empty article cases
            if(my_list[count]['content'] == ' '):
                del my_list[count]
            elif(my_list[count]['content'] == ''):
                del my_list[count]
            else:
                count += 1

    #find content in xml file
    def findContents(s):

        """
        -finds the first element of each
        -we don't need (use) the first element since
        it is associated with web details
        """

        temp_title = soup.find('title')
        title = temp_title
        temp_link = soup.find('link')
        link = temp_link
        temp_content = soup.find('content:encoded')
        content = temp_content

        #number of articles/content found
        num_of_articles = len(soup.find_all('title'))

        """
        -finds the next item in the xml file and
        appends the list
        -content is found after append because
        it appears less times than the rest and this method
        prevents errors
        """

        x = 1
        for x in range(num_of_articles - 1):
            title = title.findNext('title')
            link = link.findNext('link')
            my_list.append({'title': title.get_text(), 'link': link.get_text(),'content': content.get_text()})
            content = content.findNext('content:encoded')

    # corrects format of lists and images before converting to markdown
    def format(s):
        for y in range(len(my_list)):
            #searches for the captions and singles them out
            pattern = re.compile(r'<figcaption>[a-z:,/.\-_? =&%0-9A-Z]*<\/figcaption>')
            caption = pattern.findall(my_list[y]['content'])

            #corrects caption and image tags
            for t in range(len(caption)):
                my_list[y]['content'] = my_list[y]['content'].replace(caption[t], '')
                caption[t] = caption[t].replace('<figcaption>', '')
                caption[t] = caption[t].replace('</figcaption>', '')
                #adds the caption to the end of the image
                my_list[y]['content'] = my_list[y]['content'].replace('/></figure>','></img>' + caption[t] + '</p>')

            #replaces image end tag and list tags
            my_list[y]['content'] = my_list[y]['content'].replace('/></figure>','></img></p>')
            my_list[y]['content'] = my_list[y]['content'].replace('<img','<p><img')
            my_list[y]['content'] = my_list[y]['content'].replace('</li>','</li>\n')

    # converts to markdown
    def toMarkdown(s):

        for z in range(len(my_list)):
            #searches for articles written with the wp editor
            # or written in html within wp
            pattern = re.compile(r'<!-- wp:paragraph -->')
            search = pattern.search(my_list[z]['content'])

            if (search != None):
                #articles written in wp editor are converted
                my_list[z]['content']= tomd.convert(my_list[z]['content'])
            else:
                #tags are changed for html new line and list elements
                my_list[z]['content'] = my_list[z]['content'].replace('\n','<br>')
                my_list[z]['content'] = my_list[z]['content'].replace('<li>','<br><li>')
                my_list[z]['content'] = my_list[z]['content'].replace('</li>','</li><br>')
                # a different converter is used that is better for html
                # that was written within the wp editor
                my_list[z]['content'] = md(my_list[z]['content'])
        # double checks that empty articles are removed from list
        s.emptyContents()
        #sends for the ipfs image search


    #converts to proper string format
    def __str__(s):
        string = json.dumps(my_list)
        return string

    #converts to proper string format
    def __repr__(s):
        string = json.dumps(my_list)
        return string
