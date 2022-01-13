#!/usr/bin/env python3

import sys
import datetime

sys.stdout.write('Content-type: text/event-stream \r\n\r\n')
now = datetime.datetime.now()
sys.stdout.write('data: %s \r\n' % now)
sys.stdout.write('retry: 1000\r\n\r\n')
sys.stdout.flush()