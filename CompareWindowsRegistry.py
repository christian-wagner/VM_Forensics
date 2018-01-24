#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import argparse
import time
import os
import shutil
import datetime
import codecs
import csv

from Registry import Registry

TEMP_DIRECTORY_A = '/tmp/libguestfs-tmp/A/'
TEMP_DIRECTORY_B = '/tmp/libguestfs-tmp/B/'

files = set()

def main():
  #Definition der Argumente
  parser = argparse.ArgumentParser(
    description='Vergleich der Windows-Registrierungsdatenbank')
  parser.add_argument('--imageA', help='Dateipfad des ersten Festplattenabbildes',
    required=False)
  parser.add_argument('--imageB', help='Dateipfad des zweiten Festplattenabbildes',
    required=False)
  parser.add_argument('--outputDir',
    help='Dateipfad, in dem die Resultate der Vergleiche der einzelnen Dateien im '
         'CSV-Format abgelegt werden', required=True)
  parser.add_argument('--dirA', help='Verzeichnis, aus dem die Dateien gelesen werden',
    required=False)
  parser.add_argument('--dirB', help='Verzeichnis, aus dem die Dateien gelesen werden',
    required=False)
  args = vars(parser.parse_args())

  if not args.get('imageA') and not args.get('dirA'):
    parser.error(
      u'Entweder --imageA bzw. --imageB oder --dirA bzw. --dirB müssen als Parameter '
      u'angegeben werden.')

  if args.get('imageA') and not args.get('imageB'):
    parser.error(u'Es müssen beide Pfade zu den virtuellen Festplatten angegeben werden.')

  if args.get('dirA') and not args.get('dirB'):
    parser.error(u'Es müssen beide Pfade zu den Verzeichnissen angegeben werden.')

  imageA = args.get('imageA')
  imageB = args.get('imageB')
  outputDir = os.path.join(args.get('outputDir'), '', '')
  dirA = args.get('dirA')
  dirB = args.get('dirB')

  #Messen der benötigten Zeit
  startTime = time.time()

  if not dirA:
    dirA = TEMP_DIRECTORY_A
    dirB = TEMP_DIRECTORY_B
    g = guestfs.GuestFS(python_return_dict=True)
    extractFiles(g, imageA, dirA)
    extractFiles(g, imageB, dirB)
    g.close()
  else:
    dirA = os.path.join(dirA, '', '')
    dirB = os.path.join(dirB, '', '')
    for root, subFolders, fileList in os.walk(dirA):
      for file in fileList:
        files.add(file)

    for root, subFolders, fileList in os.walk(dirB):
      for file in fileList:
        files.add(file)

  if not os.path.exists(outputDir):
    os.makedirs(outputDir)

  for file in files:
    regA = Registry.Registry(dirA + file)
    regB = Registry.Registry(dirB + file)
    compare(regA, regB, file, outputDir)

  if not dirA:
    shutil.rmtree(TEMP_DIRECTORY_A)
    shutil.rmtree(TEMP_DIRECTORY_B)

  endTime = time.time()

  print u'Skript ausgeführt in {0}'.format(
    datetime.timedelta(seconds=round(endTime - startTime, 0)))

def extractFiles(g, image, tempPath):
  if not os.path.exists(tempPath):
    os.makedirs(tempPath)

  # Attach the first disk image read-only to libguestfs.
  g.add_drive_opts(image, readonly=1)

  # Run the libguestfs back-end.
  g.launch()

  for p in g.list_partitions():
    g.mount_ro(p, "/")

    #Suchen der Dateien gemäss Tabelle 5-1
    if g.exists("/Boot/BCD"):
      files.add("BCD")
      g.download("/Boot/BCD", tempPath + 'BCD')

    if g.exists("/Windows/System32/config/COMPONENTS"):
      files.add("COMPONENTS")
      g.download("/Windows/System32/config/COMPONENTS", tempPath + 'COMPONENTS')

    if g.exists("/Windows/System32/config/SYSTEM"):
      files.add("SYSTEM")
      g.download("/Windows/System32/config/SYSTEM", tempPath + 'SYSTEM')

    if g.exists("/Windows/System32/config/SAM"):
      files.add("SAM")
      g.download("/Windows/System32/config/SAM", tempPath + 'SAM')

    if g.exists("/Windows/System32/config/SECURITY"):
      files.add("SECURITY")
      g.download("/Windows/System32/config/SECURITY", tempPath + 'SECURITY')

    if g.exists("/Windows/System32/config/SOFTWARE"):
      files.add("SOFTWARE")
      g.download("/Windows/System32/config/SOFTWARE", tempPath + 'SOFTWARE')

    if g.exists("/Windows/System32/config/DEFAULT"):
      files.add("DEFAULT")
      g.download("/Windows/System32/config/DEFAULT", tempPath + 'DEFAULT')

    if g.exists("/Windows/ServiceProfiles/LocalService/NTUSER.DAT"):
      files.add("LOCALSERVICE_NTUSER.DAT")
      g.download("/Windows/System32/config/SOFTWARE",
        tempPath + 'LOCALSERVICE_NTUSER.DAT')

    if g.exists("/Windows/ServiceProfiles/NetworkService/NTUSER.DAT"):
      files.add("NETWORKSERVICE_NTUSER.DAT")
      g.download("/Windows/System32/config/SOFTWARE",
        tempPath + 'NETWORKSERVICE_NTUSER.DAT')

    if g.exists('/Users'):
      for dir in g.ls('/Users'):
        if g.is_dir('/Users/' + dir):
          if g.exists("/Users/" + dir + "/NTUSER.DAT"):
            files.add(dir + "_NTUSER.DAT")
            g.download("/Users/" + dir + "/NTUSER.DAT", tempPath + dir + '_NTUSER.DAT')

          if g.exists("/Users/" + dir + "/AppData/Local/Microsoft/Windows/UsrClass.dat"):
            files.add(dir + "_UsrClass.dat")
            g.download("/Users/" + dir + "/AppData/Local/Microsoft/Windows/UsrClass"
                                         ".dat", tempPath + dir + '_UsrClass.dat')

    g.umount_all()
  g.shutdown()

