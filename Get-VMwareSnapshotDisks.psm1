function Get-VMwareSnapshotDisks {
  [CmdletBinding()]
  param (
    [parameter(Mandatory=$true)]
    [string[]]$vmName
  )
  PROCESS {
    $vm = Get-VM $vmName;

    Get-HardDisk -vm $vm | Select-Object @{Name = "Aktuelle Festplatte(n)"; `
      Expression = { $_.FileName }};

    $snapshots = Get-Snapshot $vm;
    
    foreach ($snapshot in $snapshots){
      $out = new-object psobject; 
      $out | Add-Member "Name" ($snapshot.name); 
      $out | Add-Member "Beschreibung" ($snapshot.description); 
      $out | Add-Member "Erzeugt am" ($snapshot.created); 
      $out | Add-Member "Status" ($snapshot.powerstate); 
      $out | Add-Member "Parent Snapshot" ($snapshot.parentsnapshot); 

      $hd = Get-HardDisk -snapshot $snapshot; 
      $out | add-member "Delta-Festplatte" ($hd.filename); 

      Write-Output $out | Format-List
    }
  }
}