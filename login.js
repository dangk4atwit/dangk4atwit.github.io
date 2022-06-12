
window.alert = null;


// Executes on click of login button.
function validate() {
    var username = document.getElementById("Uname").value;
    var password = document.getElementById("Pass").value;


    if ( username == "user" && password == "user"){
        alert ("Login successfully");
        window.location = "success.html"; // Redirecting to other page.
        delete window.alert;
    }
    else if ( username == "admin" && password == "admin"){
        alert ("Login successfully");
        window.location = "sucess.html"; // Redirecting to other page.
        delete window.alert;
    }
    else {
        alert ("Log in failed. Please Try Again: ");
        document.getElementById("password").value = "";
        return false;

        }
    }