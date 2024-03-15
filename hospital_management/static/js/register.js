document.addEventListener("DOMContentLoaded", function() {
    // Get the select elements
    const roleSelect = document.getElementById('roleSelect');
    const jobTitleSelect = document.getElementById('jobTitleSelect');
    var clinicSelect = document.getElementById("doctorClinic");
    var clinicSelect = document.getElementById("clinicSelect");
    var othersFields = document.getElementById("othersFields");
    
    // Define the job titles for each role
    const doctorJobTitles = ['General Practitioner', 'Dermatologist', 'Pediatrician'];
    const nurseJobTitles = ['Head Nurse', 'Bedside Nurse'];

    // Function to update job titles based on selected role
    function updateJobTitles() {
        const selectedRole = roleSelect.value;
        jobTitleSelect.innerHTML = ''; // Clear existing options
        
        // Show placeholder option if selected role is empty
        if (!selectedRole) {
            const placeholderOption = document.createElement('option');
            placeholderOption.value = '';
            placeholderOption.textContent = '- Select Role First -';
            jobTitleSelect.appendChild(placeholderOption);
        } else {
            // If role is selected, populate job titles accordingly
            const jobTitles = selectedRole === 'Doctor' ? doctorJobTitles : nurseJobTitles;
            jobTitles.forEach(jobTitle => {
                const option = document.createElement('option');
                option.value = jobTitle;
                option.textContent = jobTitle;
                jobTitleSelect.appendChild(option);
            });
        }
        if (this.value === "Doctor") {
            doctorClinic.style.display = "block";
        } else {
            doctorClinic.style.display = "none";
            othersFields.style.display = "none";
        }

    }

    // Event listener for role selection change
    roleSelect.addEventListener('change', updateJobTitles);

    // Initialize job titles based on default role selection
    updateJobTitles();

    
    clinicSelect.addEventListener("change", function() {
        if (this.value === "Others") {
            othersFields.style.display = "block";
        } else {
            othersFields.style.display = "none";
        }
    });
});
