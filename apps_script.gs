// Tempel di Google Sheets: Extensions > Apps Script.
// Deploy > Manage deployments > Edit > New version  (Web app, Execute as: Me, Access: Anyone)

function doGet(e) {
  const p = e.parameter;
  if (p.aksi === 'perintah') return perintah_(p.id);
  return catatLokasi_(p);
}

function sheet_(nama, header) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName(nama) || ss.insertSheet(nama);
  if (sh.getLastRow() === 0) sh.appendRow(header);
  return sh;
}

function catatLokasi_(p) {
  const sh = sheet_('Lokasi', ['Waktu', 'Perangkat', 'Lat', 'Lng', 'Akurasi (m)', 'Peta']);
  const waktu = p.timestamp ? new Date(Number(p.timestamp) * 1000) : new Date();
  sh.appendRow([waktu, p.id, Number(p.lat), Number(p.lon), Number(p.accuracy),
    'https://maps.google.com/?q=' + p.lat + ',' + p.lon]);
  return ContentService.createTextOutput('ok');
}

// Sheet "Perintah": kolom B diubah manual menjadi AKTIF untuk memaksa pelacakan.
function perintah_(id) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sh = sheet_('Perintah', ['Perangkat', 'Status (STANDBY / AKTIF)', 'Terakhir online']);
    const n = Math.max(sh.getLastRow() - 1, 1);
    const ids = sh.getRange(2, 1, n, 1).getValues().map(r => String(r[0]));
    let row = ids.indexOf(String(id));
    if (row < 0) {
      sh.appendRow([id, 'STANDBY', new Date()]);
      row = sh.getLastRow();
      sh.getRange(row, 2).setDataValidation(
        SpreadsheetApp.newDataValidation().requireValueInList(['STANDBY', 'AKTIF'], true).build());
    } else {
      row += 2;
      sh.getRange(row, 3).setValue(new Date());
    }
    const status = String(sh.getRange(row, 2).getValue()).trim().toUpperCase();
    return ContentService.createTextOutput(status === 'AKTIF' ? 'AKTIF' : 'STANDBY');
  } finally {
    lock.releaseLock();
  }
}
