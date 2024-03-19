
        immunizationLink.addEventListener('click', function(event) {
            event.preventDefault();
            contentContainer.innerHTML = `
            <form method="post">
            {% csrf_token %}
            <div id="immunization-table">
                <div class="row header">
                    <div class="cell vaccine">Vaccine</div>
                    <div class="cell date">Date</div>
                </div>
                <div class="row">
                    <div class="cell vaccine" name="vaccine"></div>
                    <div class="cell date">
                        <input type="date" name="date">
                    </div>
                    
                </div>
            </div>
            <div id="edit-immunization">
                <button id="edit-immunization-button">Edit</button>
                <button id="save-immunization-button" name="saveImmunizationButton" value={{ chosenPatientData_id }}>Save</button>
                <button id="cancel-immunization-button" style="display: none;">Cancel</button>
                <button id="add-new-immunization-button">Add New Row</button>
            </div>            
        </form>`;

            // Add event listeners
            const editImmunizationButton = document.getElementById('edit-immunization-button');
            const cancelImmunizationButton = document.getElementById('cancel-immunization-button');
            const addNewImmunizationButton = document.getElementById('add-new-immunization-button');

            addNewImmunizationButton.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent form submission
                            
                const newRow = document.createElement('div');
                newRow.classList.add('row');
                        
                newRow.innerHTML = `
                    <div class="cell vaccine"></div>
                    <div class="cell date">
                        <input type="date" name="date">
                    </div>`;
                        
                const immunizationTable = document.getElementById('immunization-table');
                immunizationTable.appendChild(newRow);
            });
            
            editImmunizationButton.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent form submission
                
                // Show the Cancel button
                cancelImmunizationButton.style.display = 'inline-block';
                
                // Get all rows excluding the header row
                const rows = document.querySelectorAll('.row:not(.header)');
                
                // Iterate over each row
                rows.forEach(row => {
                    // Get the vaccine cell of the row
                    const vaccineCell = row.querySelector('.cell.vaccine');
                    
                    // Replace text content with input box
                    vaccineCell.innerHTML = '<input type="text" name="vaccine">';
                    
                    // Get the date cell of the row
                    const dateCell = row.querySelector('.cell.date');
                    
                    // Replace text content with date input
                    dateCell.innerHTML = '<input type="date" name="date">';
                });
            });
            
            
            cancelImmunizationButton.addEventListener('click', function() {
                // Hide the Cancel button
                cancelImmunizationButton.style.display = 'none';
                        
                // Get all rows excluding the header row
                const rows = document.querySelectorAll('.row:not(.header)');
                        
                // Iterate over each row
                rows.forEach(row => {
                    // Restore original content
                    row.querySelector('.cell.vaccine').innerHTML = '';
                    row.querySelector('.cell.date').innerHTML = '';
                });
            });
        });
