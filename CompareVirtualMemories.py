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
#VOLATILITY_LOCATION = r'/usr/local/volatility-2.4/vol.py'
VOLATILITY_LOCATION = r'C:\Workarea\Transfer\volatility_2.4.win.standalone\volatility-2.4.standalone.exe'

class ProcessEntry:
  def __init__(self):
    self.offset = None
    self.name = None
    self.pid = None
    self.ppid = None
    self.threads = None
    self.handles = None
    self.sessions = None
    self.wow64 = None
    self.start = None
    self.exit = None

def parsePslistOutput(volatilityOutput):
  encoding = locale.getdefaultlocale()[1]
  startIndex = 0
  entries = {}

  #die ersten Zeilen ignorieren, diese enthalten keine verwertbaren Informationen,
  #erst nachdem der Spaltentitel Offset(V) vorhanden ist beginnen verwertbare
  # Informationen
  for line in volatilityOutput.decode(encoding).split('\n'):
    startIndex += 1
    if line.startswith("Offset(V)"):
      startIndex += 1
      break;

  #aus den einzelnen Prozesseinträge werden Datenstrukturen erzeugt
  for line in volatilityOutput.decode(encoding).split('\n')[startIndex:-1]:
    lineSplit = line.split()
    processEntry = ProcessEntry()
    processEntry.offset = lineSplit[0].strip()
    processEntry.name = lineSplit[1].strip()
    processEntry.pid = lineSplit[2].strip()
    processEntry.ppid = lineSplit[3].strip()
    processEntry.threads = lineSplit[4].strip()
    processEntry.handles = lineSplit[5].strip()
    processEntry.sessions = lineSplit[6].strip()
    processEntry.wow64 = lineSplit[7].strip()
    processEntry.start = lineSplit[8].strip() + ' ' + lineSplit[9].strip() + ' ' + \
                         lineSplit[10].strip()
    if len(lineSplit) > 11:
      processEntry.exit = lineSplit[11].strip() + ' ' + lineSplit[12].strip() + ' ' + \
                          lineSplit[13].strip()
    entries[processEntry.pid + processEntry.name] = processEntry

  return entries

#Vergleich der Metadaten der Prozesse, wenn diese in beiden Momentaufnahmen vorhanden sind
def compareMatchedContent(entryA, entryB, outputFileWriter):
  offsetIdentisch = True
  nameIdentisch = True
  ppidIdentisch = True
  threadsIdentisch = True
  handlesIdentisch = True
  sessionsIdentisch = True
  wow64Identisch = True
  startIdentisch = True
  exitIdentisch = True
  allesIdentisch = True

  if entryA.offset != entryB.offset:
    offsetIdentisch = False
    allesIdentisch = False

  if entryA.name != entryB.name:
    nameIdentisch = False
    allesIdentisch = False

  if entryA.ppid != entryB.ppid:
    ppidIdentisch = False
    allesIdentisch = False

  if entryA.threads != entryB.threads:
    threadsIdentisch = False
    allesIdentisch = False

  if entryA.handles != entryB.handles:
    handlesIdentisch = False
    allesIdentisch = False

  if entryA.sessions != entryB.sessions:
    sessionsIdentisch = False
    allesIdentisch = False

  if entryA.wow64 != entryB.wow64:
    wow64Identisch = False
    allesIdentisch = False

  if entryA.start != entryB.start:
    startIdentisch = False
    allesIdentisch = False

  if entryA.exit != entryB.exit:
    exitIdentisch = False
    allesIdentisch = False

  outputFileWriter.writerow(
    [entryA.offset, entryB.offset, entryA.name, entryB.name, entryA.pid, entryA.ppid,
      entryB.ppid, entryA.threads, entryB.threads, entryA.handles, entryB.handles,
      entryA.sessions, entryB.sessions, entryA.wow64, entryB.wow64, entryA.start,
      entryB.start, entryA.exit, entryB.exit, True, True, offsetIdentisch, nameIdentisch,
      ppidIdentisch, threadsIdentisch, handlesIdentisch, sessionsIdentisch,
      wow64Identisch, startIdentisch, exitIdentisch, allesIdentisch])

def writeCsvEntry(csvFileWriter, entry):
  csvFileWriter.writerow(entry)

