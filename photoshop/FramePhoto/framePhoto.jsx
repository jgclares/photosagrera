#target photoshop

function processImage() {
    // Prompt user to select the JPG file
    var sourceFile = File.openDialog("Select JPG file", "*.jpg");
    
    if (!sourceFile) {
        alert("No file selected. Script cancelled.");
        return;
    }

    // Get the current active document
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
    
    // Open the image file as a layer in the current document
    var imageLayer = backgroundDoc.artLayers.add();
    imageLayer.name = sourceFile.name;
    
    // Load image into the layer
    app.load(sourceFile, imageLayer);
    
    // Calculate new image dimensions while preserving aspect ratio
    var targetWidth = bgWidth - (2 * sideMargin);
    var scaleFactor = targetWidth / imageLayer.bounds[2].value;
    var targetHeight = imageLayer.bounds[3].value * scaleFactor;
    
    // Ensure the image fits vertically
    if ((targetHeight + topMargin) > bgHeight) {
        scaleFactor = (bgHeight - topMargin) / imageLayer.bounds[3].value;
        targetWidth = imageLayer.bounds[2].value * scaleFactor;
        targetHeight = imageLayer.bounds[3].value * scaleFactor;
    }
    
    // Resize the layer
    imageLayer.resize(
        scaleFactor * 100, 
        scaleFactor * 100, 
        AnchorPosition.MIDDLECENTER
    );
    
    // Position the new layer
    imageLayer.translate(
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
    var saveFolder = new Folder("Z:\\Fotos\\Fotos Originales\\PhotoSagrera\\Exposición Steempunk");
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
    
    alert("Image processed and saved successfully!");
}

// Run the script
processImage();