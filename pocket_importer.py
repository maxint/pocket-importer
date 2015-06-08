# coding: utf-8

import re
import pocket


ITEM_RE = re.compile(r'<a href="([^"]+)" time_added="(\d+)" tags="([^"]*)">', re.IGNORECASE | re.MULTILINE)


def parse_list(content):
    results = list()
    for url, time_added, tags in ITEM_RE.findall(content):
        results.append(dict(url=url, time=time_added, tags=tags))
    return results


def batch_do(p, actions, action):
    """:type p: pocket.Pocket"""
    print 'Batch %s (num=%d) ...' % (action, len(actions))
    for d in actions:
        d['action'] = action
    r = p.send(actions).json()
    assert r['status'] == 1, 'Batch operation ({}) failed'.format(action)
    return r


def main_do(fp):
    """:type fp: file"""
    c = fp.read()
    m = re.findall(r'<ul>([\s\S\r\n]+?)</ul>', c, re.IGNORECASE | re.MULTILINE)
    assert len(m) >= 1

    p = pocket.create_pocket_from_cache()

    batch_do(p, parse_list(m[0]), action='add')
    if len(m) > 1:
        r = batch_do(p, parse_list(m[1]), action='add')
        actions = [dict(item_id=d['item_id'], time=d.get('time_added')) for d in r['action_results']]
        batch_do(p, actions, action='archive')

    print 'Done!'


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import official exported list from getpocket.com')
    parser.add_argument('file', type=argparse.FileType('r'),
                        help='Target HTML file to be imported')
    args = parser.parse_args()
    main_do(args.file)


if __name__ == '__main__':
    main()
