#!/usr/bin/env python3

# Author: Psyho
# Blog: http://psyho.gg/
# Twitter: https://twitter.com/fakepsyho

import urllib.request
import xml.etree.ElementTree as ET
import argparse
import copy
import random
import pickle
import os.path
import numpy as np

args = None

def retrieve_individual_results(round_id, handle_id):
    url = 'http://www.topcoder.com/longcontest/stats/?module=IndividualResultsFeed&rd={}&cr={}'.format(round_id, handle_id)
    data = urllib.request.urlopen(url).read().decode('utf-8')
    return ET.fromstring(data)


def parse_individual_results(xml):
    handle = xml.find('handle').text
    scores = [float(e.text) for e in xml.findall('testcases/testcase/score')]
    return handle, scores


def retrieve_match_results(round_id):
    url = 'http://www.topcoder.com/tc?module=BasicData&c=dd_marathon_round_results&rd={}'.format(round_id)
    data = urllib.request.urlopen(url).read().decode('utf-8')
    return ET.fromstring(data)


def parse_match_results(xml):
    coder_ids = [int(e.text) for e in xml.findall('row/coder_id')]
    places = [int(e.text) for e in xml.findall('row/placed')]
    return [id for _, id in sorted(zip(places, coder_ids))]


def custom_scoring(scores):
    rv = copy.deepcopy(scores)
    for i in range(len(scores[0])):
        best = None
        for j in range(len(scores)):
            if scores[j][i] > 0 and (best is None or scores[j][i] < best):
                best = scores[j][i]
        for j in range(len(scores)):
            rv[j][i] = (best / scores[j][i]) ** 2 if scores[j][i] > 0 else 0
    return rv


def simulate(scores, tests_no):
    np_scores = np.transpose(np.array(scores, dtype=float))
    np_sum = np.zeros(len(scores), dtype=float)
    for i in range(tests_no):
        t = random.randint(0, len(scores[0]) - 1)
        np_sum += np_scores[t]

    sum = np_sum.tolist()
    order = [p for _, p in sorted(zip(sum, [i for i in range(len(sum))]), reverse=True)]

    rv = [0] * len(scores)
    for i, p in enumerate(order):
        rv[p] = i
    return rv


def print_table(places, handles, coders_limit, places_limit, digits, style):
    lines = [''] * coders_limit

    max_handle_len = len(max(handles[:coders_limit], key=len))
    cw = 3 + (digits + 1 if digits > 0 else 0)

    positions = ' ' * (max_handle_len + 2)
    for i, h in enumerate(handles[:coders_limit]):
        handle = h if style == 'plain' else '[h]' + h + '[/h]'
        lines[i] += handle + ' ' * (max_handle_len + 2 - len(h))

    for p in range(places_limit):
        positions += ('{:>' + str(cw) + 'd} ').format(p + 1)
        for i in range(coders_limit):
            lines[i] += ('{:>' + str(cw) + '.' + str(digits) + '%} ').format(places[i][p])

    lines = [positions] + lines
    if style == 'tc':
        lines = ['<pre>'] + lines + ['</pre>']

    if not args.silent:
        print('-' * 80)
    for l in lines:
        print(l)
    if not args.silent:
        print('-' * 80)


CURRENT_VERSION = 0.1


def get_file_name(round_id):
    return 'round' + str(round_id) + '.data'


def load_data(round_id):
    fn = get_file_name(round_id)
    if not os.path.isfile(fn):
        if not args.silent:
            print('Unable to find cache file:', fn)
        return {}

    with open(fn, 'rb') as f:
        rv = pickle.load(f)

    if rv['version'] != CURRENT_VERSION:
        if not args.silent:
            print('Cache file was created with a different version:', rv['version'], 'instead of', CURRENT_VERSION)
        return {}

    if not args.silent:
        print('Cache data loaded successfully')

    return rv


def save_data(round_id, data):
    data['version'] = CURRENT_VERSION
    with open(get_file_name(round_id), 'wb') as f:
        pickle.dump(data, f)

    if not args.silent:
        print('Cache data saved successfully')


def main():
    parser = argparse.ArgumentParser(description='Produces placement distribution for specific Marathon Match')
    parser.add_argument('round_id', type=int, help='round ID (usually a 5-digit number)')
    parser.add_argument('-l', '--limit', type=int, default=0, help='number of coders to process')
    parser.add_argument('-s', '--show', type=int, default=0, help='number of coders to show')
    parser.add_argument('-p', '--places', type=int, default=0, help='number of places to show')
    parser.add_argument('-d', '--digits', type=int, default=2, help='number of precision digits to use for printing')
    parser.add_argument('-n', '--simulations', type=int, default=1000, help='number of simulations to perform')
    parser.add_argument('-t', '--tests', type=int, default=0, help='number of tests per simulation')
    parser.add_argument('-f', '--format', choices=['tc', 'plain'], default='tc', help='how to format the output, tc adds [h] tags for forum post')
    parser.add_argument('-c', '--cache', action='store_true', help='adds caching (saves round data to file and tries to reuse it)')
    parser.add_argument('--silent', action='store_true', help='doesn\'t print debug info')

    global args
    args = parser.parse_args()

    if not args.silent:
        print('Round ID:', args.round_id)

    data = load_data(args.round_id) if args.cache else {}

    if 'coder_ids' not in data:
        match_results = retrieve_match_results(args.round_id)
        data['coder_ids'] = parse_match_results(match_results)

    args.limit = args.limit or len(coder_ids)
    args.show = args.show or args.limit
    args.places = args.places or args.show

    assert(args.show <= args.limit)
    assert(args.places <= args.limit)

    if 'handles' not in data:
        data['handles'] = []
        data['scores'] = []

    for id in data['coder_ids'][len(data['handles']):args.limit]:
        individual_results = retrieve_individual_results(args.round_id, id)
        h, s = parse_individual_results(individual_results)
        if not args.silent:
            print('Downloaded scores for', h)
        data['handles'] += [h]
        data['scores'] += [s]

    if args.cache:
        save_data(args.round_id, data)

    args.tests = args.tests or len(data['scores'][0])

    scores = custom_scoring(data['scores'][:args.limit])

    places = [[0] * args.limit for i in range(args.limit)]
    for i in range(args.simulations):
        if i % 10 == 9:
            if not args.silent:
                print('\rPerforming simulations:', i + 1, '/', args.simulations, '       ', end='')
        result = simulate(scores, args.tests)
        for j, v in enumerate(result):
            places[j][v] += 1
    print()

    for i in range(len(places)):
        for j in range(len(places[0])):
            places[i][j] /= args.simulations

    if args.format in ['tc', 'plain']:
        print_table(places, data['handles'][:args.limit], coders_limit=args.show, places_limit=args.places, digits=args.digits, style=args.format)


if __name__ == "__main__":
    main()
