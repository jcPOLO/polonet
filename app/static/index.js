function deleteInventory(inventoryId) {
    fetch('/inventory/'+ inventoryId, {
        method: 'DELETE',
        credentials: 'include',
        body: JSON.stringify({ inventoryId: inventoryId })
    }).then((_res) => {
        window.location.href = "/";
    });
};

const searchInput = document.getElementById("search");
const rows = document.querySelectorAll("tbody td");
const table = document.getElementById("inventoryTable");
const cells = table.getElementsByTagName('td');
searchInput.addEventListener("keyup", function(event) {
    const q = event.target.value.toLowerCase();
    console.log(rows)
    rows.forEach((row) => {
        console.log(row)
        row.querySelector("td").innerHTML.toLowerCase().startsWith(q) 
        ? (row.style.display = "tablerow")
        : (row.style.display = "none");
    });
});
// var cells = table.getElementsByTagName('td');
// for (var i = 0; i < cells.length; i++) {
//     cells[i].onclick = function() {
//         var input = document.createElement('input');
//         input.setAttribute('type', 'text');
//         input.value = this.innerHTML;
//         input.style.width = this.offsetWidth - (this.clientLeft * 2) + "px";
//     }
// }
