#!/usr/bin/python3
# -*- coding: utf8 -*-
import re 
from urllib.parse import urlparse, unquote 
import requests
from bs4 import BeautifulSoup

from model import User, Post, Publication, Tag, Image, OutputFormat, to_dict 
from constant import ROOT_URL, HTML_PARSER

from file_handler import IpfsHandler

def parse_user(payload):
    user_dict = payload["payload"]["user"]
    user_id = user_dict["userId"]
    user = User(user_id)
    username = user_dict["username"]
    display_name = user_dict["name"]
    avatar = user_dict["imageId"]
    bio = user_dict["bio"]
    twitter_name = user_dict["twitterScreenName"]
    facebook_id = user_dict["facebookAccountId"]

    user_meta_dict = payload["payload"]["userMeta"]
    ref_dict = payload["payload"]["references"]

    # interest_tags = user_meta_dict["interestTags"]
    # user.interest_tags = parse_tags(interest_tags)
    # author_tags = user_meta_dict["authorTags"]
    # user.author_tags = parse_tags(author_tags)

    publication_ids = ref_dict["Collection"]
    if publication_ids is not None and len(publication_ids.keys()) > 0:
        publication_list = []
        for pub_id in publication_ids.keys():
            publication = parse_publication(payload, pub_id)
            publication_list.append(publication)
        if len(publication_list) > 0:
            user.publications = publication_list

    stats_dict = ref_dict["SocialStats"][user_id]
    following_count = stats_dict["usersFollowedCount"]
    followby_count = stats_dict["usersFollowedByCount"]

    user.user_id = user_id
    user.username = username
    user.display_name = display_name
    user.avatar = avatar
    user.bio = bio
    user.twitter = twitter_name
    user.facebook = facebook_id
    user.following_count = following_count
    user.followedby_count = followby_count

    return to_dict(user)


def parse_publication(payload, pub_id=None):
    if pub_id is None:
        pub_id = payload["payload"]["collection"]["id"]
    publication_dict = payload["payload"]["references"]["Collection"][pub_id]
    publication = Publication(pub_id)
    publication.display_name = publication_dict["name"]
    publication.description = publication_dict["description"]
    publication.creator_user_id = publication_dict["creatorId"]
    image_dict = publication_dict["image"]
    image = parse_images(image_dict)
    if image is not None:
        publication.image = image
    logo_dict = publication_dict["logo"]
    logo = parse_images(logo_dict)
    if logo is not None:
        publication.logo = logo
    publication.follower_count = publication_dict["metadata"]["followerCount"]
    publication.post_count = publication_dict["metadata"]["postCount"]

    if "domain" in publication_dict:
        publication.url = "http://" + publication_dict["domain"]
    else:
        publication.url = ROOT_URL + publication_dict["slug"]
    publication.name = publication_dict["slug"]
    return to_dict(publication)


def parse_post(payload):
    # get the different parsing keys
    post_detail_parsing_keys = ("payload", "references", "Post")
    if post_detail_parsing_keys is None:
        return
    post_list_payload = payload
    for key in post_detail_parsing_keys:
        post_list_payload = post_list_payload.get(key)

    def parse_post_dict(post_dict, post_id=None):
        if post_id is None:
            post_id = post_dict["id"]
        post = Post(post_id)
        unique_slug = post_dict["uniqueSlug"]
        title = post_dict["title"]
        post_date = post_dict["createdAt"]

        publication_id = post_dict["approvedHomeCollectionId"]

        url = ROOT_URL
        ref_dict = payload["payload"]["references"]
        if publication_id is not None and publication_id:
            publication_dict = ref_dict["Collection"][publication_id]
            # custom publication domain
            if "domain" in publication_dict and publication_dict["domain"]:
                url = "https://" + publication_dict["domain"]
            else:
                # simple publication
                url += publication_dict["slug"]
        else:
            # personal post, no publication
            creator_id = post_dict["creatorId"]
            username = ref_dict["User"][creator_id]["username"]
            url += "@{username}".format(username=username)
        url += u"/{path}".format(path=unique_slug)

        virtual_dict = post_dict["virtuals"]
        recommend_count = virtual_dict["recommends"]
        response_count = virtual_dict["responsesCreatedCount"]
        read_time = virtual_dict["readingTime"]
        word_count = virtual_dict["wordCount"]
        image_count = virtual_dict["imageCount"]
        preview_image = virtual_dict["previewImage"]
        # post_tags = virtual_dict["tags"]
        # post.post_tags = parse_tags(post_tags)

        # post.unique_slug = unique_slug
        post.title = title
        post.post_date = post_date
        post.url = url
        post.recommend_count = recommend_count
        post.response_count = response_count
        post.read_time = read_time
        post.word_count = word_count
        post.image_count = image_count
        image = parse_images(preview_image)
        if image is not None:
            post.preview_image = image

        # print("{id}, {title}".format(id=post_id, title=title))
        # print("{recommend}, {response}, {read}".format(
        # recommend=recommend_count, response=response_count, read=read_time))
        return to_dict(post)

    post_list = []
    # print(post_list_payload)
    # payload -> references -> Post
    if type(post_list_payload) is dict:
        for post_id in post_list_payload.keys():
            post_dict = post_list_payload.get(post_id)
            post_list.append(parse_post_dict(post_dict, post_id))
    # payload -> value
    elif type(post_list_payload) is list:
        for post_dict in post_list_payload:
            post_list.append(parse_post_dict(post_dict))

    return post_list


