
// password validation
var number_flag = false;
var lowercase_letter_flag = false;
var uppercase_letter_flag = false;

// Checks the characters of the password Ex: lower/uper case
function check_char() {
    var user_input = document.getElementById("password");

}

// Executes on click of login button.
function validate() {
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    // clear values after submit button is pressed
    document.getElementById("username").value = "";
    document.getElementById("password").value = "";

    if ( username == "admin" && password == "admin"){
        alert ("Login successfully");
        window.location = "success.html"; // Redirecting to other page.
        return false;
    }
    else {
        alert("Log in failed. Please Try Again: ");
        return false;
        }
    }