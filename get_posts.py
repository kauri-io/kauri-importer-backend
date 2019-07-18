import requests
import json

headers = {
    'Accept': 'application/json'
}

posts = []

def get_posts_by_year(year, url):
    year_url = url+'/'+year
    for x in range(1,13):
        num = x if x < 10 else '0' + str(x)
        r = requests.get(year_url+'/'+str(x), headers=headers)
        if r.ok:
            raw = r.text
            raw_json = json.loads(r.text.replace('])}while(1);</x>', ''))
            posts_raw = raw_json['payload']['references']['Post']
            for k,v in posts_raw.items():
                post = posts_raw[k]['title']
                posts.append(post)


url = input('Enter your medium account URL: ') + '/archive'
r = requests.get(url, headers=headers)

if r.ok:
    raw = r.text
    raw_json = json.loads(r.text.replace('])}while(1);</x>', ''))
    years = raw_json['payload']['archiveIndex']['yearlyBuckets']
    for year in years:
        if year['hasStories']:
            get_posts_by_year(year['year'], url)

print(posts)