def parse_tags(tags_list_dict):
    if tags_list_dict is not None and len(tags_list_dict) > 0:
        tags_list = []
        for tag_dict in tags_list_dict:
            tag = Tag()
            tag.unique_slug = tag_dict["slug"]
            tag.name = tag_dict["name"]
            tag.post_count = tag_dict["postCount"]
            metadata_dict = tag_dict["metadata"]
            if metadata_dict is not None:
                tag.follower_count = metadata_dict["followerCount"]
            tags_list.append(to_dict(tag))
        return tags_list


def parse_images(image_dict):
    if image_dict is not None:
        image_id = image_dict["imageId"] if "imageId" in image_dict else image_dict["id"]
        if image_id:
            image = Image(image_id)
            image.original_width = image_dict["originalWidth"]
            image.original_height = image_dict["originalHeight"]
            # This isn't working.
            # image.url = u"https://cdn-images-1.medium.com/fit/t/{width}/{height}/{id}" \
            #     .format(width=image.original_width,
            #             height=image.original_height,
            #             id=image.image_id)
            return to_dict(image)
        else:
            return None


def parse_post_detail(post_url, token):
    print(post_url)
    # driver = webdriver.Remote(desired_capabilities=DesiredCapabilities.CHROME)
    # for json format, just return medium json response
    # driver.get(post_url)
    r = requests.get(post_url)
    if r.ok:
        # content_elements = driver.find_element_by_class_name("postArticle-content")
        inner_html = BeautifulSoup(r.text, HTML_PARSER).find("div", {"class": "postArticle-content"})
        content_tags = inner_html.find_all()
        response = ""
        for i in range(0, len(content_tags)):
            tag = content_tags[i]
            md = to_markdown(tag, token)
            if md is not None and md and md is not 'None':
                response += md + "\n"
        print(response)
        return response


def strip_space(text, trim_space=True):
    text = re.sub(r'\s+', ' ', text)
    if trim_space:
        return text.strip()
    else:
        return text


def to_markdown(medium_tag, token):
    text = strip_space(medium_tag.text)
    if medium_tag.name == 'h3':
        return '\n## {}'.format(text)
    elif medium_tag.name == 'h4':
        return '\n### {}'.format(text)

    elif medium_tag.name == 'p':  # text paragraph
        # find style, link inside a paragraph
        plain_text = ''
        for child in medium_tag.children:
            if child.name is None:
                if len(strip_space(child.string)) > 0:
                    plain_text += strip_space(child.string)
            else:
                content = strip_space(child.text)
                if child.name == 'strong':
                    plain_text += " \n**{0}**\n ".format(content)
                elif child.name == 'em':
                    plain_text += " \n_{0}_\n ".format(content)
                elif child.name == 'a':
                    plain_text += " \n[{0}]({1})\n ".format(content, child['href'])
                elif child.name == 'br':
                    plain_text += "{}  \n ".format(content)
                elif child.name == 'code' or child.name == '':
                    plain_text += " \n`{0}`\n ".format(content)
        return plain_text
    elif medium_tag.name == 'figure':  # image and comment
        for child in medium_tag.children:
            img_tag = child.find('img')
            if img_tag is not None and img_tag.has_attr('src'):
                x = IpfsHandler(img_tag['src'], token)
                return '\n![]({})\n'.format(x.ipfs_url)

            # Handle Tweets
            iframe = child.find('iframe')
            if iframe is not None:
                iframe_url = 'https://medium.com' + iframe['src']
                try:
                    r = requests.get(iframe_url)
                    # driver.get(iframe_url)
                    iframe_content = BeautifulSoup(r.text, HTML_PARSER).find('body')
            #        print(iframe_content)
                    if iframe_content.find('iframe'):
                        return None
                    if iframe_content.find('blockquote'):
                        return '\n{}\n'.format(iframe_content.find('blockquote'))
                    if iframe_content is not None:
                        return '\n{}\n'.format(iframe_content)
