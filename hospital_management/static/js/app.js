const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const clients_table = document.querySelector('.clients_table tbody');
const appointmentForm = document.getElementById("appointment-form");

// Event listener for the search button click
searchButton.addEventListener('click', function() {
    // Get the search text entered by the user and convert it to lowercase
    const searchText = searchInput.value.toLowerCase();
    // Get all the rows in the accounts table
    const rows = clients_table.querySelectorAll('tr');

    // Loop through each row
    rows.forEach(function(row) {
        // Get all the columns in the current row
        const columns = row.querySelectorAll('td');
        let found = false;

        // Loop through each column in the current row
        columns.forEach(function(column) {
            // Check if the column text contains the search text
            if (column.textContent.toLowerCase().includes(searchText)) {
                found = true; // Set found flag to true if search text is found
            }
        });

        // Display or hide the row based on whether the search text was found
        if (found) {
            row.style.display = ''; // Show the row
        } else {
            row.style.display = 'none'; // Hide the row
        }
    });
});


// Get all details links
var detailsLinks = document.querySelectorAll('.details-link');

// Add click event listener to each details link
detailsLinks.forEach(function(detailsLink) {
    detailsLink.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent default link behavior
        var detailsContainer = this.parentElement.nextElementSibling; // Get the details container of the clicked link
        detailsContainer.style.display = detailsContainer.style.display === 'none' ? 'block' : 'none'; // Toggle display
    });
});

var modal = document.getElementById("myModal");
var span = document.getElementsByClassName("close")[0];

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


// Function to add leading zeroes if necessary
function padZero(num) {
    return num < 10 ? '0' + num : num.toString();
}

// This is sa pagpapakita ng time options for every 30-minute interval between 9 am and 5 pm
function generateTimeOptions() {
    const selectElement = document.getElementById('new-appointment-time');
    for (let hour = 9; hour <= 16; hour++) {
        for (let minutes = 0; minutes < 60; minutes += 30) {
            const hourStr = padZero(hour);
            const minutesStr = padZero(minutes);
            const meridiem = hour < 12 ? 'AM' : 'PM';
            const displayHour = hour > 12 ? hour - 12 : hour;
            selectElement.innerHTML += `<option value="${hourStr}:${minutesStr}">${displayHour}:${minutesStr} ${meridiem}</option>`;
        }
    }
}

// This is sa rescheduling appointment. Selecting new date and selecting new time
document.addEventListener('DOMContentLoaded', function() {
    var dateInput = document.getElementById('new-appointment-date');
    var timeSelect = document.getElementById('new-appointment-time');
    var modal = document.getElementById('myModal');
    var cancelButton = document.querySelectorAll('.cancel-button');
    
    
    var today = new Date().toISOString().split('T')[0];
    dateInput.min = today;


    // Function to check if a given date is a weekend
    function isWeekend(date) {
        var day = date.getDay();
        return day === 0 || day === 6; // 0 for Sunday, 6 for Saturday
    }

    // Disable weekends in the date input field
    dateInput.addEventListener('input', function() {
        var selectedDate = new Date(this.value);
        if (isWeekend(selectedDate)) {
            // If selected date is a weekend, clear the input value
            this.value = '';
        }
    });

    cancelButton.forEach(function(cancelButton) {
        cancelButton.addEventListener('click', function() {
        // Ask for confirmation
        var confirmCancel = confirm('Are you sure you want to cancel this appointment?');
        if (confirmCancel) {
            // If confirmed, close the modal
            modal.style.display = 'none';
        }
        });
    });
});

window.onload = generateTimeOptions;

