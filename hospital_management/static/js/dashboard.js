document.addEventListener("DOMContentLoaded", function() {
    // Get references to the search input, search button, accounts table, and pagination buttons
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const accountsTable = document.querySelector('.accounts_table tbody');
    const doctorsButton = document.getElementById('doctorsButton');
    const nursesButton = document.getElementById('nursesButton');
    const allButton = document.getElementById('allButton');
    const previousButton = document.querySelector('.previous'); // Initialize previous button
    const nextButton = document.querySelector('.next'); // Initialize next button

    // Event listener for the search button click
    searchButton.addEventListener('click', function() {
        // Get the search text entered by the user and convert it to lowercase
        const searchText = searchInput.value.toLowerCase();
        // Get all the rows in the accounts table
        const rows = accountsTable.querySelectorAll('tr');

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

    // Event listener for previous button click
    previousButton.addEventListener('click', function() {
        window.history.back();
    });

    // Event listener for next button click
    nextButton.addEventListener('click', function() {
        window.history.forward();
    });

    // Event listener for doctors button click
    doctorsButton.addEventListener('click', function() {
        // Show only doctors' accounts
        document.querySelectorAll('.accounts_table tbody tr').forEach(function(row) {
            const role = row.querySelector('#accountT_role').textContent;
            if (role !== 'Doctor') {
                row.style.display = 'none';
            } else {
                row.style.display = '';
            }
        });
    });

    // Event listener for nurses button click
    nursesButton.addEventListener('click', function() {
        // Show only nurses' accounts
        document.querySelectorAll('.accounts_table tbody tr').forEach(function(row) {
            const role = row.querySelector('#accountT_role').textContent;
            if (role !== 'Nurse') {
                row.style.display = 'none';
            } else {
                row.style.display = '';
            }
        });
    });

    allButton.addEventListener('click', function() {
        // Show only all accounts
        document.querySelectorAll('.accounts_table tbody tr').forEach(function(row) {
            const role = row.querySelector('#accountT_role').textContent;
            row.style.display = '';
        });
    });
});
