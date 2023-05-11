
setTimeout(function() {
    document.querySelectorAll('.alert').forEach(function(alert) {
        alert.style.display = 'none';
    });
}, 1000);
var timeLimit = 0;

// Get the timer element
var timerElement = document.getElementById("timer");

// Update the timer every second
var timer = setInterval(function() {
    timeLimit++;
    var minutes = Math.floor(timeLimit / 60);
    var seconds = timeLimit % 60;
    if (seconds < 10) {
    seconds = "0" + seconds;
    }
    timerElement.innerHTML = minutes + ":" + seconds;
    timerElement.value = minutes*60+seconds;
}, 1000);