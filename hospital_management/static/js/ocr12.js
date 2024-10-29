// Fetch the CSRF token from the cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Check if the cookie name matches the desired name
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Display selected filename and show remove and upload buttons
function displayFileName(input) {
    const selectedFile = document.getElementById('selected-file');
    const removeButton = document.getElementById('remove-button');
    const uploadButton = document.getElementById('upload-button');
    if (input.files.length > 0) {
        selectedFile.textContent = input.files[0].name;
        removeButton.style.display = 'inline-block';
        uploadButton.style.display = 'inline-block';
    } else {
        selectedFile.textContent = '';
        removeButton.style.display = 'none';
        uploadButton.style.display = 'none';
    }
}

// Remove selected file
function removeFile() {
    const fileInput = document.getElementById('file-input');
    fileInput.value = ''; 
    const selectedFile = document.getElementById('selected-file');
    selectedFile.textContent = ''; 
    const removeButton = document.getElementById('remove-button');
    removeButton.style.display = 'none'; 
    const uploadButton = document.getElementById('upload-button');
    uploadButton.style.display = 'none'; 
}

// Event listener for upload button
document.getElementById('upload-button').addEventListener('click', function(event) {
    event.preventDefault();
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (file) {
        performOCR(file);
    } else {
        alert('Please select a file to upload.');
    }
});

function performOCR(file) {
    const formData = new FormData();
    formData.append('image', file);

    fetch('/perform_ocr/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrftoken
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to perform OCR');
        }
        return response.text();
    })
    .then(text => {
        console.log('OCR result:', text);
        // Extract medicine names (Alprazolam and Lorazepam)
        const medicineNames = extractSpecificMedicineNames(text);
        const dosages = extractDosages(text);
        const routes = extractRoute(text);
        const frequencies = extractFrequency(text);
        const days = extractNumberOfDays(text);
        // Display extracted medicine names in a div
        document.getElementById('ocrResult').textContent = 'Medicine names: ' + medicineNames.join(', ');
        document.getElementById('dosages').textContent = 'Dosages: ' + dosages.join(', ');
        document.getElementById('routes').textContent = 'Routes: ' + routes.join(', ');
        document.getElementById('frequencies').textContent = 'Frequencies: ' + frequencies.join(', ');
        document.getElementById('days').textContent = 'Days: ' + days.join(', ');
    })
    
    
    .catch(error => {
        console.error('Error performing OCR:', error);
        alert('Failed to perform OCR. Please try again.');
    });
}

// Function to extract specific medicine names (Alprazolam and Lorazepam) from the OCR result
// const fuzz = require('fuzzball');

function extractSpecificMedicineNames(text) {
    const medicineNames = [];
    // Search for medicines in the OCR result
    if (text.includes('Alprazolam')) {
        medicineNames.push('Alprazolam');
    }
    if (text.includes('Lorazepam')) {
        medicineNames.push('Lorazepam');
    }
    if (text.includes('Amoxicillin')) {
        medicineNames.push('Amoxicillin');
    }
    if (text.includes('Colace')) {
        medicineNames.push('Colace');
    }
    if (text.includes('Rosuvastatin')) {
        medicineNames.push('Rosuvastatin');
    }
    if (text.includes('Atorvastatin')) {
        medicineNames.push('Atorvastatin');
    }
    if (text.includes('Cefoxitin sodium')) {
        medicineNames.push('Cefoxitin sodium');
    }
    if (text.includes('Prednisolone')) {
        medicineNames.push('Prednisolone');
    }
    if (text.includes('HCTZ')) {
        medicineNames.push('HCTZ');
    }
    if (text.includes('Metformin')) {
        medicineNames.push('Metformin');
    }
    if (text.includes('Glipizide')) {
        medicineNames.push('Glipizide');
    }
    if (text.includes('Diclofenac')) {
        medicineNames.push('Diclofenac');
    }
    if (text.includes('Paracetamol')) {
        medicineNames.push('Paracetamol');
    }
    if (text.includes('Loratadine')) {
        medicineNames.push('Loratadine');
    }
    if (text.includes('Hydroxyzine')) {
        medicineNames.push('Hydroxyzine');
    }
    return medicineNames;
}


function extractDosages(text) {
    const dosages = [];
    // Example regex pattern to match numerical values followed by "mg"
    const regex = /\b(\d+(?:\.\d+)?) mg\b/g;
    let match;
    while ((match = regex.exec(text)) !== null) {
        dosages.push(match[0]);
    }
    return dosages;
}

function extractRoute(text) {
    const routes = [];
    const routeKeywords = ['Oral', 'Topical', 'Injection'];
    for (const keyword of routeKeywords) {
        if (text.includes(keyword)) {
            routes.push(keyword);
        }
    }
    return routes;
}

function extractFrequency(text) {
    const frequencies = [];
    const frequencyKeywords = ['Morning', 'Afternoon', 'Evening'];
    for (const keyword of frequencyKeywords) {
        if (text.includes(keyword)) {
            frequencies.push(keyword);
        }
    }
    return frequencies;
}

function extractNumberOfDays(text) {
    const days = [];
    const regex = /\b(\d+) days?\b/g; // Match numerical values followed by "days" or "day"
    let match;
    while ((match = regex.exec(text)) !== null) {
        days.push(match[1]); // Extract the numerical value only
    }
    return days;
}
