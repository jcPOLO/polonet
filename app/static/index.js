function deleteInventory(inventoryId) {
    fetch('/inventory/'+ inventoryId, {
        method: 'DELETE',
        credentials: 'include',
        body: JSON.stringify({ inventoryId: inventoryId })
    }).then((_res) => {
        window.location.href = "/";
    });
}

// function validatePasswords() {
//     var password = document.getElementById("password1").value;
//     var confirmPassword = document.getElementById("password2").value;
//     if (password != confirmPassword) {
//         alert("Passwords do not match.");
//         return false;
//     }
//     return true;
// }