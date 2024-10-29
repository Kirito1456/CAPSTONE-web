const daysTag = document.querySelector(".days");
const currentDate = document.querySelector(".current-date");
const prevNextIcon = document.querySelectorAll(".icons span");

// Initialize date, current year, and month variables
let date = new Date();
let currYear = date.getFullYear();
let currMonth = date.getMonth();

// Array of full month names
const months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"];

// Function to render the calendar
const renderCalendar = () => {
    const firstDayOfMonth = new Date(currYear, currMonth, 1).getDay();
    const lastDateOfMonth = new Date(currYear, currMonth + 1, 0).getDate();
    const lastDayOfMonth = new Date(currYear, currMonth, lastDateOfMonth).getDay();
    const lastDateOfLastMonth = new Date(currYear, currMonth, 0).getDate();
    let liTag = "";

    // Create li elements for the days of the previous month
    for (let i = firstDayOfMonth; i > 0; i--) {
        liTag += `<li class="inactive">${lastDateOfLastMonth - i + 1}</li>`;
    }

    // Create li elements for the days of the current month
    for (let i = 1; i <= lastDateOfMonth; i++) {
        // Add active class if the day is today
        let isToday = i === date.getDate() && currMonth === date.getMonth() && currYear === date.getFullYear() ? "active" : "";
        liTag += `<li class="${isToday}">${i}</li>`;
    }

    // Create li elements for the days of the next month
    for (let i = lastDayOfMonth; i < 6; i++) {
        liTag += `<li class="inactive">${i - lastDayOfMonth + 1}</li>`;
    }
    
    // Update the current date text to display the selected date
    currentDate.innerText = `${months[currMonth]} ${currYear}`;
    
    // Update the HTML content of the days tag
    daysTag.innerHTML = liTag;
}

// Call renderCalendar to initially render the calendar
renderCalendar();

// Add event listeners to previous and next icons for navigation
prevNextIcon.forEach(icon => {
    icon.addEventListener("click", () => {
        // Update current month based on the clicked icon
        currMonth = icon.id === "prev" ? currMonth - 1 : currMonth + 1;

        // Check if the current month is out of bounds
        if (currMonth < 0 || currMonth > 11) {
            // Update date and current month and year accordingly
            date = new Date(currYear, currMonth, date.getDate());
            currYear = date.getFullYear();
            currMonth = date.getMonth();
        } else {
            // Reset date to current date
            date = new Date();
        }
        
        // Render the calendar with the updated month
        renderCalendar();
    });
});

// Get the modal element
var modal = document.getElementById("apt-requests-modal");

// Get the <div> element that triggers the modal
var divTrigger = document.getElementById("apt_schedule-booked");

// When the user clicks the <div>, open the modal
divTrigger.addEventListener('click', function() {
  modal.style.display = "block";
});

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

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
