# Excel MCP Module - Complete Documentation

## 📊 Overview

The Excel module provides comprehensive Excel file manipulation capabilities through MCP (Model Context Protocol). Built with a modular architecture for maintainability and scalability.

## 🏗️ Module Structure

```
modules/excel/
├── operations/          # Core Excel operations (12 files)
│   ├── workbook.py     # Workbook management
│   ├── sheet.py        # Sheet operations
│   ├── data.py         # Data read/write
│   ├── formatting.py   # Cell formatting
│   ├── calculations.py # Formulas & calculations
│   ├── chart.py        # Chart creation
│   ├── tables.py       # Excel table operations
│   ├── pivot.py        # Pivot table creation
│   ├── validation.py   # Data validation
│   ├── cell_utils.py   # Cell utilities
│   ├── cell_validation.py  # Validation helpers
│   └── exceptions.py   # Custom exceptions
├── tools/
│   └── excel.py        # MCP tool registration
└── routes/
    └── excel.py        # FastAPI endpoints (optional)
```

## 🚀 Quick Start

### Import and Use

```python
# Register MCP tools
from src.modules.excel.tools import excel_tools
excel_tools(mcp, get_excel_path)

# Direct operations
from src.modules.excel.operations import workbook, sheet, data

workbook.create_workbook("report.xlsx")
sheet.create_sheet("report.xlsx", "Sales")
data.write_data("report.xlsx", "Sales", [[1, 2, 3]], "A1")
```

## 📚 Available MCP Tools

### Workbook Operations

### create_workbook

Creates a new Excel workbook.

```python
create_workbook(filepath: str) -> str
```

- `filepath`: Path where to create workbook
- Returns: Success message with created file path

### create_worksheet

Creates a new worksheet in an existing workbook.

