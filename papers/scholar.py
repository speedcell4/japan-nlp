import json
import re

import requests

__all__ = [
    'get_citation_by_id',
    'get_citation_by_title',
]


def get_citation_by_id(id: str):
    response = requests.get(
        f'https://api.semanticscholar.org/graph/v1/paper/{id}', params={
            'fields': 'title,citationCount',
        }
    )

    response.raise_for_status()

    paper = json.loads(response.text)
    return paper['title'], paper['citationCount']


def get_citation_by_title(title: str):
    response = requests.get(
        'https://api.semanticscholar.org/graph/v1/paper/search', params={
            'query': ' '.join(re.findall(r'\w+', title)),
            'fields': 'title,citationCount',
        }
    )

    response.raise_for_status()

    for paper in json.loads(response.text)['data']:
        return paper['title'], paper['citationCount']
    print(f'{title} is not found')
    return 0
