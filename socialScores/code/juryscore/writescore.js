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
    return ContentService.createTextOutput("Error: Sheet 'Puntuaciones' not found.");
  }

  // Encuentra la siguiente columna vacía
  const lastCol = sheet.getLastColumn();
  const newCol = lastCol + 1;

  // Escribe el nombre del jurado en la cabecera
  sheet.getRange(1, newCol).setValue(juradoName);

  // Inserta cada puntuación en la fila correspondiente
  for (let i = 0; i < scores.length; i++) {
    // +2 porque la primera fila es cabecera y los datos empiezan en la segunda
    sheet.getRange(i + 2, newCol).setValue(scores[i]);
  }

  // Devolver una respuesta para indicar que la operación fue exitosa
  logToSheet('Devolver una respuesta para indicar que la operación fue exitosa');
  return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);
}

// La función doGet se activa cuando la Web App recibe una solicitud GET.
// Esta función devuelve el número de filas de datos en la hoja 'Puntuaciones'. 
function doGet(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Puntuaciones');
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        error: "Sheet 'Puntuaciones' not found"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Obtener el número de filas, excluyendo el encabezado
    const numRows = sheet.getLastRow() - 1;
    
    // Devolver la respuesta como JSON
    return ContentService.createTextOutput(JSON.stringify({
      numRows: numRows,
      status: "success"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      error: error.toString(),
      status: "error"
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// Función para registrar mensajes en una hoja de cálculo llamada "Logs"
function logToSheet(message) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Logs");
  if (!sheet) return;
  sheet.appendRow([new Date(), message]);
}

