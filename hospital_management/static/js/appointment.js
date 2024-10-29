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

function openModal(appointmentId) {
    
    modal.style.display = "block";
    var appIDInput = document.getElementById('appID');
    appIDInput.value = appointmentId;
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

// This is sa rescheduling appointment. Selecting new date and selecting new time
document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('myModal');
    var cancelButton = document.querySelectorAll('.cancel-button');

    cancelButton.forEach(function(cancelButton) {
        cancelButton.addEventListener('click', function() {
        var confirmCancel = confirm('Are you sure you want to cancel this appointment?');
        if (confirmCancel) {
            modal.style.display = 'none';
        }
        });
    });

    
});
