// Wait for the DOM content to be fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Get references to the search input, search button, and accounts table
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const accountsTable = document.querySelector('.accounts_table tbody');

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
});
