#!/usr/bin/env python3

# Author: Psyho
# Blog: http://psyho.gg/
# Twitter: https://twitter.com/fakepsyho

import urllib.request
import xml.etree.ElementTree as ET
import argparse
import random
import pickle
import os.path
import numpy as np


# TODO: [bug] sometimes crashes during downloading data
# TODO: [option] add scale for showranking


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
    placed = [int(e.text) for e in xml.findall('row/placed')]
    num_submissions = [int(e.text) for e in xml.findall('row/num_submissions')]
    return [id for _, id, subs in sorted(zip(placed, coder_ids, num_submissions)) if subs > 0]


def scoring_raw(scores):
    return [max(v, 0) for v in scores]


def scoring_relative_max(scores):
    best = max([v for v in scores if v > 0] + [0]) or 1
    return [v / best if v > 0 else 0 for v in scores]


def scoring_relative_min(scores):
    best = min([v for v in scores if v > 0] + [1e100])
    return [best / v if v > 0 else 0 for v in scores]


def scoring_rank_max(scores):
    rv = []
    for i, vi in enumerate(scores):
        tot = 0
        for j, vj in enumerate(scores):
            if i == j:
                continue
            if vi > vj:
                tot += 1
            if vi == vj:
                tot += 0.5
        rv += [tot / (len(scores) - 1)]
    return rv


def scoring_rank_min(scores):
    scores = [v if v > 0 else 1e100 for v in scores]
    rv = []
    for i, vi in enumerate(scores):
        tot = 0
        for j, vj in enumerate(scores):
            if i == j:
                continue
            if vi < vj:
                tot += 1
            if vi == vj:
                tot += 0.5
        rv += [tot / (len(scores) - 1)]
    return rv


def scoring_custom(scores):
    best = min([v for v in scores if v > 0]) or None
    return [(best / v) ** 2 if v > 0 else 0 for v in scores]


def process_scores(scores, scoring):
    scoring_functions = {
        'relmax': scoring_relative_max,
        'relmin': scoring_relative_min,
        'raw': scoring_raw,
        'rankmax': scoring_rank_max,
        'rankmin': scoring_rank_min,
        'custom': scoring_custom,
    }

    scoring_function = scoring_functions[scoring]

    rv = []
    for i in range(len(scores[0])):
        test_case = [scores[j][i] for j in range(len(scores))]
        rv += [scoring_function(test_case)]
    return rv


def simulate(scores, tests_no):
    np_scores = np.array(scores, dtype=float)
    np_sum = np.zeros(len(scores[0]), dtype=float)
    for i in range(tests_no):
        t = random.randint(0, len(scores) - 1)
        np_sum += np_scores[t]

    order = reversed(np.argsort(np_sum).tolist())

    rv = [0] * len(scores[0])
    for i, p in enumerate(order):
        rv[p] = i

    return rv


def print_table(data, formatting=None, style='plain'):
    # make data full 2d str array
    data = [list(map(str, l)) for l in data]
    max_columns = max(map(len, data))
    data = [l + [''] * (max_columns - len(l)) for l in data]

    col_width = [max([len(data[j][i]) for j in range(len(data))]) for i in range(len(data[0]))]

    if formatting is None:
        formatting = [''] * max_columns

    lines = []
    for l in data:
        line = ''
        for i, s in enumerate(l):
            alignment = ''
            pre = ''
            post = ''
            if '>' in formatting[i]:
                alignment += '>'
            if '<' in formatting[i]:
                alignment += '<'
            if 'h' in formatting[i] and style == 'tc':
                pre += '[h]'
                post += '[/h]'
            line += ('{:' + alignment + str(col_width[i] + len(pre) + len(post)) + '} ').format(pre + s + post)
        lines += [line]

    if style == 'tc':
        lines = ['<pre>'] + lines + ['</pre>']

    if not args.silent:
        print('-' * 80)
    for l in lines:
        print(l)
    if not args.silent:
        print('-' * 80)


def print_place_distribution(places, handles, coders_limit, places_limit, digits, style):
    data = [[''] + [str(i) for i in range(1, 1+places_limit)]]
    for i, h in enumerate(handles[:coders_limit]):
        line = [h] + [('{:.' + str(digits) + '%}').format(places[i][p]) for p in range(places_limit)]
        data += [line]

    print_table(data, ['h<'] + ['>'] * places_limit, style)


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
    parser.add_argument('--scoring', choices=['relmax', 'relmin', 'raw', 'rankmax', 'rankmin', 'custom'], default='raw', help='selects scoring method for scores pre-processing')
    parser.add_argument('--silent', action='store_true', help='doesn\'t print debug info')
    parser.add_argument('--showranking', action='store_true', help='instead of performing simulations, just shows the final ranking')

    global args
    args = parser.parse_args()

    if not args.silent:
        print('Round ID:', args.round_id)

    data = load_data(args.round_id) if args.cache else {}

    if 'coder_ids' not in data:
        match_results = retrieve_match_results(args.round_id)
        data['coder_ids'] = parse_match_results(match_results)

    if len(data['coder_ids']) == 0:
        print('[ERROR] Unable to find any data for this round')
        return

    args.limit = args.limit or len(data['coder_ids'])
    args.show = args.show or args.limit
    args.places = args.places or args.show

    assert(args.show <= args.limit)
    assert(args.places <= args.limit)

    if 'handles' not in data:
        data['handles'] = []
        data['scores'] = []

    for coder_id in data['coder_ids'][len(data['handles']):args.limit]:
        individual_results = retrieve_individual_results(args.round_id, coder_id)
        h, s = parse_individual_results(individual_results)
        if not args.silent:
            print('Downloaded scores for', h)
        data['handles'] += [h]
        data['scores'] += [s]

    if args.cache:
        save_data(args.round_id, data)

    args.tests = args.tests or len(data['scores'][0])

    scores = process_scores(data['scores'][:args.limit], args.scoring)

    if args.showranking:
        scores_sum = np.sum(np.array(scores), axis=0)
        table_data = []
        for pos, idx in enumerate(reversed(np.argsort(np.array(scores_sum)).tolist())):
            table_data += [[pos + 1, data['handles'][idx], ('{:.' + str(args.digits) + 'f}').format(scores_sum[idx])]]
        print_table(table_data, ['>', 'h>', '>'], args.format)
        return

    places = [[0] * args.limit for _ in range(args.limit)]
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

    print_place_distribution(places, data['handles'][:args.limit], coders_limit=args.show, places_limit=args.places, digits=args.digits, style=args.format)


if __name__ == "__main__":
    main()
