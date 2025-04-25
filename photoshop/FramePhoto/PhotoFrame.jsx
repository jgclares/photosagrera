#target photoshop

var verticalDoc;
var horizontalDoc;
var userParams;

function loadImageAsimageLayer(sourceFile, savePath) {
    // Check if a document is open
    if (app.documents.length == 0) {
        alert("Please open a document first.");
        return;
    }
    var sourceFileDecoded =  decodeURI(sourceFile.name);
	var authorName = sourceFileDecoded.substring(0, sourceFileDecoded.lastIndexOf('.'));

    // Open de source file (image to be placed) as a document   
    var image_doc = app.open(new File(sourceFile));
        
    if (!(app.activeDocument === image_doc)) {
        alert("Error opening the image file: " + sourceFileDecoded);
        return;
    }

    if (userParams.orientation == 'h') {
        app.activeDocument = horizontalDoc;
    } else if (userParams.orientation == 'v') {  
        app.activeDocument = verticalDoc;
    } else {
        var imageAspectRatio = image_doc.width / image_doc.height;
        if (imageAspectRatio > 1.0) { // horizontal
            app.activeDocument = horizontalDoc;
        } else {
            app.activeDocument = verticalDoc;
        }
    }
    image_doc.close(SaveOptions.DONOTSAVECHANGES);

    
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

    // Compute ratio of the image layer
	var imageLayerWidth = (imageLayer.bounds[2] - imageLayer.bounds[0]).as("cm");
	var imageLayerHeight = (imageLayer.bounds[3] - imageLayer.bounds[1]).as("cm");
    // alert("ImageLayerWidth =" + imageLayerWidth + " ImageLayerHeight="+ imageLayerHeight);
    var aspectRatio = imageLayerWidth / imageLayerHeight;

    // Resize and position the new layer
    var docWidth = doc.width.as("cm");
    var docHeight = doc.height.as("cm");

    var targetWidth = docWidth - 6; // 3 cm from each side
    var targetHeight = docHeight - 8; // 4 cm from top, 4  cm from bottom
	

		
	var xFactor= targetWidth / imageLayerWidth * 100;
	var yFactor= targetHeight / imageLayerHeight * 100;
	

	
	// if horizontal (aspectRatio >= 1) or vertical but applying yScale would exceed target width size: scale horizontal, else scale vertical
	var factor = 1.0;
    if ( aspectRatio >= 1.0  ) { 
		if (imageLayerWidth * yFactor/100  >  targetWidth) {
			factor=xFactor;
		} else { 
			factor=yFactor;
		}
    } else {
       	if (imageLayerHeight * xFactor/100  >  targetHeight) {
			factor=yFactor;
		} else { 
			factor=xFactor;
		}
    }
	
	imageLayer.resize(factor, factor);

    imageLayer.translate((3 - imageLayer.bounds[0].as("cm")), (4 - imageLayer.bounds[1].as("cm")));
	
	// New imagelayer size after scaling
	var newImageLayerWidth = (imageLayer.bounds[2] - imageLayer.bounds[0]).as("cm");
	var newImageLayerHeight = (imageLayer.bounds[3] - imageLayer.bounds[1]).as("cm");
	
	// if not wide enough center the image only horizontal axe
	if (newImageLayerWidth + 0.05 < targetWidth) {
		
		imageLayer.translate( (docWidth - newImageLayerWidth)/2 - imageLayer.bounds[0].as("cm"), 0 );
	}

    // Add text layer
    var textLayer = doc.artLayers.add();
    textLayer.kind = LayerKind.TEXT;
	
    var textItem = textLayer.textItem;
    textItem.contents = cleanFileName(authorName);
    textItem.size = 14;
    textItem.font = "Verdana";
	// Calculate layers Witdth and Height
	var textLayerWidth = (textLayer.bounds[2] - textLayer.bounds[0]).as("cm");
	var textLayerHeight = (textLayer.bounds[3] - textLayer.bounds[1]).as("cm");
	
	// Text position
	var x= (docWidth - newImageLayerWidth)/2 + newImageLayerWidth - textLayerWidth   // docWidth - 3 - textLayerWidth
	var y= 4 + newImageLayerHeight + 2
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
    jpgOptions.quality = 10; // High quality
	
    var saveFile = new File(savePath);
    doc.saveAs(saveFile, jpgOptions, true, Extension.LOWERCASE);
    
    // Hide the image layers after saving
	// imageLayer.visible = false;
    // textLayer.visible = false;
	
    // Remove the image layers created for this image processing 
	   imageLayer.remove() ;
       textLayer.remove();

    
    // Save the document (we do not save, it is too big)
    // doc.save();
    
    //alert("Image processed and saved successfully!");

}

