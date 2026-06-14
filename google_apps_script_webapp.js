// Google Sheets dashboard receiver for AIoT Smart Recycling System
// Deploy as Web App and paste the Web App URL into config.py SHEETS_WEBAPP_URL.
// Mobile alerts are intentionally not included.

const SHEET_NAME = 'events';

function doPost(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);

  const headers = [
    'received_at',
    'timestamp',
    'event_type',
    'status',
    'label',
    'category',
    'confidence',
    'temperature_c',
    'humidity_percent',
    'fullness_sensor',
    'distance_cm',
    'fullness_percent',
    'image_path',
    'annotated_path',
    'note'
  ];

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }

  const data = JSON.parse(e.postData.contents);
  sheet.appendRow([
    new Date(),
    data.timestamp || '',
    data.event_type || '',
    data.status || '',
    data.label || '',
    data.category || '',
    data.confidence || '',
    data.temperature_c || '',
    data.humidity_percent || '',
    data.fullness_sensor || '',
    data.distance_cm || '',
    data.fullness_percent || '',
    data.image_path || '',
    data.annotated_path || '',
    data.note || ''
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
