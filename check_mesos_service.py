#!/usr/bin/env python

import sys
import traceback
from argparse import ArgumentParser
from collections import namedtuple
from urlparse import urljoin

import requests

discotimeout = 4 # In seconds.
tokenkey = 'server-token'
resplim = 128 # Response output character limit.

class Main(object):
  Problem = namedtuple('Problem', ('code', 'message'))

  # Parse arguments.
  def __init__(self):
    parser = ArgumentParser(description='Check Mesos service for health.')
    parser.add_argument('-d', '--discovery', required=True,
      help='discovery server URL')
    parser.add_argument('-s', '--service', required=True,
      help='service name to check')
    parser.add_argument('-e', '--endpoint', default='health',
      help='endpoint to check; default %(default)r')
    parser.add_argument('-t', '--timeout', type=float, default=5,
      help='endpoint check timeout in seconds; default %(default)s')
    parser.add_argument('-c', '--critical', type=int, default=1,
      help='minimum instances before critical; default %(default)s; '
      'set to 0 to disable')
    parser.add_argument('-w', '--warn', type=int, default=1,
      help='minimum instances before warning; default %(default)s; '
      'set to 0 to disable')
    args = parser.parse_args()

    # Parser error terminates process with code 2 ("CRITICAL").
    if args.timeout <= 0:
      parser.error('timeout must be positive')
    if args.critical < 0:
      parser.error('critical must be non-negative')
    if args.warn < 0:
      parser.error('warn must be non-negative')
    if args.warn < args.critical:
      parser.error('warn must be at least as large as critical')

    self.args = args

  def get_announcements(self):
    url = urljoin(self.args.discovery, 'state')
    state = requests.get(url, timeout=discotimeout).json()
    return [a for a in state if a['serviceType'] == self.args.service]

  @staticmethod
  def count_announcements(announcements):
    seen = set()
    count = 0
    for ann in announcements:
      metadata = ann.get('metadata', {})
      if tokenkey not in metadata:
        # No token; this is ok.
        count += 1
        continue
      token = metadata[tokenkey]
      if token not in seen:
        seen.add(token)
        count += 1
    return count

  @classmethod
  def make_problem(cls, code, topic, message):
    state = {2: 'critical', 1: 'warning'}[code]
    return cls.Problem(code, '%s %s: %s' % (topic, state, message))

  def make_announcement_problem(self, code, count):
    msg = '%s (crit./warn thresh. %s/%s)' % (
      count, self.args.critical, self.args.warn)
    return self.make_problem(code, 'announcements', msg)

  @classmethod
  def make_response_problem(cls, code, status_code, text):
    if len(text) > resplim: text = text[:resplim] + '...'
    msg = '%s from endpoint\n%s' % (status_code, text)
    return cls.make_problem(code, 'health', msg)

  def make_timeout_problem(self, type):
    return self.make_problem(2, '%s timeout' % type,
      'thresh. %.2f' % self.args.timeout)

  # Return Problem or None if ok.
  def check_endpoint(self, announcement):
    url = urljoin(announcement['serviceUri'], self.args.endpoint)
    try:
      resp = requests.get(url, timeout=self.args.timeout)
      code = resp.status_code // 100
      if code == 5:
        return self.make_response_problem(2, resp.status_code, resp.text)
      if code == 4:
        return self.make_response_problem(1, resp.status_code, resp.text)
    except requests.exceptions.ConnectTimeout:
      return self.make_timeout_problem('connect')
    except requests.exceptions.ReadTimeout:
      return self.make_timeout_problem('read')
    except requests.exceptions.RequestException:
      return self.make_problem(2, 'health',
        'unhandled exception\n' + traceback.format_exc())

  def run(self):
    try:
      announcements = self.get_announcements()
    except Exception:
      print 'failed to get announcements'
      print traceback.format_exc()
      return 3

    # Will contain Problem instances.
    bad = []

    count = self.count_announcements(announcements)
    if count < self.args.critical:
      bad.append(self.make_announcement_problem(2, count))
    elif count < self.args.warn:
      bad.append(self.make_announcement_problem(1, count))

    for ann in announcements:
      problem = self.check_endpoint(ann)
      if problem is not None: bad.append(problem)

    bad.sort(reverse=True) # Worst problems first.
    for problem in bad: print problem.message

    # Return with worst code if there are any, else 0 for success.
    return bad[0].code if bad else 0

sys.exit(Main().run())
