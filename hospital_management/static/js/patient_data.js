function toggleDropdown() {
    var dropdown = document.getElementById("diagnosisDropdown");
    if (dropdown.style.display === "none") {
        dropdown.style.display = "block";
    } else {
        dropdown.style.display = "none";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const backButton = document.getElementById('backButton');
    const dropdown = document.getElementById("diagnosisDropdown");
    var healthConditions = document.getElementById("health-conditions");
    var otherDiagnosis = document.getElementById("otherDiagnosis");

    healthConditions.addEventListener("change", function() {
        if (this.value === "Others") {
            otherDiagnosis.style.display = "block";
        } else {
            otherDiagnosis.style.display = "none";
        }
    });

    backButton.addEventListener('click', function() {
        window.history.back();
    });

    var toggleSwitch = document.getElementById("patientTypeToggle");
    var patientStatus = toggleSwitch.checked ? "Inpatient" : "Outpatient";
    toggleSections(patientStatus);

    // Add event listener to toggle patient type
    toggleSwitch.addEventListener('change', function() {
        togglePatientType();
        updateEndTransactionButton();
    });

    // Update the "End Transaction" button initially
    updateEndTransactionButton();

    // Add event listener to Cancel button
    var cancelButton = document.getElementById("cancelButton");
    cancelButton.addEventListener('click', function() {
        toggleChiefComplaint();
    });

});

function toggleContactInfo() {
    var contactDetails = document.getElementById("contact-details");
    if (contactDetails.style.display === "none") {
        contactDetails.style.display = "block";
    } else {
        contactDetails.style.display = "none";
    }
}

function toggleBiometricInfo() {
    var biometricInfo = document.getElementById("biometric-info");
    if (biometricInfo.style.display === "none") {
        biometricInfo.style.display = "block";
    } else {
        biometricInfo.style.display = "none";
    }
}

// Add event listeners for the Chief Complaint button
var chiefComplaintButton = document.getElementById("chiefComplaintButton");
var chiefComplaintArea = document.getElementById("chiefComplaintArea");
var saveChiefComplaintButton = document.getElementById("saveChiefComplaintButton");
var cancelChiefComplaintButton = document.getElementById("cancelChiefComplaintButton");

chiefComplaintButton.addEventListener('click', function() {
    toggleChiefComplaint();
});

saveChiefComplaintButton.addEventListener('click', function() {
    saveChiefComplaint();
});

cancelChiefComplaintButton.addEventListener('click', function() {
    toggleChiefComplaint();
});

// Add event listeners for the Diagnosis button
var diagnosisButton = document.getElementById("diagnosisButton");
var diagnosisArea = document.getElementById("diagnosisArea");
var saveDiagnosisButton = document.getElementById("saveDiagnosisButton");
var cancelDiagnosisButton = document.getElementById("cancelDiagnosisButton");

diagnosisButton.addEventListener('click', function() {
    toggleDiagnosis();
});

saveDiagnosisButton.addEventListener('click', function() {
    saveDiagnosis();
});

cancelDiagnosisButton.addEventListener('click', function() {
    toggleDiagnosis();
});

// Function to toggle the visibility of the Chief Complaint area
function toggleChiefComplaint() {
    if (chiefComplaintArea.style.display === "none") {
        chiefComplaintArea.style.display = "block";
    } else {
        chiefComplaintArea.style.display = "none";
    }
}

// Function to toggle the visibility of the Diagnosis area
function toggleDiagnosis() {
    if (diagnosisArea.style.display === "none") {
        diagnosisArea.style.display = "block";
    } else {
        diagnosisArea.style.display = "none";
    }
}

function toggleSections(status) {
    var consultationNotesContainer = document.getElementById("consultation-notes-container");
    var diagnosticsContainer = document.getElementById("diagnostic-tests-container");
    var progressNotesContainer = document.getElementById("progress-notes-container");
    var vitalSignContainer = document.getElementById("vital-signs-container");
    var patientInfo = document.getElementById("patient-info");

    if (status === "Inpatient") {
        patientInfo.style.display = "block";
        consultationNotesContainer.style.display = "block";
        diagnosticsContainer.style.display = "block";
        vitalSignContainer.style.display = "block";
        progressNotesContainer.style.display = "block";
    } else {
        consultationNotesContainer.style.display = "block";
        diagnosticsContainer.style.display = "block";
        patientInfo.style.display = "block";
        vitalSignContainer.style.display = "none";
        progressNotesContainer.style.display = "none";
    }
}

function togglePatientType() {
    var toggleSwitch = document.getElementById("patientTypeToggle");
    var label = document.querySelector('.toggle-switch label');

    // Toggle the status between "Inpatient" and "Outpatient"
    label.textContent = (label.textContent === "Inpatient") ? "Outpatient" : "Inpatient";
    
    // Get the updated patient status
    var patientStatus = toggleSwitch.checked ? "Inpatient" : "Outpatient";
    
    // Toggle the visibility of sections based on the updated status
    toggleSections(patientStatus);
}

function updateEndTransactionButton() {
    var endTransactionButton = document.getElementById("endtransaction");
    var toggleSwitch = document.getElementById("patientTypeToggle");
    var patientStatus = toggleSwitch.checked ? "Inpatient" : "Outpatient";

    // Update button text based on patient status
    if (patientStatus === "Inpatient") {
        endTransactionButton.textContent = "Discharge";
    } else {
        endTransactionButton.textContent = "Appointment Finished";
    }
}
// function toggleDropdown() {

//     if (dropdown.style.display === "none") {
//         dropdown.style.display = "block";
//     } else {
//         dropdown.style.display = "none";

//     }

// }

