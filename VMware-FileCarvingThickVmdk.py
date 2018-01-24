#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import subprocess
import argparse
import time
import datetime

def main():
  # Definition der Argumente
  parser = argparse.ArgumentParser(
    description=u'File carving von VMDK-Festplatten im Thick-Format auf dem Datastore '
                u'von VMware vSphere Hypervisor')
  parser.add_argument('--datastore',
    help=u'Datastore kann entweder der Mountpoint des Datastores sein oder eine '
         u'Abbilddatei', required=True)
  parser.add_argument('--inputVmdk',
    help=u'Pfad und Name der VMDK-Festplatte (auf dem Datastore), welche dem File '
         u'Carving unterzogen wird', required=True)
  parser.add_argument('--outputVmdk',
    help=u'Lokaler Dateipfad der Datei, in welche die Ergebnisse geschrieben werden',
    required=True)
  args = vars(parser.parse_args())

  datastore = args.get('datastore')
  inputVmdk = args.get('inputVmdk')
  outputVmdk = args.get('outputVmdk')

  def openDebugvmfsShell():
    return subprocess.Popen(['sudo', '-S', 'debugvmfs', datastore, 'shell'],
      stdin=subprocess.PIPE, stdout=subprocess.PIPE)

  #Messen der benötigten Zeit
  startTime = time.time()

  #Starten der Shell von debugvmfs
  debugvmfsProcess = openDebugvmfsShell()

  #Abfragen der Inode-Nummer
  command = 'show inode["' + inputVmdk + '"]\n'
  debugvmfsOutput = debugvmfsProcess.communicate(command)[0]

  print u'Inode von {0}:'.format(inputVmdk)
  print debugvmfsOutput

  debugvmfsProcess = openDebugvmfsShell()

  #Abfragen der Inode-Blocks
  command = 'show inode["' + inputVmdk + '"].blocks\n'
  debugvmfsOutput = debugvmfsProcess.communicate(command)[0]
  blocks = debugvmfsOutput.replace('\n', ' ')
  blocks = blocks.strip()
  blocks = blocks.split(' ')

  print u'Inode-Blocks von {0}:'.format(inputVmdk)
  print debugvmfsOutput

  i = 0
  for block in blocks:
    i = i + 1

    debugvmfsProcess = openDebugvmfsShell()

    #Abfragen des Items hinter des Inode-Blocks
    command = 'show blkid["' + block.strip() + '"].item\n'

    debugvmfsOutput = debugvmfsProcess.communicate(command)[0]
    debugvmfsProcess = openDebugvmfsShell()
    blkRef = debugvmfsOutput[15:].replace('\n', '')
    command = 'show ' + blkRef + '''.blocks\n'''

    #Abfragen der Block-Adressen
    debugvmfsOutput = debugvmfsProcess.communicate(command)[0]
    debugvmfsOutput = debugvmfsOutput.replace('\n', ' ')
    debugvmfsOutput = debugvmfsOutput.strip()
    blockAddresses = debugvmfsOutput.split(' ')
    j = 0

    for blockAddress in blockAddresses:
      j = j + 1
      debugvmfsProcess = openDebugvmfsShell()
      command = 'read_block ' + blockAddress.strip() + '\n'

      print u'Inode-Block {0} ({1}/{2}) - Lesen von Adresse {3} ({4}/{5})'.format(block,
        str(i), str(len(blocks)), blockAddress, str(j), str(len(blockAddresses)))

      #Abfragen des Inhalts der entsprechenden Block-Adresse
      debugvmfsOutput = debugvmfsProcess.communicate(command)[0]
      outputVmdkFile = open(outputVmdk, 'ab')
      outputVmdkFile.write(debugvmfsOutput)

  endTime = time.time()

  print u'Inhalt erfolgreich in Datei "{0}" extrahiert'.format(outputVmdk)
  print ''
  print u'Skript ausgeführt in {0}'.format(
    datetime.timedelta(seconds=round(endTime - startTime, 0)))

if __name__ == '__main__':
  main()