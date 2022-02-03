function deleteInventory(inventoryId) {
    fetch('/inventory/'+ inventoryId, {
        method: 'DELETE',
        credentials: 'include',
        body: JSON.stringify({ inventoryId: inventoryId })
    }).then((_res) => {
        window.location.href = "/";
    });
};

function getColDefs(anObject) {
    const colDefs = gridOptions.api.getColumnDefs();
    colDefs.length=0;
    const keys = Object.keys(anObject[0]);
    keys.forEach(key => {
        if (key == 'hostname') {
            colDefs.push({
                field : key,
                sortable: true, 
                filter: true,
                checkboxSelection: false,
                editable: true,
                onCellValueChanged: onCellValueChanged
            })
        } else {
            colDefs.push({
                field : key,
                sortable: true, 
                filter: true,
                editable: true,
                onCellValueChanged: onCellValueChanged
            });
        }
    });
    return colDefs
}

function createInventoryTable(inventoryName) {
    // specify the columns
    const columnDefs = [];
    // specify the data
    const rowData = [];
    // let the grid know which columns and what data to use
    const gridOptions = {
        columnDefs: columnDefs,
        rowData: rowData,
        rowSelection: 'multiple'
    };
    // lookup the container we want the Grid to use
    const eGridDiv = document.querySelector('#myGrid');
    // create the grid passing in the div to use together with the columns & data we want to use
    new agGrid.Grid(eGridDiv, gridOptions);
    // fetch the row data to use and one ready provide it to the Grid via the Grid API
    fetch('/v1/inventory/' + inventoryName, {
        method: 'GET',
        credentials: 'include',
    })
    .then(response => response.json())
    .then(data => {
        gridOptions.api.setColumnDefs(getColDefs(data));
        gridOptions.api.setRowData(data);
    });
}

const getSelectedRows = (inventoryName) => {
    const selectedNodes = gridOptions.api.getSelectedNodes()
    const selectedData = selectedNodes.map( node => node.data )
    const selectedDataStringPresentation = selectedData.map( node => `${node.hostname} ${node}`).join(', ')
    return updateInventory(inventoryName, selectedData)
}

function updateInventory(inventoryName, data=[]) {
    fetch('/v1/inventory/'+ inventoryName, {
        method: 'UPDATE',
        credentials: 'include',
        body: JSON.stringify(data)
    }).then((_res) => {
        window.location.href = '/inventory/'+ inventoryName;
    });
};

function deleteInventory(inventoryId) {
    fetch('/inventory/'+ inventoryId, {
        method: 'DELETE',
        credentials: 'include',
        body: JSON.stringify({ inventoryId: inventoryId })
    }).then((_res) => {
        window.location.href = "/";
    });
};

function onCellValueChanged(params) {
    var changedData = [params.data];
    console.log('cell modifcada');
    params.api.applyTransaction({ update: changedData });
    updateInventory('asdfa', changedData)
  }
  
// setup the grid after the page has finished loading
document.addEventListener('DOMContentLoaded', function () {
    var gridDiv = document.querySelector('#myGrid');
    new agGrid.Grid(gridDiv, gridOptions);
  });
