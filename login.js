

// Executes on click of login button.
function validate() {
    var username = document.getElementById("Uname").value;
    var password = document.getElementById("Pass").value;

    // clear values after submit button is pressed
    document.getElementById("password").value = "";

    if ( username == "user" && password == "user"){
        alert ("Login successfully");
        window.location = "success.html"; // Redirecting to other page.
    }
    else if ( username == "admin" && password == "admin"){
        alert ("Login successfully");
        window.location = "sucess.html"; // Redirecting to other page.
    }
    else {
        alert ("Log in failed. Please Try Again: ");
        return false;
        }
    }