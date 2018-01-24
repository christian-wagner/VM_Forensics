#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import argparse

from datetime import datetime
from struct import unpack, pack

def main():
  #Definition der Argumente
  parser = argparse.ArgumentParser(
    description=u'Umrechnung der Zeitangaben in der Datei vmsd in ein lesbares Format')
  parser.add_argument('--high',
    help=u'Ganzzahl der Eigenschaft createTimeHigh aus der vmsd-Datei', required=True)
  parser.add_argument('--low',
    help=u'Ganzzahl der Eigenschaft createTimeLow aus der vmsd-Datei', required=True)

  args = vars(parser.parse_args())
  high = args.get('high')
  low = args.get('low')

  combinedTimeMsec = float((long(high) * 2 ** 32) + unpack('I', pack('i', int(low)))[0])
  timestamp = datetime.fromtimestamp(combinedTimeMsec / 1000000)

  print u'Zeitpunkt Erstellung der Momentaufnahme = {0}'.format(
    timestamp.strftime('%d.%m.%Y %H:%M:%S'))

if __name__ == '__main__':
  main()