#                    if 'body' in frame_content):
#                        print(iframe_content.find('body'))
#                        return '\n{}\n'.format(iframe_content.find('body'))
#                    if iframe_content.find('iframe') is not None:
#                        return '\n{}\n'.format(iframe_content.find('iframe'))
                except:
                    return None

    elif medium_tag.name == 'blockquote':  # quote
        return '> {}\n'.format(strip_space(medium_tag.text))
    elif medium_tag.name == 'ol' or medium_tag.name == 'ul':
        return "\n"
    elif medium_tag.name == 'li':
        plain_text = ''
        for child in medium_tag.children:
            if child.name is None:
                if len(strip_space(child.string)) > 0:
                    plain_text += strip_space(child.string)
            else:
                content = strip_space(child.text)
                if child.name == 'strong':
                    plain_text += " **{0}** ".format(content)
                elif child.name == 'em':
                    plain_text += " _{0}_ ".format(content)
                elif child.name == 'a':
                    plain_text += " [{0}]({1}) ".format(content, child['href'])
                elif child.name == 'code' or child.name == '':
                    plain_text += " `{0}` ".format(content)
        return '\n * {0}'.format(plain_text)
    elif medium_tag.name == 'pre':  # code block (not inline code or embed code)
        code_block = ''
        code_tags = medium_tag.prettify().split('<br/>')
        for i in range(len(code_tags)):
            t = BeautifulSoup(code_tags[i], HTML_PARSER)
            code = re.sub(r'\r\n(\s{10})', '', t.text).replace('\n', '')
            code_block += '{}\n'.format(code)
            # print(i, code)
        return '\n```\n{}```\n\n'.format(code_block)
    # elif medium_tag.name == 'hr':
    #     return '\n----\n'

    # TODO: need more test and change to adopt to chrome driver
    elif medium_tag.name == 'iframe':
        # gist, video, github, link...etc.
        iframe_url = ROOT_URL + medium_tag['src']
        try:
            r = requests.get(iframe_url)
            # driver.get(iframe_url)
            iframe_content = BeautifulSoup(r.text, HTML_PARSER).find('iframe')
            if iframe_content is not None:
                iframe_src = iframe_content['src']
                try:
                    uq = unquote(iframe_src)
                    src_string = urlparse(uq)
                    src_string2 = src_string.query
                    rgx = re.search('(?<=src\=)(.*?[^?]*)', src_string2).group()
                    iframe_content['src'] = rgx
                    iframe_content['width'] = '512'
                    iframe_content['height'] = '300'
                    return '\n{}\n'.format(iframe_content)
                except:
                    return None
            else:
                iframe_content = BeautifulSoup(r.text, HTML_PARSER).find('script')
                try:
                    iframe_url = iframe_content['src']
                except:
                    return None
                r = requests.get(iframe_url)
                if r.ok:
                    try:
                        raw_url = r.text.split('href=\\"')[1].split("\\")[0]
                        req = requests.get(raw_url)
                        if req.ok:
                            code_html = BeautifulSoup(req.content, HTML_PARSER)
                            return '\n```\n{}\n```\n\n'.format(code_html.prettify())           
                    except:
                        return None

        except (RuntimeError, requests.exceptions.MissingSchema):
            pass
            # print(e)

    else:
        return None