function isStopChar(mychar, stopChars) {
    for (var i = 0; i < stopChars.length; i++) {
        if (mychar === stopChars[i]) {
            return true;
        }
    }
    return false;
}

// Modified function
function cleanFileName(input) {
    // Convert to lowercase first
    input = input.toLowerCase();
    
    // Split into words
    var words = input.split(' ');
    
    // Capitalize first letter of each word
    for (var i = 0; i < words.length; i++) {
        if (words[i].length > 0) {
            words[i] = words[i].charAt(0).toUpperCase() + words[i].slice(1);
        }
    }
    
    // Join words back together
    var titleCaseString = words.join(' ');
    
    // Find the index of the first special character or digit
    var stopChars = ['0','1','2','3','4','5','6','7','8','9','_','-','(', ','];
    var stopIndex = titleCaseString.length;
    
    for (var j = 0; j < titleCaseString.length; j++) {
        if (isStopChar(titleCaseString.charAt(j), stopChars)) {
            stopIndex = j;
            break;
        }
    }
    
    // Return substring up to the first special character or digit
    return titleCaseString.substring(0, stopIndex);
}

function createTemplate(docName, pageWidth, pageHeight) {
    // Assign the passed parameters to the document dimensions
    var docWidth = pageWidth; // Width in cm
    var docHeight = pageHeight; // Height in cm
    var docResolution = 300; // Resolution in DPI
    var docMode = NewDocumentMode.RGB; // Color mode
    var docDepth = BitsPerChannelType.EIGHT; // 8 bits/channel jgp required
    var docFill = DocumentFill.WHITE; // Fill with white

    // Convert dimensions to pixels
    var widthInPixels = docWidth * (docResolution / 2.54);
    var heightInPixels = docHeight * (docResolution / 2.54);

    // Create the new document
    var backgroundDoc = app.documents.add(
        UnitValue(docWidth, "cm"),
        UnitValue(docHeight, "cm"),
        docResolution,
        docName,
        docMode,
        docFill,
        pixelAspectRatio = 1,
        docDepth,
        colorProfileName = "sRGB IEC61966-2.1"
        
    );

    // Add rulers
    var cmToPixels = docResolution / 2.54; // conversion factor
    backgroundDoc.guides.add(Direction.HORIZONTAL, UnitValue(4 * cmToPixels, "px"));
    backgroundDoc.guides.add(Direction.HORIZONTAL, UnitValue((docHeight - 4) * cmToPixels, "px"));
    backgroundDoc.guides.add(Direction.VERTICAL, UnitValue(2.5 * cmToPixels, "px"));
    backgroundDoc.guides.add(Direction.VERTICAL, UnitValue((docWidth - 2.5) * cmToPixels, "px"));

    return backgroundDoc;
}

