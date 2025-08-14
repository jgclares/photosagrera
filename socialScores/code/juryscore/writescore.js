// La función doPost se activa cuando la Web App recibe una solicitud POST.
function doPost(e) { 
  logToSheet('Entro en función Post Version 2');
  // Asegurarse de que el cuerpo de la solicitud no esté vacío
  if (!e || !e.postData || !e.postData.contents) {
    return ContentService.createTextOutput("Error: No data received.");
  }

  // Parsear el JSON recibido del HTML
  const data = JSON.parse(e.postData.contents);
  const juradoName = data.juradoName;
  const scores = data.scores;

  // Obtener la hoja de cálculo activa y la hoja de destino
  logToSheet('Obtener la hoja de cálculo activa y la hoja de destino');
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Puntuaciones'); // Asegúrate de que este nombre coincida con el de tu hoja
  if (!sheet) {
    return ContentService.createTextOutput("Error: Sheet 'Puntuaciones Jurado' not found.");
  }

  // Preparar los datos para la fila.
  // La primera columna será el nombre del jurado, las siguientes serán las puntuaciones.
  // Usamos el nombre del jurado para rellenar toda la columna A
  const photoLabels = scores.map((score, index) => `Foto ${index + 1}`);

  // Recorre las puntuaciones y añade una fila por cada una
  for (let i = 0; i < scores.length; i++) {
    const row = [photoLabels[i], scores[i], juradoName]; // Formato: [Etiqueta, Puntuación, Jurado]
    sheet.appendRow(row);
  }

  // Devolver una respuesta para indicar que la operación fue exitosa
  logToSheet('Devolver una respuesta para indicar que la operación fue exitosa');
  return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);
}

function logToSheet(message) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Logs");
  if (!sheet) return;
  sheet.appendRow([new Date(), message]);
}