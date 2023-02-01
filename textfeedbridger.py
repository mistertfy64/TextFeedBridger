import html
import json
import requests
from bs4 import BeautifulSoup
import re
import datetime
import time

building = False
feed = ""
configuration = json.load(open("configuration.json"))
request = requests.get(configuration["url"])
request_text = request.text
soup = BeautifulSoup(request_text, features="html.parser")
post_previews = soup.find_all(
    class_=configuration["names"]["post_preview_class"])

# TODO: Why use global keyword?


def start_feed(feed):
    global building
    building = True
    feed += """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
    <channel>
    <title>mistertfy64's blog</title>
    <link>https://blog.mistertfy64.com/</link>
    <description>mistertfy64's blog</description>
    <language>en-US</language>
    <category>Personal blogs</category>
    <copyright>Copyright 2022-2023 mistertfy64</copyright>"""
    return feed


def build_feed(post_preview, feed):
    global building
    if building:
        feed += "<item>\n"
        feed += f"<title>{post_preview['title']}</title>\n"
        feed += f"<link>{post_preview['url']}</link>\n"
        feed += f"<guid>{post_preview['url']}</guid>\n"
        feed += f"<pubDate>{(datetime.datetime.fromisoformat(post_preview['date_created'].replace('Z',''))).strftime('%a, %d %b %Y %H:%M:%S')} GMT</pubDate>\n"
        if post_preview['date_modified']:
            feed += f"<lastBuildDate>{(datetime.datetime.fromisoformat(post_preview['date_modified'].replace('Z',''))).strftime('%a, %d %b %Y %H:%M:%S')} GMT</lastBuildDate>\n"
        # TODO: Remaining: tags
        feed += f"<description>{post_preview['content']}</description>"
        feed += "</item>\n"
    else:
        print("Not building as building hasn't started/already ended.")
    return feed


def end_feed(feed):
    global building
    feed += """</channel>
  </rss>"""
    building = False
    return feed


def get_post_details(post_preview, recursive=True):
    names = configuration["names"]
    descendants = post_preview
    url = f"{configuration['url']}/{descendants.find('a',class_=names['post_preview_id_class'])['href']}"
    title = f"{descendants.find(class_=names['post_preview_title_class']).string}".strip(
    )
    date = re.findall(r"{}".format(configuration["date_publish_regex"]),
                      descendants.find(class_=names['post_preview_date_class']).string, re.DOTALL)
    date_created = date[0]
    date_modified = date[1] if len(date) > 1 else None
    content = descendants.find(
        class_=names['post_preview_content_class'], recursive=True).contents
    post_elements = ""
    for element in content:
        post_elements += html.escape(str(element))
    tags = f"{descendants.find(class_=names['post_preview_tags_class']).string}".strip(
    )
    return {"url": url, "title": title, "date_created": date_created, "date_modified": date_modified, "content": post_elements}


start = time.perf_counter()
feed = start_feed(feed)
for post_preview in post_previews:
    feed = build_feed(get_post_details(post_preview), feed)
feed = end_feed(feed)

file = open("feed.txt", "w")
file.write(feed)
end = time.perf_counter()
print(f"Took {1000*(end-start)}ms.")
