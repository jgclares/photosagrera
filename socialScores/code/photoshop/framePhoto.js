#target photoshop

function processImage() {
    // Prompt user to select the JPG file
    var sourceFile = File.openDialog("Select JPG file", "*.jpg");
    
    if (!sourceFile) {
        alert("No file selected. Script cancelled.");
        return;
    }

    // Open the source file
    var originalDoc = app.open(sourceFile);
    
    // Select the background document (assumed to be already open)
    var backgroundDoc = app.activeDocument;
    
    // Convert measurements to pixels (assuming 300 DPI)
    var docResolution = 300; // standard resolution
    var cmToPixels = docResolution / 2.54; // conversion factor
    
    // Background document dimensions
    var bgWidth = backgroundDoc.width.value;
    var bgHeight = backgroundDoc.height.value;
    
    // Resize parameters
    var topMargin = 4 * cmToPixels;
    var sideMargin = 2 * cmToPixels;
    
    // Calculate new image dimensions while preserving aspect ratio
    var targetWidth = bgWidth - (2 * sideMargin);
    var scaleFactor = targetWidth / originalDoc.width.value;
    var targetHeight = originalDoc.height.value * scaleFactor;
    
    // Ensure the image fits vertically
    if ((targetHeight + topMargin) > bgHeight) {
        scaleFactor = (bgHeight - topMargin) / originalDoc.height.value;
        targetWidth = originalDoc.width.value * scaleFactor;
        targetHeight = originalDoc.height.value * scaleFactor;
    }
    
    // Resize the original document
    originalDoc.resizeImage(
        UnitValue(targetWidth, "px"), 
        UnitValue(targetHeight, "px"), 
        docResolution, 
        ResampleMethod.BICUBIC
    );
    
    // Select and copy the resized image
    originalDoc.selection.selectAll();
    originalDoc.selection.copy();
    
    // Switch back to background document
    app.activeDocument = backgroundDoc;
    
    // Paste the image as a new layer
    backgroundDoc.paste();
    
    // Position the new layer
    var newLayer = backgroundDoc.activeLayer;
    newLayer.translate(
        UnitValue(sideMargin, "px"), 
        UnitValue(topMargin, "px")
    );
    
    // Add text layer with filename
    var textLayer = backgroundDoc.artLayers.add();
    textLayer.kind = LayerKind.TEXT;
    
    // Configure text
    var textItem = textLayer.textItem;
    textItem.contents = sourceFile.name;
    textItem.font = "Verdana";
    textItem.size = 14;
    textItem.color = new SolidColor();
    textItem.color.rgb.hexValue = "727272";
    
    // Position text 2 cm below image bottom, aligned to right
    textItem.position = [
        UnitValue(bgWidth - sideMargin, "px"), 
        UnitValue(topMargin + targetHeight + (2 * cmToPixels), "px")
    ];
    textItem.justification = Justification.RIGHT;
    
    // Save the file
    var saveFolder = new Folder("Z:\\Fotos\\Fotos Originales\\PhotoSagrera\\Exposición Steampunk");
    if (!saveFolder.exists) {
        saveFolder.create();
    }
    
    var saveFile = new File(saveFolder + "\\" + sourceFile.name);
    var saveOptions = new JPEGSaveOptions();
    saveOptions.quality = 100;
    
    backgroundDoc.saveAs(saveFile, saveOptions, true, Extension.LOWERCASE);
     // Hide the image layer after saving
     imageLayer.visible = false;
    
     // Save the document
     backgroundDoc.save();
     
     // Close source document, saving changes
     originalDoc.close(SaveOptions.SAVECHANGES);
    
    alert("Image processed and saved successfully!");
}

// Run the script
processImage();