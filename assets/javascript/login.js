// Executes on click of login button.
function validate() {
    var username = document.getElementById('Uname').value;
    var password = document.getElementById('Pass').value;


    if (checkValidLogin(username, password)){
        //login(username, password);
        window.location = "success.html"; // Redirecting to other page.
    } else {
        // clear values after submit button is pressed
        alert("Log in failed.");
        document.getElementById('Pass').value = "";
    }
    return false;
}    

function login(username, password){
    return false;
}

function checkValidLogin(username, password){
    if(username == "admin"){
        if(password == "admin"){
            return true;
        }
    }
    return false;
}