```python
create_worksheet(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Name for the new worksheet
- Returns: Success message

### get_workbook_metadata

Get metadata about workbook including sheets and ranges.

```python
get_workbook_metadata(filepath: str, include_ranges: bool = False) -> str
```

- `filepath`: Path to Excel file
- `include_ranges`: Whether to include range information
- Returns: String representation of workbook metadata

## Data Operations

### write_data_to_excel

Write data to Excel worksheet.

```python
write_data_to_excel(
    filepath: str,
    sheet_name: str,
    data: List[Dict],
    start_cell: str = "A1"
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `data`: List of dictionaries containing data to write
- `start_cell`: Starting cell (default: "A1")
- Returns: Success message

### read_data_from_excel

Read data from Excel worksheet.

```python
read_data_from_excel(
    filepath: str,
    sheet_name: str,
    start_cell: str = "A1",
    end_cell: str = None,
    preview_only: bool = False
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Source worksheet name
- `start_cell`: Starting cell (default: "A1")
- `end_cell`: Optional ending cell
- `preview_only`: Whether to return only a preview
- Returns: String representation of data

## Formatting Operations

### format_range

Apply formatting to a range of cells.

```python
format_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    font_size: int = None,
    font_color: str = None,
    bg_color: str = None,
    border_style: str = None,
    border_color: str = None,
    number_format: str = None,
    alignment: str = None,
    wrap_text: bool = False,
    merge_cells: bool = False,
    protection: Dict[str, Any] = None,
    conditional_format: Dict[str, Any] = None
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Optional ending cell of range
- Various formatting options (see parameters)
- Returns: Success message

### merge_cells

Merge a range of cells.

```python
merge_cells(filepath: str, sheet_name: str, start_cell: str, end_cell: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Ending cell of range
- Returns: Success message

### unmerge_cells

Unmerge a previously merged range of cells.

```python
unmerge_cells(filepath: str, sheet_name: str, start_cell: str, end_cell: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Ending cell of range
- Returns: Success message

### get_merged_cells

Get merged cells in a worksheet.

```python
get_merged_cells(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- Returns: String representation of merged cells


## Formula Operations

### apply_formula

Apply Excel formula to cell.

```python
apply_formula(filepath: str, sheet_name: str, cell: str, formula: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `cell`: Target cell reference
- `formula`: Excel formula to apply
- Returns: Success message

### validate_formula_syntax

Validate Excel formula syntax without applying it.

```python
validate_formula_syntax(filepath: str, sheet_name: str, cell: str, formula: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `cell`: Target cell reference
- `formula`: Excel formula to validate
- Returns: Validation result message

## Chart Operations

### create_chart

Create chart in worksheet.

```python
create_chart(
    filepath: str,
    sheet_name: str,
    data_range: str,
    chart_type: str,
    target_cell: str,
    title: str = "",
    x_axis: str = "",
    y_axis: str = ""
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `data_range`: Range containing chart data
- `chart_type`: Type of chart (line, bar, pie, scatter, area)
- `target_cell`: Cell where to place chart
- `title`: Optional chart title
- `x_axis`: Optional X-axis label
- `y_axis`: Optional Y-axis label
- Returns: Success message

## Pivot Table Operations

### create_pivot_table

Create pivot table in worksheet.

```python
create_pivot_table(
    filepath: str,
    sheet_name: str,
    data_range: str,
    target_cell: str,
    rows: List[str],
    values: List[str],
    columns: List[str] = None,
    agg_func: str = "mean"
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `data_range`: Range containing source data
- `target_cell`: Cell where to place pivot table
- `rows`: Fields for row labels
- `values`: Fields for values
- `columns`: Optional fields for column labels
- `agg_func`: Aggregation function (sum, count, average, max, min)
- Returns: Success message

## Table Operations

### create_table

Creates a native Excel table from a specified range of data.

```python
create_table(
    filepath: str,
    sheet_name: str,
    data_range: str,
    table_name: str = None,
    table_style: str = "TableStyleMedium9"
) -> str
```

- `filepath`: Path to the Excel file.
- `sheet_name`: Name of the worksheet.
- `data_range`: The cell range for the table (e.g., "A1:D5").
- `table_name`: Optional unique name for the table.
- `table_style`: Optional visual style for the table.
- Returns: Success message.

## Worksheet Operations

### copy_worksheet

Copy worksheet within workbook.

```python
copy_worksheet(filepath: str, source_sheet: str, target_sheet: str) -> str
```

- `filepath`: Path to Excel file
- `source_sheet`: Name of sheet to copy
- `target_sheet`: Name for new sheet
- Returns: Success message

### delete_worksheet

Delete worksheet from workbook.

```python
delete_worksheet(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Name of sheet to delete
- Returns: Success message

### rename_worksheet

Rename worksheet in workbook.

```python
rename_worksheet(filepath: str, old_name: str, new_name: str) -> str
```

- `filepath`: Path to Excel file
- `old_name`: Current sheet name
- `new_name`: New sheet name
- Returns: Success message

## Range Operations

### copy_range

Copy a range of cells to another location.

```python
copy_range(
    filepath: str,
    sheet_name: str,
    source_start: str,
    source_end: str,
    target_start: str,
    target_sheet: str = None
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Source worksheet name
- `source_start`: Starting cell of source range
- `source_end`: Ending cell of source range
- `target_start`: Starting cell for paste
- `target_sheet`: Optional target worksheet name
- Returns: Success message

### delete_range

Delete a range of cells and shift remaining cells.

```python
delete_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str,
    shift_direction: str = "up"
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Ending cell of range
- `shift_direction`: Direction to shift cells ("up" or "left")
- Returns: Success message

### validate_excel_range

Validate if a range exists and is properly formatted.

```python
validate_excel_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str = None
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Optional ending cell of range
- Returns: Validation result message

### get_data_validation_info

Get data validation rules and metadata for a worksheet.

```python
get_data_validation_info(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- Returns: JSON string containing all data validation rules with metadata including:
  - Validation type (list, whole, decimal, date, time, textLength)
  - Operator (between, notBetween, equal, greaterThan, lessThan, etc.)
  - Allowed values for list validations (resolved from ranges)
  - Formula constraints for numeric/date validations
  - Cell ranges where validation applies
  - Prompt and error messages

**Note**: The `read_data_from_excel` tool automatically includes validation metadata for individual cells when available.

## Row and Column Operations

### insert_rows

Insert one or more rows starting at the specified row.

```python
insert_rows(
    filepath: str,
    sheet_name: str,
    start_row: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_row`: Row number where to start inserting (1-based)
- `count`: Number of rows to insert (default: 1)
- Returns: Success message

### insert_columns

Insert one or more columns starting at the specified column.

```python
insert_columns(
    filepath: str,
    sheet_name: str,
    start_col: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_col`: Column number where to start inserting (1-based)
- `count`: Number of columns to insert (default: 1)
- Returns: Success message

---

## 💡 Usage Examples

### Example 1: Create Report with Formatting

```python
from src.modules.excel.operations import workbook, sheet, data, formatting

# Create workbook
workbook.create_workbook("sales_report.xlsx")
sheet.create_sheet("sales_report.xlsx", "Q1 Sales")

# Write header
data.write_data(
    "sales_report.xlsx",
    "Q1 Sales",
    [["Product", "Sales", "Revenue"]],
    "A1"
)

# Format header
formatting.format_range(
    "sales_report.xlsx",
    "Q1 Sales",
    "A1",
    "C1",
    bold=True,
    bg_color="4472C4",
    font_color="FFFFFF"
)

# Write data
data.write_data(
    "sales_report.xlsx",
    "Q1 Sales",
    [
        ["Widget A", 100, 5000],
        ["Widget B", 150, 7500],
        ["Widget C", 200, 10000]
    ],
    "A2"
)
```

### Example 2: Create Chart from Data

```python
from src.modules.excel.operations import chart

# Create line chart
chart.create_chart(
    "sales_report.xlsx",
    "Q1 Sales",
    data_range="A1:C4",
    chart_type="line",
    target_cell="E2",
    title="Q1 Sales Trend",
    x_axis="Products",
    y_axis="Revenue"
)
```

### Example 3: Create Pivot Table

```python
from src.modules.excel.operations import pivot

# Create pivot table
pivot.create_pivot_table(
    "sales_report.xlsx",
    "Q1 Sales",
    data_range="A1:C4",
    target_cell="F2",
    rows=["Product"],
    values=["Revenue"],
    agg_func="sum"
)
```

### Example 4: Data Validation

```python
from src.modules.excel.operations import validation

# Add dropdown validation
validation.add_data_validation(
    "sales_report.xlsx",
    "Q1 Sales",
    "D2:D10",
    validation_type="list",
    formula="Approved,Pending,Rejected"
)
```

---

## 🔧 Advanced Features

### Custom Exceptions

```python
from src.modules.excel.operations.exceptions import (
    ValidationError,
    WorkbookError,
    SheetError,
    DataError,
    FormattingError
)

try:
    workbook.create_workbook("existing.xlsx")
except WorkbookError as e:
    print(f"Workbook error: {e}")
```

### Cell Utilities

```python
from src.modules.excel.operations import cell_utils

# Convert cell reference
col_letter = cell_utils.column_index_to_letter(1)  # 'A'
col_index = cell_utils.column_letter_to_index('A')  # 1

# Validate cell reference
is_valid = cell_utils.is_valid_cell_reference('A1')  # True
```

---

## 📊 Supported Chart Types

| Type | Description |
|------|-------------|
| `line` | Line chart for trends |
| `bar` | Vertical bar chart |
| `column` | Horizontal bar chart |
| `pie` | Pie chart for proportions |
| `scatter` | Scatter plot for correlation |
| `area` | Area chart for cumulative data |

---

## 🎨 Supported Table Styles

- `TableStyleLight1` through `TableStyleLight21`
- `TableStyleMedium1` through `TableStyleMedium28`
- `TableStyleDark1` through `TableStyleDark11`

---

## ⚙️ Configuration

### File Path Resolution

When using **SSE or Streamable HTTP**:

```bash
# Set base path for Excel files
export EXCEL_FILES_PATH="/path/to/excel/files"

# Relative paths will be resolved from this base
workbook.create_workbook("report.xlsx")  # Creates /path/to/excel/files/report.xlsx
```

When using **Stdio**:

```python
# Absolute paths required
workbook.create_workbook("/full/path/to/report.xlsx")
```

---

## 🔐 Best Practices

### 1. Error Handling

```python
from src.modules.excel.operations import workbook
from src.modules.excel.operations.exceptions import WorkbookError

try:
    workbook.create_workbook("report.xlsx")
except WorkbookError as e:
    print(f"Failed to create workbook: {e}")
```

### 2. Validate Before Operations

```python
from src.modules.excel.operations import validation

# Validate range before writing
result = validation.validate_excel_range(
    "report.xlsx",
    "Sheet1",
    "A1",
    "Z100"
)
```

### 3. Use Named Ranges

```python
# Define named range for reusability
data.write_data("report.xlsx", "Sheet1", data, "SalesData")
```

### 4. Batch Operations

```python
# Batch multiple writes
data_rows = [
    ["Header1", "Header2", "Header3"],
    ["Data1", "Data2", "Data3"],
    ["Data4", "Data5", "Data6"]
]

data.write_data("report.xlsx", "Sheet1", data_rows, "A1")
```

---

## 🧪 Testing

### Unit Tests

```python
import pytest
from src.modules.excel.operations import workbook

def test_create_workbook():
    result = workbook.create_workbook("test.xlsx")
    assert "successfully" in result.lower()
```

### Integration Tests

```python
def test_full_workflow():
    # Create
    workbook.create_workbook("test.xlsx")
    sheet.create_sheet("test.xlsx", "Data")
    
    # Write
    data.write_data("test.xlsx", "Data", [[1, 2, 3]], "A1")
    
    # Read
    result = data.read_data_from_excel("test.xlsx", "Data", "A1", "C1")
    
    # Verify
    assert "1" in result and "2" in result and "3" in result
```

---

## 📖 API Reference

For complete API documentation, see the module source code:

- **Operations**: `src/modules/excel/operations/`
- **Tools**: `src/modules/excel/tools/excel.py`
- **Routes**: `src/modules/excel/routes/excel.py`

---

## 🔗 Related Documentation

- [Server Module Documentation](SERVER.md)
- [Modular Architecture](MODULAR_STRUCTURE.md)
- [Main README](../README.md)

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: File not found error

```python
# Solution: Use absolute path or set EXCEL_FILES_PATH
export EXCEL_FILES_PATH="/path/to/files"
```

**Issue**: Permission denied

```python
# Solution: Check file permissions
chmod 644 report.xlsx
```

**Issue**: Invalid cell reference

```python
# Solution: Validate cell reference
from src.modules.excel.operations import cell_utils
is_valid = cell_utils.is_valid_cell_reference('A1')
```

---

## 📝 Changelog

### Version 2.0 - Modular Architecture
- ✅ Reorganized into modular structure
- ✅ Separated operations, tools, and routes
- ✅ Improved error handling with custom exceptions
- ✅ Enhanced documentation

### Version 1.0 - Initial Release
- ✅ Basic Excel operations
- ✅ MCP tool integration
- ✅ Support for formulas and charts

### delete_sheet_rows

Delete one or more rows starting at the specified row.

```python
delete_sheet_rows(
    filepath: str,
    sheet_name: str,
    start_row: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_row`: Row number where to start deleting (1-based)
- `count`: Number of rows to delete (default: 1)
- Returns: Success message

### delete_sheet_columns

Delete one or more columns starting at the specified column.

```python
delete_sheet_columns(
    filepath: str,
    sheet_name: str,
    start_col: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_col`: Column number where to start deleting (1-based)
- `count`: Number of columns to delete (default: 1)
- Returns: Success message

