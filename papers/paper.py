import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from lxml import etree

from papers.scholar import get_citation_by_id, get_citation_by_title

MIT = re.compile(r'(http|https)://direct\.mit\.edu/tacl/article/doi/(?P<id>[.\d]+/\w+)')
ACL1 = re.compile(r'(http|https)://aclweb.org/anthology/(?P<id>[-.\w]+)')
ACL2 = re.compile(r'(http|https)://aclanthology.org/(?P<id>[-.\w]+)')
ACL3 = re.compile(r'(http|https)://www.aclweb.org/anthology/(?P<id>[-.\w]+)(.pdf)')
ACL4 = re.compile(r'(http|https)://www.aclweb.org/anthology/(?P<id>[-.\w]+)')


def process_author(name: str):
    name, affiliation = name.strip()[:-1].split(' (', maxsplit=1)
    return name, list(set(affiliation.split('; ')))


def fetch_papers(year: int):
    response = requests.get(f'https://murawaki.org/misc/japan-nlp-{year}.html')
    html = str(response.content, encoding='utf-8')

    ignores = set(etree.HTML(html).xpath('/html/body/div/div[4]/table/tbody/tr/td/span/text()'))

    html = html.replace(r'<span style="color: grey;">', '')
    html = html.replace(r'</span>', '')

    elements = etree.HTML(html)

    data = []
    for item in elements.xpath('/html/body/div/div[4]/table/tbody/tr'):
        category, *authors = item.xpath('td/text()')
        title, = item.xpath('td/a/text()')
        url, = item.xpath('td/a/@href')

        data.append((category, [process_author(author) for author in authors], title, url))

    return data, ignores


def fetch_id(data):
    for category, authors, title, url in data:
        match = re.match(pattern=MIT, string=url)
        if match is not None:
            yield category, authors, title, f"DOI:{match.group('id')}", url
        else:
            for pattern in [MIT, ACL1, ACL2, ACL3, ACL4]:
                match = re.match(pattern=pattern, string=url)
                if match is not None:
                    break

            if match is not None:
                yield category, authors, title, f"ACL:{match.group('id')}", url
            else:
                print(f'{title} - {url} is ignored')


def fetch_citation(year):
    data, ignores = fetch_papers(year)
    data = fetch_id(data)

    avg = Counter()
    first = Counter()

    papers = []
    for index, (category, authors, title, id, url) in enumerate(data):
        try:
            title, citation = get_citation_by_id(id)
        except Exception:
            title, citation = get_citation_by_title(title)

        print(f'#{index}: {title} -> {url}')
        papers.append((
            citation, category,
            (f'{name} ({"; ".join(affiliations)})' for name, affiliations in authors),
            title, url,
        ))

        num_authors = len(authors)

        for index, (name, afflictions) in enumerate(authors):
            if index == 0:
                num_afflictions = len(afflictions)
                for affliction in afflictions:
                    avg[affliction] += citation / num_afflictions / (2 if num_authors > 1 else 1)
                    first[affliction] += citation / num_afflictions
            else:
                num_afflictions = len(afflictions)
                for affliction in afflictions:
                    avg[affliction] += citation / num_afflictions / 2 / (num_authors - 1)

    papers = sorted(papers, key=lambda item: item[0], reverse=True)
    affiliations = [
        (name, round(citation * 1.0, ndigits=1), round(first[name] * 1.0, ndigits=1))
        for name, citation in avg.most_common()
        if name not in ignores
    ]
    return papers, affiliations


def render_html(year: int, folder: str = 'docs', directory: Path = Path(__file__).parent):
    env = Environment(
        loader=FileSystemLoader(str((directory / 'templates').resolve())),
        autoescape=select_autoescape()
    )
    template = env.get_template('page.html')

    if not (directory.parent / folder).exists():
        (directory.parent / folder).mkdir(parents=True, exist_ok=True)
    with open(str((directory.parent / folder / f'{year}.html').resolve()), 'w') as fp:
        papers, affiliations = fetch_citation(year)

        print(template.render(
            year=year, papers=papers, affiliations=affiliations,
            utcnow=datetime.now(tz=timezone(timedelta(hours=9))),
        ), file=fp)
