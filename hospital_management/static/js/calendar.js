document.addEventListener("DOMContentLoaded", function() {
    const task = [ 
      { hdate: "21-02-2024", task: "9:30 AM Taylor Swift" },
      { hdate: "22-02-2024", task: "9:30 AM Taylor Sheesh" },
      { hdate: "22-02-2024", task: "10:30 AM Jake Sim" },
      { hdate: "23-02-2024", task: "9:30 AM Jay Park" },
      { hdate: "23-02-2024", task: "11:00 AM Winnie He" },
      { hdate: "23-02-2024", task: "2:00 PM Wendy He" },
      { hdate: "23-02-2024", task: "4:00 PM Chola He" },
      { hdate: "24-02-2024", task: "10:30 AM Peter Griffin" },
      { hdate: "24-02-2024", task: "11:00 AM Stewie Griffin" },
      { hdate: "24-02-2024", task: "2:30 PM Meg Griffin" },
      { hdate: "24-02-2024", task: "4:00 PM Brian Griffin" },
      { hdate: "24-02-2024", task: "4:30 PM Dan Heng" },
    ];
  
    const calendar = document.querySelector("#calendar");
    const monthBanner = document.querySelector("#month");
    let navigation = 0;
    let events = localStorage.getItem("events") ? JSON.parse(localStorage.getItem("events")) : [];
    const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  
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
        const dateText = `${dateVal}-${monthVal}-${year}`;
        if (i > emptyDays) {
          dayBox.innerText = i - emptyDays;
          const eventOfTheDay = events.find((e) => e.date == dateText);
          const tasksOfTheDay = task.filter((e) => e.hdate == dateText);
  
          if (i - emptyDays === day && navigation == 0) {
            dayBox.id = "currentDay";
          }
  
          tasksOfTheDay.slice(0, 2).forEach(task => {
            const eventDiv = document.createElement("div");
            eventDiv.classList.add("event");
            eventDiv.classList.add("task");
            eventDiv.innerText = task.task;
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
  