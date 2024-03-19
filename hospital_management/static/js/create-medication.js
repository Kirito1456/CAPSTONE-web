function selectAllCheckboxes() {
    var checkboxes = document.getElementsByClassName("remove-checkbox");
    var selectAllCheckbox = document.getElementById("select-all-checkbox");
    for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = selectAllCheckbox.checked;
    }
}


// Event listener for input field
document.getElementById('medicine_name_input').addEventListener('input', function() {
    var query = this.value;
    var suggestions = Array.from(document.getElementById('medicine_name_suggestions').options)
        .map(option => option.value)
        .filter(medicine => medicine.toLowerCase().includes(query.toLowerCase()));

    displayAutocompleteSuggestions(suggestions);
});

// Function to display autocomplete suggestions
function displayAutocompleteSuggestions(suggestions) {
    var dropdown = document.getElementById('medicine_name_suggestions');
    dropdown.innerHTML = ''; // Clear previous suggestions

    suggestions.forEach(function(suggestion) {
        var option = document.createElement('option');
        option.value = suggestion;
        dropdown.appendChild(option);
    });
}

var modal = document.getElementById("myModal");
var span = document.getElementsByClassName("close")[0];

modal.style.display = "none";

function openModal() {
    modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    var birthdayString = document.getElementById("birthday-view").innerText;
    var birthday = new Date(birthdayString);
    var today = new Date();
    var ageYear = today.getFullYear() - birthday.getFullYear();
    var ageMonth = today.getMonth() - birthday.getMonth();
    var modal = document.getElementById('myModal');

    document.getElementById("fname").addEventListener("change", function() {
        var selectedOption = this.options[this.selectedIndex];
        var birthdayString = selectedOption.getAttribute("data-birthday");
        var gender = selectedOption.getAttribute("data-gender");
        var birthday = new Date(birthdayString);
        var today = new Date();
        var ageYear = today.getFullYear() - birthday.getFullYear();
        var ageMonth = today.getMonth() - birthday.getMonth();

        if (ageMonth < 0 || (ageMonth === 0 && today.getDate() < birthday.getDate())) {
            ageYear--;
            ageMonth += 12;
        }

        document.getElementById("age-view").innerText = ageYear + " years and " + ageMonth + " months";

        updatePatientInfo(birthdayString, gender);
    });


    function updatePatientInfo(birthday, gender) {
        document.getElementById("birthday-view").innerText = birthday;
        document.getElementById("gender-view").innerText = gender;
    }

    var todayDate = today.toISOString().split('T')[0];
    document.getElementById("today-view").innerText = todayDate;
    var txt = document.getElementById("todayinput");
    txt.value = todayDate;

    document.getElementById("select-all-checkbox").addEventListener("change", function() {
        selectAllCheckboxes();
    });

    document.getElementById("add-medication-button").addEventListener("click", function(event) {
        event.preventDefault(); // Prevent default behavior of the link
        var medicationListContainer = document.getElementById("medication-list-container");
        var newTableBody = document.createElement("div");
        newTableBody.id = "table-body";
        newTableBody.innerHTML = `
            <div style="flex: 1; text-align: center;"><input type="checkbox" class="remove-checkbox"></div>
            <div style="flex: 1; text-align: center;">
                <input type="text" name="medicine_name" id="medicine_name_input" placeholder="Enter Medicine Name" list="medicine_name_suggestions">
                
            </div>
            
            <div style="flex: 1; text-align: center;"><input type="text" class="dosage-input" placeholder="Dosage" name="dosage"></div>
            <div style="flex: 1; text-align: center;">
                <select class="route-dropdown" name="route">
                    <option value="" selected disabled>Select Route</option>
                    <option value="Oral">Oral</option>
                    <option value="Injection">Injection</option>
                    <option value="Topical">Topical</option>
                </select>
            </div>
            <div style="flex: 1; text-align: center;">
                <select class="frequency-dropdown" name="frequency">
                    <option value="" selected disabled>Select Frequency</option>
                    <option value="Once Daily">Once Daily</option>
                    <option value="Twice Daily">Twice Daily</option>
                    <option value="Thrice Daily">Thrice Daily</option>
                </select>
            </div>
            <div style="flex: 1; text-align: center;"><input type="text" class="remarks-input" placeholder="Additional Remarks" name="additionalremarks"></div>
        `;
        medicationListContainer.appendChild(newTableBody);
    });
    

    document.getElementById("remove-medication-button").addEventListener("click", function(event) {
        event.preventDefault(); // Prevent default behavior of the link
        var medicationListContainer = document.getElementById("medication-list-container");
        var tableBodies = medicationListContainer.querySelectorAll("#table-body");
    
        tableBodies.forEach(function(tableBody) {
            if (tableBody.querySelector(".remove-checkbox").checked) {
                medicationListContainer.removeChild(tableBody);
            }
        });
    });
    
});