function getUserParams() {
    var dialog = new Window("dialog", "Parámetros de impresión");
    dialog.orientation = "column";
    dialog.alignChildren = "left";

    var verticalFrameSizeGroup = dialog.add("group");
    verticalFrameSizeGroup.orientation = "row";
    verticalFrameSizeGroup.alignChildren = "left";
    verticalFrameSizeGroup.add("statictext", undefined, "Alto del marco en cm:");
    var verticalFrameSizeInput = verticalFrameSizeGroup.add("edittext", undefined, "40");
    verticalFrameSizeInput.characters = 10;

    var horizontalFrameSizeGroup = dialog.add("group");
    horizontalFrameSizeGroup.orientation = "row";
    horizontalFrameSizeGroup.alignChildren = "left";
    horizontalFrameSizeGroup.add("statictext", undefined, "Ancho del marco en cm:");
    var horizontalFrameSizeInput = horizontalFrameSizeGroup.add("edittext", undefined, "30");
    horizontalFrameSizeInput.characters = 10;

    dialog.add("statictext", undefined, "Orientación de impresión:");
    var orientationGroup = dialog.add("group");
    orientationGroup.orientation = "row";
    orientationGroup.alignChildren = "left";
    var horizontalRadio = orientationGroup.add("radiobutton", undefined, "Horizontal");
    var verticalRadio = orientationGroup.add("radiobutton", undefined, "Vertical ");
    var bestModeRadio = orientationGroup.add("radiobutton", undefined, "Según imagen");
    bestModeRadio.value = true; // Default selection

    var upperMarginGroup = dialog.add("group");
    upperMarginGroup.orientation = "row";
    upperMarginGroup.alignChildren = "left";
    upperMarginGroup.add("statictext", undefined, "Margen superior (cm):");
    var upperMarginInput = upperMarginGroup.add("edittext", undefined, "4");
    upperMarginInput.characters = 10;

    var leftMarginGroup = dialog.add("group");
    leftMarginGroup.orientation = "row";
    leftMarginGroup.alignChildren = "left";
    leftMarginGroup.add("statictext", undefined, "Margen mínimo a los lados (cm):");
    var leftMarginInput = leftMarginGroup.add("edittext", undefined, "3");
    leftMarginInput.characters = 10;

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
        var horizontalFrameSize = parseFloat(horizontalFrameSizeInput.text);
        var verticalFrameSize = parseFloat(verticalFrameSizeInput.text);
        var upperMargin = parseFloat(upperMarginInput.text);
        var leftMargin = parseFloat(leftMarginInput.text);
        var sourceFolder = sourceFolderInput.text;
        var resultFolder = resultFolderInput.text;

        if (horizontalFrameSize < 10) {
            alert("El ancho del marco debe ser al menos 10 cm.");
            return;
        }
        if (verticalFrameSize < 10) {
            alert("El alto del marco debe ser al menos 10 cm.");
            return;
        }
        if (upperMargin >= (verticalFrameSize / 2 )) {
            alert("El margen superior debe ser menor que la mitad del alto del marco.");
            return;
        }
        if (leftMargin >= horizontalFrameSize / 2) {
            alert("El margen a los lados debe ser menor que la mitad del ancho del marco.");
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
        var orientationValue;
        if (horizontalRadio.value) {
            orientationValue = 'h';
        } else if (verticalRadio.value) {
            orientationValue = 'v';
        } else {
            orientationValue = 'b';
        }

        return {
            orientation: orientationValue,
            horizontalFrameSize: parseFloat(horizontalFrameSizeInput.text),
            verticalFrameSize: parseFloat(verticalFrameSizeInput.text),
            upperMargin: parseFloat(upperMarginInput.text),
            leftMargin: parseFloat(leftMarginInput.text),
            sourceFolder: sourceFolderInput.text,
            resultFolder: resultFolderInput.text
        };
    } else {
        return null;
    }
}

function main() {

    userParams = getUserParams();
    if (!userParams) {
        return;
    }
    
    verticalDoc = createTemplate("Vertical", userParams.horizontalFrameSize, userParams.verticalFrameSize); // Example dimensions: 30 cm width, 40 cm height
    horizontalDoc = createTemplate("Horizontal", userParams.verticalFrameSize, userParams.horizontalFrameSize);
    //horizontalDoc.saveAs(new File("C:\\Temp\\Horizontal.psd"));
    //verticalDoc.saveAs(new File("C:\\Temp\\Vertical.psd"));

    // Set the verticalDoc as the active document
    //app.activeDocument = horizontalDoc;

    // Use userParams.sourceFolder and userParams.resultFolder instead of prompting the user
    var sourceFolder = new Folder(userParams.sourceFolder);
    if (!sourceFolder.exists) {
        alert("Source folder does not exist. Script cancelled.");
        return;
    }

    var destination = new Folder(userParams.resultFolder);
    if (!destination.exists) {
        alert("Result folder does not exist. Script cancelled.");
        return;
    }

    var destFolderStr = destination.fsName.replace(/\\/g, "\\\\") + "\\\\";
    var destFolder = new Folder(destFolderStr);

    // Get all JPG files in the selected folder
    var jpgFiles = sourceFolder.getFiles("*.jpg");
    if (jpgFiles.length == 0) {
        alert("No JPG files found in the selected folder.");
        return;
    }

    for (var i = 0; i < jpgFiles.length; i++) {
        var imagePath = jpgFiles[i].fsName;
        var destFilePathStr = destFolderStr + File.encode(decodeURI(jpgFiles[i].name), "Windows-1252");
        loadImageAsimageLayer(jpgFiles[i], destFilePathStr);
        // Display a progress message
        var progressMessage = "Processing file: " + decodeURI(new File(imagePath).name);
        $.writeln(progressMessage); // Log progress to the console 
        //alert(progressMessage); 
    }


    horizontalDoc.close(SaveOptions.DONOTSAVECHANGES);
    verticalDoc.close(SaveOptions.DONOTSAVECHANGES);

    alert("Image processing finished successfully!");
}



// Run the main function
main();

// End of script
