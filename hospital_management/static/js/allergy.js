document.addEventListener("DOMContentLoaded", function() {
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', function() {
        window.history.back();
    });
});

function edit(button) {
    // Find the parent row of the clicked button
    var rowIndex = button.parentNode.parentNode.rowIndex;

    // Get the div elements
    var allergenElement = document.getElementById("allergen-text-" + rowIndex);
    var severityElement = document.getElementById("severity-text-" + rowIndex);

    // Get the input elements
    var allergenInput = document.getElementById("allergen-input-" + rowIndex);
    var severityInput = document.getElementById("severity-input-" + rowIndex);

    // Update the text content of the div elements with the input field values
    allergenInput.value = allergenElement.textContent;
    severityInput.value = severityElement.textContent;

    // Display the input fields and hide the div elements
    allergenInput.style.display = "block";
    allergenElement.style.display = "none";

    severityInput.style.display = "block";
    severityElement.style.display = "none";
}

function save(button) {
    // Find the parent row of the clicked button
    var rowIndex = button.parentNode.parentNode.rowIndex;

    // Get the div elements
    var allergenElement = document.getElementById("allergen-text-" + rowIndex);
    var severityElement = document.getElementById("severity-text-" + rowIndex);

    // Get the input elements
    var allergenInput = document.getElementById("allergen-input-" + rowIndex);
    var severityInput = document.getElementById("severity-input-" + rowIndex);

    // Update the text content of the div elements with the input field values
    allergenElement.textContent = allergenInput.value;
    severityElement.textContent = severityInput.value;

    // Hide the input fields and show the div elements
    allergenInput.style.display = "none";
    allergenElement.style.display = "block";

    severityInput.style.display = "none";
    severityElement.style.display = "block";

    // Show the edit button and hide the save button
    document.getElementById("edit-" + rowIndex).style.display = "inline";
    document.getElementById("save-" + rowIndex).style.display = "none";
}

function add() {
    // Retrieve reference to the table
    var table = document.getElementById("allergies-table");

    // Create a new row element
    var newRow = document.createElement("tr");

    // Create cells for allergen and severity
    var allergenCell = document.createElement("td");
    var severityCell = document.createElement("td");

    // Set content for allergen cell
    var allergenContent = document.createElement("div");
    var allergenInput = document.createElement("select");
    allergenInput.className = "allergenSelect";
    allergenInput.innerHTML = document.querySelector('.allergenSelect').innerHTML;
    allergenInput.selectedIndex = 0; // Set initial value of dropdown
    allergenInput.id = "allergen-input-" + (table.rows.length);
    allergenContent.style.display = "none"; // Initially hidden
    allergenContent.id = "allergen-text-" + (table.rows.length);
    allergenCell.appendChild(allergenContent);
    allergenCell.appendChild(allergenInput);

    // Set content for severity cell
    var severityContent = document.createElement("div");
    var severityInput = document.createElement("select");
    severityInput.className = "severitySelect";
    severityInput.innerHTML = document.querySelector('.severitySelect').innerHTML;
    severityInput.selectedIndex = 0; // Set initial value of dropdown
    severityInput.id = "severity-input-" + (table.rows.length);
    severityContent.style.display = "none"; // Initially hidden
    severityContent.id = "severity-text-" + (table.rows.length);
    severityCell.appendChild(severityContent);
    severityCell.appendChild(severityInput);

    // Append cells to row
    newRow.appendChild(allergenCell);
    newRow.appendChild(severityCell);

    // Append row to table
    table.appendChild(newRow);
}

function save_new_row(button) {
    // Find the parent row of the clicked button
    var rowIndex = button.parentNode.parentNode.rowIndex;

    // Get the div elements
    var allergenElement = document.getElementById("allergen-text-" + rowIndex);
    var severityElement = document.getElementById("severity-text-" + rowIndex);

    // Get the input elements
    var allergenInput = document.getElementById("allergen-input-" + rowIndex);
    var severityInput = document.getElementById("severity-input-" + rowIndex);

    // Update the text content of the div elements with the input field values
    allergenElement.textContent = allergenInput.options[allergenInput.selectedIndex].text;
    severityElement.textContent = severityInput.options[severityInput.selectedIndex].text;

    // Hide the input fields and show the div elements
    allergenInput.style.display = "none";
    allergenElement.style.display = "block";

    severityInput.style.display = "none";
    severityElement.style.display = "block";

    // Show the edit button and hide the save button
    document.getElementById("edit-" + rowIndex).style.display = "inline";
    document.getElementById("save-" + rowIndex).style.display = "none";
}

function updateAllergen(select) {
    var allergenText = select.options[select.selectedIndex].text;
    var allergenInput = document.getElementById("allergen-input-" + select.parentNode.parentNode.rowIndex);
    allergenInput.value = allergenText;
}

function updateSeverity(select) {
    var severityText = select.options[select.selectedIndex].text;
    var severityInput = document.getElementById("severity-input-" + select.parentNode.parentNode.rowIndex);
    severityInput.value = severityText;
}