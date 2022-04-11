import json
import re

import requests


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


def get_id_by_title(title: str):
    response = requests.get(
        'https://api.semanticscholar.org/graph/v1/paper/search', params={
            'query': ' '.join(re.findall(r'\w+', title)),
            'fields': 'title,externalIds',
        }
    )

    response.raise_for_status()

    for paper in json.loads(response.text)['data']:
        externalIds = paper['externalIds']
        if 'ACL' in externalIds:
            return paper['title'], f'ACL:{externalIds["ACL"]}', f'https://aclanthology.org/{externalIds["ACL"]}'
        else:
            return paper['title'], f'DOI:{externalIds["DOI"]}', f'http://dx.doi.org/{externalIds["DOI"]}'
    print(f'{title} is not found')
    return 0
