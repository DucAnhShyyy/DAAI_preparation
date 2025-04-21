from langchain_core.tools import tool
from database import Database
import json

@tool
def get_distinct_values_tool(table: str, column: str) -> str:
    """
    Tool to retrieve distinct values from a column in a given table.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_distinct_values(table, column)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_total_tool(table: str, value_col: str) -> float:
    """
    Tool to calculate the total sum of a numeric column in a table.
    """
    db = Database()
    db.connect()
    try:
        return db.get_total(table, value_col)
    finally:
        db.close()

@tool
def get_count_tool(table: str) -> int:
    """
    Tool to count total number of rows in a table.
    """
    db = Database()
    db.connect()
    try:
        return db.get_count(table)
    finally:
        db.close()

@tool
def get_total_by_group_tool(table: str, group_col: str, value_col: str) -> str:
    """
    Tool to group by a column and calculate total values.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_total_by_group(table, group_col, value_col)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_avg_by_group_tool(table: str, group_col: str, value_col: str) -> str:
    """
    Tool to group by a column and calculate average values.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_avg_by_group(table, group_col, value_col)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_total_by_month_tool(table: str, date_col: str, value_col: str) -> str:
    """
    Tool to calculate total value per month from a date column.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_total_by_month(table, date_col, value_col)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_entity_trend_tool(table: str, entity_col: str, entity_value: str, date_col: str, value_col: str) -> str:
    """
    Tool to get trend of values by month for a specific entity.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_entity_trend(table, entity_col, entity_value, date_col, value_col)
        return json.dumps(result)
    finally:
        db.close()

@tool
def compare_plan_vs_actual_tool(plan_table: str, actual_table: str, match_col: str, value_col: str) -> str:
    """
    Tool to compare planned and actual values and return the difference.
    """
    db = Database()
    db.connect()
    try:
        result = db.compare_plan_vs_actual(plan_table, actual_table, match_col, value_col)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_monthly_growth_tool(table: str, date_col: str, value_col: str) -> str:
    """
    Tool to calculate monthly growth rate based on summed values.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_monthly_growth(table, date_col, value_col)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_best_employees_by_score_tool(kpi_table: str, salein_table: str, top_n: int = 5) -> str:
    """
    Tool to calculate composite score for employees based on KPI and quantity.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_best_employees_by_score(kpi_table, salein_table, top_n)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_best_products_by_region_tool(table: str, top_n: int = 5) -> str:
    """
    Tool to rank products by province coverage and quantity.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_best_products_by_region(table, top_n)
        return json.dumps(result)
    finally:
        db.close()

@tool
def get_deliver_by_region_per_month_tool(regions: List[str], department: str, year: int) -> str:
    """
    Tool: Get total delivery by region per month for a department and year.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_deliver_by_region_per_month(regions, department, year)
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()

@tool
def get_plan_vs_actual_same_day_tool(date: str, department: str, regions: List[str]) -> str:
    """
    Tool: Compare planned vs actual delivery for a specific date.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_plan_vs_actual_same_day(date, department, regions)
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()

@tool
def get_completion_rate_by_department_per_month_tool(year: int) -> str:
    """
    Tool: Calculate completion rate per department per month in a given year.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_completion_rate_by_department_per_month(year)
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()

@tool
def get_avg_kpi_by_month_tool(year: int) -> str:
    """
    Tool: Get average KPI score per month in a given year.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_avg_kpi_by_month(year)
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()

@tool
def get_salein_comparison_by_region_year_tool(years: List[int]) -> str:
    """
    Tool: Compare total sale-in by region across selected years.
    """
    db = Database()
    db.connect()
    try:
        result = db.get_salein_comparison_by_region_year(years)
        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()