def main():
  #Definition der Argumente
  parser = argparse.ArgumentParser(
    description=u'Vergleich des Hauptspeichers virtueller Maschinen')
  parser.add_argument('--memoryA',
    help=u'Dump A des Hauptspeichers einer virtuellen Maschine', required=True)
  parser.add_argument('--memoryB',
    help=u'Dump B des Hauptspeichers einer virtuellen Maschine', required=True)
  parser.add_argument('--volCommand', help=u'Auszuführendes Volatility-Plugin',
    required=True)
  parser.add_argument('--profile', help=u'Volatility-Profil der Hauptspeicherabbilder',
    required=True)
  parser.add_argument('--csv',
    help=u'Dateipfad der CSV-Datei, die die Ergebnisse des Vergleichs enthält',
    required=True)

  args = vars(parser.parse_args())
  memoryA = args.get('memoryA')
  memoryB = args.get('memoryB')
  volCommand = args.get('volCommand')
  csvFile = args.get('csv')
  profile = args.get('profile')

  #Messen der benötigten Zeit
  startTime = time.time()

  if volCommand == 'pslist':
    volatilityOutputA = subprocess.check_output(
      [VOLATILITY_LOCATION, r'--filename=' + memoryA, r'--profile=' + profile,
        volCommand])
    volatilityOutputB = subprocess.check_output(
      [VOLATILITY_LOCATION, r'--filename=' + memoryB, r'--profile=' + profile,
        volCommand])

    processesA = parsePslistOutput(volatilityOutputA)
    processesB = parsePslistOutput(volatilityOutputB)

    with open(csvFile, 'wb') as csvOutputfile:
      csvOutputfile.write(codecs.BOM_UTF8)
      outputFileWriter = csv.writer(csvOutputfile, delimiter=';',
        quoting=csv.QUOTE_MINIMAL)
      writeCsvEntry(outputFileWriter,
        ['OFFSET_A', 'OFFSET_B', 'NAME_A', 'NAME_B', 'PID', 'PPID_A', 'PPID_B',
          'THREADS_A', 'THREADS_B', 'HANDLES_A', 'HANDLES_B', 'SESSIONS_A', 'SESSIONS_B',
          'WOW64_A', 'WOW64_B', 'START_A', 'START_B', 'EXIT_A', 'EXIT_B',
          'EXISTIERT_IN_A', 'EXISTIERT_IN_B', 'OFFSET_IDENTISCH', 'NAME_IDENTISCH',
          'PPID_IDENTISCH', 'THREADS_IDENTISCH', 'HANDLES_IDENTISCH',
          'SESSIONS_IDENTISCH', 'WOW64_IDENTISCH', 'START_IDENTISCH', 'EXIT_IDENTISCH',
          'ALLES_IDENTISCH'])
      anzExistInBoth = 0

      for key, value in processesA.items():
        existsInB = key in processesB
        if existsInB:
          compareMatchedContent(value, processesB[key], outputFileWriter)
          anzExistInBoth = anzExistInBoth + 1
          del processesA[key]
          del processesB[key]

      for key, value in processesA.items():
        writeCsvEntry(outputFileWriter,
          [value.offset, None, value.name, None, value.pid, value.ppid, None,
            value.threads, None, value.handles, None, value.sessions, None, value.wow64,
            None, value.start, None, value.exit, None, True, False, None, None, None,
            None, None, None, None, None, None, None])

      for key, value in processesB.items():
        writeCsvEntry(outputFileWriter,
          [None, value.offset, None, value.name, value.pid, None, value.ppid, None,
            value.threads, None, value.handles, None, value.sessions, None, value.wow64,
            value.start, None, value.exit, None, False, True, None, None, None, None,
            None, None, None, None, None, None])

    print u'Anzahl Prozesse in beiden Hauptspeicherabbildern vorhanden : {0}'.format(
      anzExistInBoth)
    print u'Anzahl Prozesse nur im 1. Hauptspeicherabbild vorhanden    : {0}'.format(
      len(processesA))
    print u'Anzahl Prozesse nur im 2. Hauptspeicherabbild vorhanden    : {0}'.format(
      len(processesB))
    print ''
    print u'Resultat des Vergleichs in Datei {0} ersichtlich.'.format(csvFile)
    print ''

  else:
    print u'Der Volatility-Befehl {0} wird nicht unterstützt'.format(volCommand)

  endTime = time.time()

  print u'Skript ausgeführt in {0}'.format(
    datetime.timedelta(seconds=round(endTime - startTime, 0)))

if __name__ == '__main__':
  main()