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
    
});