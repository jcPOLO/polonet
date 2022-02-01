function deleteInventory(inventoryId) {
    fetch('/inventory/'+ inventoryId, {
        method: 'DELETE',
        credentials: 'include',
        body: JSON.stringify({ inventoryId: inventoryId })
    }).then((_res) => {
        window.location.href = "/";
    });
}

