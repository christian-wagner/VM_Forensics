#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import subprocess
import locale
import mmap
import os
import argparse
import time
import datetime
import csv
import codecs

#individuell anpassbarer Speicherort des Volatility-Frameworks
VOLATILITY_LOCATION = r'/usr/local/volatility-2.4/vol.py'

class TagEntry:
  def __init__(self):
    self.dataOffset = None
    self.dataSize = None
    self.name = None
    self.data = None

#Erzeugt eine separate Datei mit den jeweils extrahierten Daten
def createFile(inputFileName, outputFileName, tagEntry):
  outputFile = open(outputFileName, 'w+b')
  with open(inputFileName, 'rb') as file:
    m = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
    cfg = m[int(tagEntry.dataOffset, 0):(
      int(tagEntry.dataOffset, 0) + int(tagEntry.dataSize, 0))]
    outputFile.write(cfg)
  outputFile.close()
  print u'Datei {0} gespeichert'.format(outputFileName)

def main():
  #Definition der Argumente
  parser = argparse.ArgumentParser(
    description=u'Extrahierung von Daten aus VMware vmss/vmsn-Dateien')
  parser.add_argument('--file',
    help=u'Die vom Host gesicherte vmss/vmsn-Datei einer virtuellen Maschine',
    required=True)
  parser.add_argument('--outputDir',
    help=u'Verzeichnis, in das die Ergebnisse geschrieben werden', required=True)
  args = vars(parser.parse_args())
  inputFile = args.get('file')
  outputDir = os.path.join(args.get('outputDir'), '', '')

  #Messen der benötigten Zeit
  startTime = time.time()

  #Extrahieren des Namens des Gastes
  guestName = os.path.basename(inputFile).rsplit('-')[0]
  encoding = locale.getdefaultlocale()[1]

  #Ausführen des Volatility-Befehls und Speichern der Ausgabe
  vmwareInfoOutput = subprocess.check_output(
    [r'python', VOLATILITY_LOCATION, r'--filename=' + inputFile, r'vmwareinfo'])

  entries = {}
  startIndex = 0

  #die ersten Zeilen ignorieren, diese enthalten keine verwertbaren Informationen,
  #erst nachdem der Spaltentitel DataOffset vorhanden ist beginnen verwertbare
  #Informationen
  for line in vmwareInfoOutput.decode(encoding).split('\n'):
    startIndex += 1
    if line.startswith('DataOffset'):
      startIndex += 1
      break;

  #Erstelle für jede Zeile der Ausgabe einen Eintrag
  for line in vmwareInfoOutput.decode(encoding).split('\n')[startIndex:-1]:
    lineSplit = line.split()
    tagEntry = TagEntry()
    tagEntry.dataOffset = lineSplit[0].strip()
    tagEntry.dataSize = lineSplit[1].strip()
    tagEntry.name = lineSplit[2].strip()

    if len(lineSplit) > 3:
      tagEntry.data = lineSplit[3].strip()

    entries[tagEntry.name] = tagEntry

  if not os.path.exists(outputDir):
    os.makedirs(os.path.dirname(outputDir))

  #CSV-Datei erzeugen
  csvOutputFile = open(outputDir + guestName + '-volatileData.csv', 'wb')
  csvOutputFile.write(codecs.BOM_UTF8)
  outputFileWriter = csv.writer(csvOutputFile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
  outputFileWriter.writerow(['DATA_OFFSET', 'DATA_LENGTH', 'NAME', 'DATA'])
  print u'Datei {0} gespeichert'.format(outputDir + guestName + '-volatileData.csv')

  #Speichere bekannte Daten in separate Dateien
  for key, value in sorted(entries.items()):
    if 'vm.powerOnTimeStamp.clientData' in key and value.data != '0x0':
      #Erstellen einer separaten Datei für timestamps
      f = open(outputDir + guestName + '-timestamps.txt', 'w+')
      timestamp = datetime.datetime.fromtimestamp(int(value.data, 0))
      f.write(u'Zeitpunkt Power on: %s\r\n' % (timestamp.strftime('%d. %b %Y %H:%M:%S')))
      f.close()
      print u'Datei {0} gespeichert'.format(outputDir + guestName + '-timestamps.txt')
    elif 'vm.suspendTime.clientData' in key and value.data != '0x0':
      #Erstellen einer separaten Datei für timestamps
      f = open(outputDir + guestName + '-timestamps.txt', 'a')
      timestamp = datetime.datetime.fromtimestamp(int(value.data, 0))
      f.write(u'Zeitpunkt Suspend: %s' % (timestamp.strftime('%d. %b %Y %H:%M:%S')))
      f.close()
    elif 'Snapshot/cfgFile' in key:
      #Erstellen einer separaten Datei für cfgFile
      createFile(inputFile, outputDir + guestName + '.vmx', value)
    elif 'Snapshot/nvramFile' in key:
      #Erstellen einer separaten Datei für nvramFile
      createFile(inputFile, outputDir + guestName + '.nvram', value)
    elif 'Snapshot/extendedConfigFile' in key:
      #Erstellen einer separaten Datei für extendedConfigFile
      createFile(inputFile, outputDir + guestName + '.vmxf', value)
    elif 'Cs440bx/romImage' in key:
      #Erstellen einer separaten Datei für romImage
      createFile(inputFile, outputDir + guestName + '.rom', value)
    elif 'MKSVMX/imageData' in key:
      #Erstellen einer separaten Datei für imageData
      createFile(inputFile, outputDir + guestName + '.png', value)
      numScreenshots = int(entries.get('MKSVMX/checkpoint.mks.numScreenshots').data, 0)
      #Falls mehrere Monitore an die virtuelle Maschine angeschlossen sind
      if numScreenshots > 1:
        for i in range(numScreenshots):
          createFile(inputFile, outputDir + guestName + '_' + (i + 1) + '.png',
            entries.get('MKSVMX/checkpoint.mks.screenshot[' + (i + 1) + ']'))

    #Hinzufügen in CSV-Datei
    outputFileWriter.writerow([value.dataOffset, value.dataSize, value.name, value.data])

  endTime = time.time()

  print ''
  print u'Skript ausgeführt in {0}'.format(
    datetime.timedelta(seconds=round(endTime - startTime, 0)))

if __name__ == '__main__':
  main()