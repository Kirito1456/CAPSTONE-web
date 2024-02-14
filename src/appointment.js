// This is the pop up sa rescheduling appointment
var detailsLink = document.getElementById('details-link');

// Add a click event listener to toggle details
detailsLink.addEventListener('click', function(event) {
    event.preventDefault(); // Prevent default link behavior
    var detailsContainer = document.querySelector('.details-container');
    detailsContainer.style.display = detailsContainer.style.display === 'none' ? 'block' : 'none';
});


var modal = document.getElementById("myModal");
var btn = document.querySelector(".reschedule-button");
var span = document.getElementsByClassName("close")[0];

// When the user clicks on the button, open the modal
btn.onclick = function() {
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
    var cancelButton = document.querySelector('.cancel-button');
    
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

     // Event listener for cancel button click
     cancelButton.addEventListener('click', function() {
        // Ask for confirmation
        var confirmCancel = confirm('Are you sure you want to cancel this appointment?');
        if (confirmCancel) {
            // If confirmed, close the modal
            modal.style.display = 'none';
        }
    });

});

window.onload = generateTimeOptions;
