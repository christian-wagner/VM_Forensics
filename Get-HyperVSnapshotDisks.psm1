function Get-HyperVSnapshotDisks {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)]
    [String]$vmName
  )
  process { 
    Get-VM -Name $vmName | Get-VMHardDiskDrive | Select-Object @{Name = "Aktuelle ` 
Festplatte(n)"; Expression = {$_.Path}} | Format-List

    foreach ($snapshot in Get-VM -Name $vmName | Get-VMSnapshot) {
      $out = new-object psobject;
      $out | Add-Member Id ($snapshot.Id);
      $out | Add-Member Name ($snapshot.Name);
      $out | Add-Member "Erzeugt am" ($snapshot.CreationTime);
      $out | Add-Member ParentSnapshotName ($snapshot.ParentSnapshotName);
      $out | Add-Member ParentSnapthotId ($snapshot.ParentSnapshotId);

      $hardDisk = $snapshot | Get-VMHardDiskDrive
      $out | Add-Member Delta-Festplatte ($hardDisk.Path);

      $depth = 0

      while (![string]::IsNullOrEmpty($snapshot.ParentSnapshotId)) {
        $depth = $depth + 1
        $snapshot = Get-VMSnapshot -Id $snapshot.ParentSnapshotId
      }

      $out | Add-Member Hierarchiestufe ($depth);

      Write-Output $out | Format-List
    }
  }
}