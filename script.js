function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text/plain", ev.target.id);
}

function drop(ev, status) {
    ev.preventDefault();
    var data = ev.dataTransfer.getData("text/plain");
    var taskElement = document.getElementById(data);
    var newStatus = status.toUpperCase();
    
    if (taskElement) {
        var jsonData = {
            "taskTitle": taskElement.querySelector('strong').innerText,
            "newStatus": newStatus
        };
        var jsonString = JSON.stringify(jsonData);
        
        var target = ev.target.closest('.dropzone');
        if (target) {
            target.appendChild(taskElement);
            console.log(jsonString);
        }
    }
}
function showTaskOptions(taskTitle) {
    console.log("Show options for task: " + taskTitle);
    document.getElementById("taskOptionsModal").style.display = "block";
}