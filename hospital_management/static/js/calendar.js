document.addEventListener("DOMContentLoaded", function() {
  var dateOfTask = "";
  var taskDetails = "";

  // Tasks item box
  task.forEach(item => {
    var hdate = item.hdate;
    var taskitem = item.task;
    dateOfTask += hdate + "<br>";
    taskDetails += taskitem + "<br>";
  });

  const calendar = document.querySelector("#calendar");
  const monthBanner = document.querySelector("#month");
  let navigation = 0;
  let events = localStorage.getItem("events") ? JSON.parse(localStorage.getItem("events")) : [];
  const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  // Loads the calendar itself and the tasks
  function loadCalendar() {
    const dt = new Date();

    if (navigation != 0) {
      dt.setMonth(new Date().getMonth() + navigation);
    }

    const day = dt.getDate();
    const month = dt.getMonth();
    const year = dt.getFullYear();
    monthBanner.innerText = `${dt.toLocaleDateString("en-us", {
      month: "long",
    })} ${year}`;
    calendar.innerHTML = "";
    const dayInMonth = new Date(year, month + 1, 0).getDate();
    const firstDayofMonth = new Date(year, month, 1);
    const dateText = firstDayofMonth.toLocaleDateString("en-us", {
      weekday: "long",
      year: "numeric",
      month: "numeric",
      day: "numeric",
    });

    const dayString = dateText.split(", ")[0];
    const emptyDays = weekdays.indexOf(dayString);

    for (let i = 1; i <= dayInMonth + emptyDays; i++) {
      const dayBox = document.createElement("div");
      dayBox.classList.add("day");
      const monthVal = month + 1 < 10 ? "0" + (month + 1) : month + 1;
      const dateVal = i - emptyDays < 10 ? "0" + (i - emptyDays) : i - emptyDays;
      const dateText = `${year}-${monthVal}-${dateVal}`;
      if (i > emptyDays) {
        dayBox.innerText = i - emptyDays;
        const tasksOfTheDay = task.filter((e) => e.hdate == dateText);

        if (i - emptyDays === day && navigation == 0) {
          dayBox.id = "currentDay";
        }

        tasksOfTheDay.slice(0, 2).forEach(task => {
          const eventDiv = document.createElement("div");
          eventDiv.classList.add("event");
          eventDiv.classList.add("task");
          eventDiv.innerText = task.task;

          const currentDate = new Date();

          const taskDateParts = task.hdate.split("-");
          const taskDate = new Date(taskDateParts[0], taskDateParts[1] - 1, taskDateParts[2]);

          if (currentDate > taskDate) {
            eventDiv.style.textDecoration = "line-through";
          }
        
          dayBox.appendChild(eventDiv);
        });


        if (tasksOfTheDay.length > 2) {
          const showMoreButton = document.createElement("button");
          showMoreButton.innerText = `+${tasksOfTheDay.length - 2} more`;
          showMoreButton.classList.add("event");
          showMoreButton.classList.add("task");
          showMoreButton.classList.add("show-more-button");
          showMoreButton.addEventListener("click", () => {
            const modal = document.getElementById("myModal");
            const taskList = document.getElementById("taskList");
            taskList.innerHTML = ""; // Clear previous tasks
            tasksOfTheDay.slice(2).forEach(task => {
              const taskItem = document.createElement("div");
              taskItem.classList.add("task-item");
              taskItem.innerText = task.task;
              taskList.appendChild(taskItem);
            });
            modal.style.display = "block";
          });
          dayBox.appendChild(showMoreButton);
        }

        dayBox.addEventListener("click", () => {
          // Handle click event if needed
        });
      } else {
        dayBox.classList.add("plain");
      }
      calendar.append(dayBox);
    }
  }

  // Function for going back and next in calendar
  function buttons() {
    const btnBack = document.querySelector("#btnBack");
    const btnNext = document.querySelector("#btnNext");
  
    btnBack.addEventListener("click", () => {
      navigation--;
      loadCalendar();
    });
    btnNext.addEventListener("click", () => {
      navigation++;
      loadCalendar();
    });
  }

  // Close modal when X button is clicked
  const closeButton = document.querySelector(".close");

  closeButton.addEventListener("click", () => {
    const modal = document.getElementById("myModal");
    modal.style.display = "none";
  });

  buttons();
  loadCalendar();
});
