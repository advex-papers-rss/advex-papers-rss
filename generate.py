import json
from datetime import datetime, timezone
from typing import Set, Dict
from urllib.request import urlopen
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring


def add(parent, key, value):
    SubElement(parent, key).text = value


def gen_feed(data, by_number: Set[int] = None, by_day: Dict[int, str] = None):
    """
    Generate RSS Feed from data.

    Args:
        data: json data, a list of papers.
        by_number: number of entries to export.
        by_day: days of entries to export. {day: tag, ...}

    Returns:
        RSS Feed per every stop condition, (feed, name_tag)
    """
    generated_on = datetime.now(timezone.utc)

    # root
    feed = Element('rss', version='2.0')
    channel = SubElement(feed, 'channel')

    # add meta data
    add(channel, 'title', 'Adversarial Example Papers')
    add(channel, 'link', 'https://nicholas.carlini.com/writing/2019/all-adversarial-example-papers.html')
    add(channel, 'description', 'Adversarial example papers collected by Nicholas Carlini.')
    add(channel, 'language', 'en-us')
    add(channel, 'lastBuildDate', generated_on.isoformat(timespec='seconds'))
    add(channel, 'generator', 'advex-papers-rss')
    add(SubElement(channel, 'author'), 'name', 'Nicholas Carlini')

    # add papers
    for i, (date, link, title, author_list, abstract) in enumerate(data, start=1):
        item = SubElement(channel, 'item')
        add(item, 'title', title)
        add(item, 'link', link)
        add(item, 'description', abstract.replace('\n', ' '))
        add(item, 'author', ','.join(author_list))
        date = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        add(item, 'pubDate', date.isoformat(timespec='seconds'))

        # stop by number
        if by_number and i in by_number:
            yield feed, f'top{i:d}'

        # stop by day
        if by_day:
            nb_days = (generated_on - date).days
            for day in by_day.keys():
                if nb_days >= day:
                    yield feed, by_day.pop(day)
                    break

    yield feed, 'all'


def dump(feed, filename):
    feed_string = tostring(feed, encoding='utf-8')
    feed_string = minidom.parseString(feed_string).toprettyxml(indent='  ')
    with open(filename, 'w') as f:
        f.write(feed_string)


if __name__ == '__main__':
    # settings
    URL = 'https://nicholas.carlini.com/writing/2019/advex_papers.json'
    BY_NUMBER = {25, 50, 100, 200, 300}
    BY_DAYS = {7: 'weekly', 31: 'monthly', 91: 'quarterly', 366: 'yearly'}

    # generate
    data = json.loads(urlopen(URL).read().decode('utf-8'))
    for feed, tag in gen_feed(data, BY_NUMBER, BY_DAYS):
        dump(feed, f'advex_papers_{tag}.xml')