def displayValue(value):
  data_type = value.value_type()

  if data_type == Registry.RegSZ or data_type == Registry.RegExpandSZ or data_type == \
      Registry.RegDWord or data_type == Registry.RegQWord:
    try:
      return unicode(value.value(), errors='replace')
    except TypeError:
      return value.value()
  elif data_type == Registry.RegMultiSZ:
    str = ""
    delimiter = ""
    for string in value.value():
      str += delimiter
      str += string
      delimiter = " "
    return str
  elif data_type == Registry.RegBin or data_type == Registry.RegNone:
    return format_hex(value.value())
  else:
    try:
      return unicode(value.value(), errors='replace')
    except TypeError:
      return value.value()

def format_hex(data):
  byte_format = {}
  for c in xrange(256):
    if c > 126:
      byte_format[c] = '.'
    elif len(repr(chr(c))) == 3 and chr(c):
      byte_format[c] = chr(c)
    else:
      byte_format[c] = '.'

  def format_bytes(s):
    return "".join([byte_format[ord(c)] for c in s])

  def dump(src, length=16):
    N = 0
    result = ''
    while src:
      s, src = src[:length], src[length:]
      hexa = ' '.join(["%02X" % ord(x) for x in s])
      s = format_bytes(s)
      result += "%04X   %-*s   %s\n" % (N, length * 3, hexa, s)
      N += length
    return result

  return dump(data)

def readRegistry(key):
  content = {}
  content[key.path()] = None

  for value in key.values():
    content[key.path() + '\\' + value.name()] = value

  for subkey in key.subkeys():
    content.update(readRegistry(subkey))

  return content

def compare(regA, regB, file, outputDir):
  contentA = readRegistry(regA.root())
  contentB = readRegistry(regB.root())

  print u'Vergleich der Datei {0} --> Resultat: {1}'.format(file,
    outputDir + file + '.csv')

  with open(outputDir + file + '.csv', 'wb') as csvOutputfile:
    csvOutputfile.write(codecs.BOM_UTF8)
    outputFileWriter = csv.writer(csvOutputfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    outputFileWriter.writerow(
      ['KEY', 'TYPE_A', 'TYPE_B', 'VALUE_A', 'VALUE_B', 'EXISTIERT_IN_A',
        'EXISTIERT_IN_B', 'IDENTISCH'])

    for key, value in sorted(contentA.items()):
      existsInB = key in contentB

      if existsInB:
        compareMatchedContent(key, value, contentB[key], outputFileWriter)
        del contentA[key]
        del contentB[key]

    for key, value in sorted(contentA.items()):
      type = None
      valueStr = ''

      if value is not None:
        type = value.value_type_str()
        valueStr = displayValue(value)

      outputFileWriter.writerow(
        [key, type, None, unicode(valueStr, errors='replace').encode("utf-8"), None, True,
          False, False])

    for key, value in sorted(contentB.items()):
      type = None
      valueStr = ''

      if value is not None:
        type = value.value_type_str()
        valueStr = displayValue(value)

      outputFileWriter.writerow(
        [key, None, type, None, unicode(valueStr, errors='replace').encode("utf-8"),
          False, True, False])

def compareMatchedContent(key, entryA, entryB, outputFileWriter):
  identical = False
  typeA = None
  typeB = None
  valueStrA = None
  valueStrB = None

  if entryA is not None:
    typeA = entryA.value_type_str()
    valueStrA = displayValue(entryA)

  if entryB is not None:
    typeB = entryB.value_type_str()
    valueStrB = displayValue(entryB)

  if valueStrA is None and valueStrB is None:
    identical = True
  elif valueStrA is not None and valueStrA is not None and valueStrA == valueStrB:
    identical = True

  outputFileWriter.writerow(
    [unicode(key).encode("utf-8"), typeA, typeB, unicode(valueStrA).encode("utf-8"),
      unicode(valueStrB).encode("utf-8"), True, True, identical])

if __name__ == '__main__':
  main()