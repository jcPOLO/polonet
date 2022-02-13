// InventoryTable class. 
// It does all ralted tasks for ag-grid table framekwork and it has all its config.
HIDDEN_DEVICE_ATTR = ['id','date_created','date_modified'];

class InventoryTable {

    constructor(inventorySlug) {
        this.inventorySlug = inventorySlug;
        // specify the columns
        this.columnDefs = [];
        // specify the data
        this.rowData = [];
        // let the grid know which columns and what data to use
        this.gridOptions = {
            columnDefs: this.columnDefs,
            rowData: this.rowData,
            rowSelection: 'multiple',
            domLayout: 'autoHeight',
            rowDragManaged: true,
            animateRows: true,
            rowDragMultiRow: true,
            onFirstDataRendered: this.onFirstDataRendered,
            defaultColDef: {
                resizable: true,
                sortable: true, 
                filter: true,
                editable: true,
                // must bind or this is lost and becomes undefined.
                onCellValueChanged: this.onCellValueChanged.bind(this) 
            }
        };
        // lookup the container we want the Grid to use
        this.eGridDiv = document.querySelector('#myGrid');
    };

    // get and set the column configuration attributes.
    getColDefs(anObject) {
        const colDefs = this.gridOptions.api.getColumnDefs();
        colDefs.length=0;
        const keys = Object.keys(anObject[0]);
        keys.forEach(key => {
            if (key == 'hostname') {
                colDefs.push({
                    field : key,
                    checkboxSelection: false,
                    width: 170,
                    rowDrag: true,
                })
            } else if (['port','platform'].includes(key)) {
                colDefs.push({
                    field: key,
                    width: 110,
                })
            } else if (HIDDEN_DEVICE_ATTR.includes(key)) {
                colDefs.push({
                    field: key,
                    hide: true,
                    suppressToolPanel: true
                })
            } else {
                colDefs.push({
                    field : key,
                    width: 150,
                });
            }
        });
        return colDefs
    };

    onFirstDataRendered(params) {
        params.api.sizeColumnsToFit();
      }

    // Creates the table and populates the data from the backend API.
    createInventoryTable() {
        // create the grid passing in the div to use together with the columns & data we want to use
        const aGrid_object = new agGrid.Grid(this.eGridDiv, this.gridOptions);
        // fetch the row data to use and one ready provide it to the Grid via the Grid API
        fetch('/v1/inventory/' + this.inventorySlug, {
            method: 'GET',
            credentials: 'include',
        })
        .then(response => response.json())
        .then(data => {
            this.gridOptions.api.setColumnDefs(this.getColDefs(data));
            this.gridOptions.api.setRowData(data);
        });
    };

    // TODO: At the moment this method removes all unselected rows from the inventory.
    getSelectedRows() {
        const selectedNodes = this.gridOptions.api.getSelectedNodes();
        const selectedData = selectedNodes.map( node => node.data );
        return this.updateInventory(selectedData)
    };

    // Updates in the backend the inventory attributed changed.
    onCellValueChanged(params) {
        let changedData = [params.data];
        params.api.applyTransaction({ update: changedData });
        const id = changedData[0].id
        return this.updateDevice(id, changedData[0])
    };

    // TODO: Need to only update/refresh the attributed changed. 
    updateInventory(data=[]) {
        fetch('/v1/inventory/'+ this.inventorySlug, {
            method: 'PUT',
            credentials: 'include',
            body: JSON.stringify(data)
        }).then((_res) => {
            window.location.href = '/inventory/'+ this.inventorySlug;
        });
    };

    updateDevice(id, data=[]) {
        fetch('/v1/device/' + id, {
            method: 'PUT',
            credentials: 'include',
            body: JSON.stringify(data)
        }).then((_res) => {
            window.location.href = '/inventory/'+ this.inventorySlug;
        });
    };
};

// Function called when clicked on the X button close to the inventory name list.
function deleteInventory(inventorySlug) {
    fetch('/inventory/'+ inventorySlug, {
        method: 'DELETE',
        credentials: 'include',
        body: JSON.stringify({ inventorySlug: inventorySlug })
    }).then((_res) => {
        window.location.href = "/";
    });
};

// setup the grid after the page has finished loading
if (document.readyState === "loading") {
    document.addEventListener('DOMContentLoaded', function () {
        const gridDiv = document.querySelector('#myGrid');
        if (gridDiv) {
            const inventorySlug = gridDiv.getAttribute("name")
            inventoryTable = new InventoryTable(inventorySlug);
            inventoryTable.createInventoryTable();
        }
      });
} else {
    if (gridDiv) {
        const gridDiv = document.querySelector('#myGrid');
        const inventorySlug = gridDiv.getAttribute("name");
        inventoryTable = new InventoryTable(inventorySlug);
        inventoryTable.createInventoryTable();
    }
}
