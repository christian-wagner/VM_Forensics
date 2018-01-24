#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import argparse
import time
import datetime
import guestfs
from threading import Thread
import os
import yara

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

LOCAL_MOUNT = '/tmp/libguestfs-local-mount/'
g = guestfs.GuestFS(python_return_dict=True)

def threaded_function():
  g.mount_local_run()

def main():
  #Definition der Argumente
  parser = argparse.ArgumentParser(
    description=u'Analyse des Inhalts einer virtuellen Festplatte mittels YARA-Regeln')
  parser.add_argument('--image', help=u'Dateipfad des Festplattenabbildes', required=True)
  parser.add_argument('--yaraRules', help=u'Dateipfad der Datei mit den YARA-Regeln',
    required=True)

  args = vars(parser.parse_args())

  image = args.get('image')
  rulesFileName = args.get('yaraRules')

  #Messen der benötigten Zeit
  startTime = time.time()

  g.add_drive_ro(image)
  g.launch()

  #Erstellen des temporären Mount-Verzeichnisses falls dieses nicht existiert
  if not os.path.exists(LOCAL_MOUNT):
    os.makedirs(LOCAL_MOUNT)

  #Laden der YARA-Regeln aus der Datei
  rules = yara.compile(rulesFileName)

  for partition, fileSystem in g.list_filesystems().iteritems():
    #unbekannte (zB extended-Partitionen oder unbekannte Dateisysteme) und
    #swap-Partitionen werden ignoriert
    if fileSystem != 'swap' and fileSystem != 'unknown':
      g.mount_ro(partition, '/')
      g.mount_local(LOCAL_MOUNT)
      thread = Thread(target=threaded_function)
      thread.start()

      filePaths = g.find('/')

      for filePath in filePaths:
        if g.is_file('/' + filePath) and g.filesize('/' + filePath) > 0:
          matches = rules.match(LOCAL_MOUNT + filePath)

          if len(matches) > 0:  #wenn eine YARA-Regel zuschlägt
            match = matches['main']
            print '{0} gefunden: {1} - {2}'.format(match[0]['rule'], partition, filePath)

      g.umount_local()
      g.umount(partition, force=True)

  endTime = time.time()

  print ''
  print u'Skript ausgeführt in {0}'.format(
    datetime.timedelta(seconds=round(endTime - startTime, 0)))

if __name__ == '__main__':
  main()