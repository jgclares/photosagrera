#target photoshop

function loadImageAsimageLayer(sourceFile, savePath) {
    // Check if a document is open
    if (app.documents.length == 0) {
        alert("Please open a document first.");
        return;
    }
    var sourceFileDecoded =  decodeURI(sourceFile.name);
	var authorName = sourceFileDecoded.substring(0, sourceFileDecoded.lastIndexOf('.'));
    // Get the current active document
    var doc = app.activeDocument;

    // Place the image as a smart object
    var desc = new ActionDescriptor();
    desc.putPath(charIDToTypeID("null"), sourceFile);
    desc.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
    executeAction(charIDToTypeID("Plc "), desc, DialogModes.NO);

    // Get the newly placed layer
    var imageLayer = doc.activeLayer;
    imageLayer.name = sourceFileDecoded;

    // Resize and position the new layer
    var docWidth = doc.width.as("cm");
    var docHeight = doc.height.as("cm");

    var targetWidth = docWidth - 6; // 3 cm from each side
    var targetHeight = docHeight - 8; // 4 cm from top, 4  cm from bottom
	
	var imageLayerWidth = (imageLayer.bounds[2] - imageLayer.bounds[0]).as("cm");
	var imageLayerHeight = (imageLayer.bounds[3] - imageLayer.bounds[1]).as("cm");

    var aspectRatio = imageLayerWidth / imageLayerHeight;
	
	var xFactor= targetWidth / imageLayerWidth * 100;
	var yFactor= targetHeight / imageLayerHeight * 100;
	
	//alert("x =" +xFactor + " y="+ yFactor);
	
    if ( aspectRatio > 1) {   //(targetWidth / targetHeight < aspectRatio)
        imageLayer.resize(xFactor, xFactor);
    } else {
        imageLayer.resize(yFactor, yFactor);
    }

    imageLayer.translate((3 - imageLayer.bounds[0].as("cm")), (4 - imageLayer.bounds[1].as("cm")));

    // Add text layer
    var textLayer = doc.artLayers.add();
    textLayer.kind = LayerKind.TEXT;
	
    var textItem = textLayer.textItem;
    textItem.contents = authorName;
    textItem.size = 14;
    textItem.font = "Verdana";
	// Calculate layers Witdth and Height
	var textLayerWidth = (textLayer.bounds[2] - textLayer.bounds[0]).as("cm");
	// Height in pixels
	var textLayerHeight = (textLayer.bounds[3] - textLayer.bounds[1]).as("cm");
	var imageLayerHeight = (imageLayer.bounds[3] - imageLayer.bounds[1]).as("cm");
	
	// Text position
	var x= docWidth - 3 - textLayerWidth
	var y= 4 + imageLayerHeight + 2
	//alert("x =" +x + " y="+ y);
    textItem.position = [x, y]; // Align text to the bottom right of the image
 
	var textColor = new SolidColor(); 
	textColor.rgb.red = 114;
	textColor.rgb.green = 114;
	textColor.rgb.blue = 114;
	textItem.color = textColor;
	
    //textItem.color.rgb.hexValue = "727272";
    textLayer.name = authorName;
	

    // Save as JPG
    var jpgOptions = new JPEGSaveOptions();
    jpgOptions.quality = 12; // Maximum quality
	
    var saveFile = new File(savePath);
    doc.saveAs(saveFile, jpgOptions, true, Extension.LOWERCASE);
    
    // Hide the image layer after saving
    // imageLayer.visible = false;
    
    // Save the document
    doc.save();
    
    alert("Image processed and saved successfully!");

}

// Replace this path with the path to your JPEG image and save path
var sourceFile = File.openDialog("Select JPG file", "*.jpg");

if (sourceFile) {
	var destFolderStr = File.encode("Z:\\Fotos\\Fotos Originales\\PhotoSagrera\\Exposición Steampunk\\", "Windows-1252");
    var destFilePathStr = destFolderStr + File.encode(decodeURI(sourceFile.name), "Windows-1252");
	var destFolder = new Folder(destFolderStr);
    if (!destFolder.exists) {
        destFolder.create();
    }
    loadImageAsimageLayer(sourceFile, destFilePathStr);
}
