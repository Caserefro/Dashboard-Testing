# Smartsheet Publisher Worker

## The Goal
The backend mathematical pipeline produces a `graphic_contract` containing:
1. `first_time_yield_gauge` (e.g. `96.0%`)
2. `tickets_per_day_chart` (e.g. `[{"day_label": "Monday", "tickets_merged": 5}, ...]`)
3. `burndown_curve` (containing historical `series` points and `forecast` tracks)

Because Smartsheet acts as our frontend UI, this worker is responsible for mapping these computed JSON values into actual Smartsheet cells asynchronously.

## Smartsheet SDK / API Integration

We will use the official `smartsheet-python-sdk`.
* **Documentation**: [Smartsheet API 2.0](https://smartsheet.redoc.ly/)

### Updating Cells (The Mechanics)
In Smartsheet, you update data by specifying the `sheetId`, the `rowId`, and the `columnId`. 
Therefore, our publisher needs a **Mapping Configuration** that tells it which cell coordinates correspond to which metrics.

```python
import smartsheet

# Initialize client
smartsheet_client = smartsheet.Smartsheet('YOUR_SMARTSHEET_ACCESS_TOKEN')

# Create cell objects to update
new_cell_fty = smartsheet.models.Cell()
new_cell_fty.column_id = 1234567890123456  # Map: FTY Column
new_cell_fty.value = graphic_contract["first_time_yield_gauge"]["fty_percentage"]

# Create a row object holding the cell
new_row = smartsheet.models.Row()
new_row.id = 9876543210987654  # Map: KPI Summary Row
new_row.cells.append(new_cell_fty)

# Push update to API
updated_row = smartsheet_client.Sheets.update_rows(
    YOUR_SHEET_ID,
    [new_row]
)
```

### Handling the Burndown Series
The burndown curve requires updating a sequence of rows (one row per day).
1. We will designate a specific sub-sheet (or contiguous block of rows) in Smartsheet as the "Burndown Data Table".
2. The publisher will iterate through `graphic_contract["burndown_curve"]["series"]` and `graphic_contract["burndown_curve"]["forecast"]["future_x"]`.
3. It will construct a list of `smartsheet.models.Row()` objects (updating the Date, Ideal, Remaining, Catch-Up, and Slip columns).
4. It will execute a single bulk `update_rows` API call to update the entire table simultaneously.

### Dashboard Widget Refresh
Once the underlying Smartsheet rows/cells are updated by the API, any Smartsheet Dashboards reading from that sheet will automatically update their widgets (Charts, Metrics, Gauges) upon the user's next browser refresh. No direct Dashboard API calls are strictly necessary if the underlying data table is structured correctly.
