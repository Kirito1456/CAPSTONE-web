document.addEventListener("DOMContentLoaded", function() {
    var birthdayString = document.getElementById("birthday-view").innerText;
    var birthday = new Date(birthdayString);
    var today = new Date();
    var ageYear = today.getFullYear() - birthday.getFullYear();
    var ageMonth = today.getMonth() - birthday.getMonth();

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
            <div style="flex: 1; text-align: center;"><input type="text" placeholder="Medicine Name"></div>
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

function selectAllCheckboxes() {
    var checkboxes = document.getElementsByClassName("remove-checkbox");
    var selectAllCheckbox = document.getElementById("select-all-checkbox");
    for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = selectAllCheckbox.checked;
    }
}
