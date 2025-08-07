#target photoshop

var userParams = null;

function getUserParams() {
    var dialog = new Window("dialog", "Parámetros de impresión");
    dialog.orientation = "column";
    dialog.alignChildren = "left";

    var maxSizeFrameGroup = dialog.add("group");
    maxSizeFrameGroup.orientation = "row";
    maxSizeFrameGroup.alignChildren = "left";
    maxSizeFrameGroup.add("statictext", undefined, "Lado más largo en pixels:");
    var maxSizeInput = maxSizeFrameGroup.add("edittext", undefined, "1920");
    maxSizeInput.characters = 10;

    var jpgQuality = dialog.add("group");
    jpgQuality.orientation = "row";
    jpgQuality.alignChildren = "left";
    jpgQuality.add("statictext", undefined, "Calidad del fichero jpg:");
    var jpgQualityInput = jpgQuality.add("edittext", undefined, "12");
    jpgQualityInput.characters = 10;
    
    dialog.add("statictext", undefined, "Ruta a la carpeta de origen:");
    var sourceFolderGroup = dialog.add("group");
    sourceFolderGroup.orientation = "row";
    sourceFolderGroup.alignChildren = "left";
    var sourceFolderInput = sourceFolderGroup.add("edittext", undefined, "");
    sourceFolderInput.characters = 30;
    var sourceFolderButton = sourceFolderGroup.add("button", undefined, "...");

    sourceFolderButton.onClick = function() {
        var sourceFolder = Folder.selectDialog("Seleccione la carpeta de origen");
        if (sourceFolder) {
            sourceFolderInput.text = sourceFolder.fsName;
        }
    };

    dialog.add("statictext", undefined, "Ruta a la carpeta de destino:");
    var resultFolderGroup = dialog.add("group");
    resultFolderGroup.orientation = "row";
    resultFolderGroup.alignChildren = "left";
    var resultFolderInput = resultFolderGroup.add("edittext", undefined, "");
    resultFolderInput.characters = 30;
    var resultFolderButton = resultFolderGroup.add("button", undefined, "...");

    resultFolderButton.onClick = function() {
        var resultFolder = Folder.selectDialog("Seleccione la carpeta de destino");
        if (resultFolder) {
            resultFolderInput.text = resultFolder.fsName;
        }
    };

    var buttonGroup = dialog.add("group");
    buttonGroup.orientation = "row";
    buttonGroup.alignment = "left";
    var okButton = buttonGroup.add("button", undefined, "OK", {name: "ok"});
    var cancelButton = buttonGroup.add("button", undefined, "Cancel", {name: "cancel"});


    okButton.onClick = function() {
        var maxSize = parseFloat(maxSizeInput.text);
        var jpgQuality = parseFloat(jpgQualityInput.text);
        var sourceFolder = sourceFolderInput.text;
        var resultFolder = resultFolderInput.text;

        if (maxSize < 100) {
            alert("El lado de la foto debe tener al menos 100 pixels.");
            return;
        }
        if (jpgQuality < 1 || jpgQuality > 12) {
            alert("La calidad del fichero jpg debe estar entre 1 y 12.");
            return;
        }
  
        if (sourceFolder === "") {
            alert("La ruta a la carpeta de origen no puede estar vacía.");
            return;
        }
        if (resultFolder === "") {
            alert("La ruta a la carpeta de destino no puede estar vacía.");
            return;
        }

        dialog.close(1);
    };

    cancelButton.onClick = function() {
        dialog.close(0);
    };

    if (dialog.show() == 1) {

        return {
            jpgQuality: parseFloat(jpgQualityInput.text),
            maxSize: parseFloat(maxSizeInput.text),
            sourceFolder: sourceFolderInput.text,
            resultFolder: resultFolderInput.text
        };
    } else {
        return null;
    }
}

function main() {

    // Set the ruler units to pixels
    app.displayDialogs = DialogModes.ERROR; // Show only ERRORS dialogs default option
    app.bringToFront(); // Bring Photoshop to the front
    app.preferences.rulerUnits = Units.PIXELS;  
    app.preferences.typeUnits = TypeUnits.PIXELS;


    if (app.documents.length > 0) {
        alert("Cierre todos los documentos abiertos antes de ejecutar el script.");
        return;
    }
    
    userParams = getUserParams();
    if (!userParams) {
        return;
    }
    
    

    // Use userParams.sourceFolder and userParams.resultFolder instead of prompting the user
    var sourceFolder = new Folder(userParams.sourceFolder);
    if (!sourceFolder.exists) {
        alert("No existe la carpeta de origen. Script cancelado.");
        return;
    }

    var destinationFolder = new Folder(userParams.resultFolder);
    if (!destinationFolder.exists) {
        alert("No existe la carpeta de estino. Script cancelado.");
        return;
    }

    var destFolderStr = null;
    if ($.os.indexOf("Windows") !== -1 )
        destFolderStr = destinationFolder.fsName.replace(/\\/g, "\\\\") + "\\\\"; // Escape backslashes for Windows paths
    else            
        destFolderStr = destinationFolder.fsName+ "/";

    // Get all JPG jpgFiles in the selected folder
    var jpgFiles = sourceFolder.getFiles(/\.(jpg|jpeg)$/i);
    if (jpgFiles.length == 0) {
        alert("No sen han encontrado ficheros JPG en la carpeta de origen.");
        return;
    }

    for (var i = 0; i < jpgFiles.length; i++) {
        var file = jpgFiles[i];
        var imagePath = file.fsName;

        // Display a progress message
        var progressMessage = "Processing file: " + decodeURI(new File(imagePath).name);
        $.writeln(progressMessage); // Log progress to the console 
        //alert(progressMessage); 
        
        // Open de source file (image to be placed) as a document   
        var doc = app.open(file);
        var sourceFileDecoded =  decodeURI(file.name);
        if (!(app.activeDocument === doc)) {
            alert("Error opening the image file: " + sourceFileDecoded);
          return;
        }

        var doc = app.activeDocument;
        // Get the width and height in pixels
        var widthInPixels = doc.width.value;
        var heightInPixels = doc.height.value;
        // Calculate the scale factor
        var maxSize = userParams.maxSize;
        var scaleFactor = Math.min(maxSize / widthInPixels, maxSize / heightInPixels);
        doc.resizeImage(widthInPixels * scaleFactor, heightInPixels * scaleFactor);

        // Guardar como JPEG en la carpeta de salida
        var charset = $.os.indexOf("Windows") !== -1 ? "Windows-1252" : "MacRoman";
        var destFilePathStr = destFolderStr + File.encode(decodeURI(jpgFiles[i].name), charset);
        var saveFile = new File(destFilePathStr);
        var saveOptions = new JPEGSaveOptions();
        saveOptions.quality = 12;
        doc.saveAs(saveFile, saveOptions, true, Extension.LOWERCASE);

        doc.close(SaveOptions.DONOTSAVECHANGES);
        
    }

    // Display a final message
    alert("Proceso finalizado correctamente!");
}



// Run the main function
main();

// End of script