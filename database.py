import pandas as pd
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from langchain_core.tools import tool
import decimal
import numpy as np
from collections import defaultdict
from typing import List, Dict
import json
load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.data_dir = "sales_data"
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DB'),
                port=int(os.getenv('MYSQL_PORT', 3306))
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            print("MySQL connection closed")
    
    def create_salein_class(self):
        """Create and populate salein_class table"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS salein_class (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE,
                    employee_name VARCHAR(255),
                    department VARCHAR(255),
                    item_code VARCHAR(50),
                    product_name VARCHAR(255),
                    quantity INT
                )
            """)
            
            salein_class_df = pd.read_csv(os.path.join(self.data_dir, "salein_class.csv"))
            for _, row in salein_class_df.iterrows():
                self.cursor.execute("""
                    INSERT IGNORE INTO salein_class (date, employee_name, department, item_code, product_name, quantity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (row['Date'], row['Employee_Name'], row['Department'], row['item_code'], row['product_name'], row['Số lượng']))
            print("Successfully created salein_class table")
            return True
        except Error as e:
            print(f"Error creating salein_class table: {e}")
            return False

    def create_salein_thuc_xuat(self):
        """Create and populate salein_thuc_xuat table"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS salein_thuc_xuat (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE,
                    employee_name VARCHAR(255),
                    unit_code VARCHAR(255),
                    product_name VARCHAR(255),
                    quantity INT,
                    province VARCHAR(255)
                )
            """)
            
            salein_thuc_xuat_df = pd.read_csv(os.path.join(self.data_dir, "salein_thuc_xuat.csv"))
            for _, row in salein_thuc_xuat_df.iterrows():
                self.cursor.execute("""
                    INSERT IGNORE INTO salein_thuc_xuat (date, employee_name, unit_code, product_name, quantity, province)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (row['Date'], row['Employee_Name'], row['unit_code'], row['product_name'], row['Số lượng xuất'], row['province']))
            print("Successfully created salein_thuc_xuat table")
            return True
        except Error as e:
            print(f"Error creating salein_thuc_xuat table: {e}")
            return False

    def create_kpi_thuc_xuat(self):
        """Create and populate kpi_thuc_xuat table"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kpi_thuc_xuat (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE,
                    employee_name VARCHAR(255),
                    kpi_code VARCHAR(50),
                    region VARCHAR(255),
                    product_name VARCHAR(255),
                    kpi_score INT
                )
            """)
            
            kpi_thuc_xuat_df = pd.read_csv(os.path.join(self.data_dir, "kpi_thuc_xuat.csv"))
            for _, row in kpi_thuc_xuat_df.iterrows():
                self.cursor.execute("""
                    INSERT IGNORE INTO kpi_thuc_xuat (date, employee_name, kpi_code, region, product_name, kpi_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (row['Date'], row['Employee_Name'], row['KPI_code'], row['region'], row['product_name'], row['Số KPI']))
            print("Successfully created kpi_thuc_xuat table")
            return True
        except Error as e:
            print(f"Error creating kpi_thuc_xuat table: {e}")
            return False

    def create_tables(self):
        """Create all necessary tables and insert data into them"""
        if not self.connect():
            return
        
        try:
            if self.create_salein_class():
                print("Salein Class table created and data inserted.")
            if self.create_salein_thuc_xuat():
                print("Salein Thuc Xuat table created and data inserted.")
            if self.create_kpi_thuc_xuat():
                print("KPI Thuc Xuat table created and data inserted.")
            
            self.connection.commit()
            print("All tables created and data inserted successfully.")
        
        except Error as e:
            print(f"Error in database creation or data insertion: {e}")
        
        finally:
            self.close()

    def extract_tables_schemas(self):
        """Extract schemas of all tables in the database"""
        if not self.connect():
            return {}
        
        try:
            # Get list of tables
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (os.getenv('MYSQL_DB'),))
            tables = self.cursor.fetchall()
            
            schemas = {}
            for (table_name,) in tables:
                # Get columns info for each table
                self.cursor.execute("""
                    SELECT 
                        column_name,
                        column_type,
                        is_nullable,
                        column_key,
                        extra,
                        column_comment
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = %s 
                    ORDER BY ordinal_position
                """, (os.getenv('MYSQL_DB'), table_name))
                
                columns = self.cursor.fetchall()
                
                # Get foreign keys info
                self.cursor.execute("""
                    SELECT
                        column_name,
                        referenced_table_name,
                        referenced_column_name
                    FROM information_schema.key_column_usage
                    WHERE table_schema = %s
                    AND table_name = %s
                    AND referenced_table_name IS NOT NULL
                """, (os.getenv('MYSQL_DB'), table_name))
                
                foreign_keys = self.cursor.fetchall()
                
                # Format schema information
                schema = {
                    'columns': [
                        {
                            'name': col[0],
                            'type': col[1],
                            'nullable': col[2],
                            'key': col[3],
                            'extra': col[4],
                            'comment': col[5]
                        }
                        for col in columns
                    ],
                    'foreign_keys': [
                        {
                            'column': fk[0],
                            'references_table': fk[1],
                            'references_column': fk[2]
                        }
                        for fk in foreign_keys
                    ]
                }
                
                schemas[table_name] = schema
            
            return schemas
            
        except Error as e:
            print(f"Error extracting table schemas: {e}")
            return {}
            
        finally:
            self.close()
            
    def get_distinct_values(self, table:str, column: str) -> list: 
        """
        Get distinct values of a column in a table.
        
        Args:
            table (str): Name of the table.
            column (str): Column name to retrieve distinct values from.

        Returns:
            list: A list of unique values found in the specified column.
        """
        self.cursor.execute(f"SELECT DISTINCT {column} FROM {table}")
        return [row[0] for row in self.cursor.fetchall()]


    def get_total(self, table: str, value_col: str) -> float:
        """
        Get the total sum of a numeric column in a table.

        Args:
            table (str): Name of the table.
            value_col (str): Name of the column to sum.

        Returns:
            float: The total sum of the specified column.
        """        
        self.cursor.execute(f"SELECT SUM({value_col}) FROM {table}")
        return self.cursor.fetchone()[0]


    def get_count(self, table: str) -> int:
        """
        Count total number of records in a table.

        Args:
            table (str): Name of the table.

        Returns:
            int: Total number of rows in the table.   
        """
        self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return self.cursor.fetchone()[0]


    def get_total_by_group(self, table: str, group_col: str, value_col: str) -> list:
        """
        Get total value grouped by a specified column.

        Args:
            table (str): Name of the table.
            group_col (str): Column to group by (e.g. 'region', 'department').
            value_col (str): Column to aggregate using SUM.

        Returns:
            list[tuple]: List of (group_value, total) pairs sorted by total descending.
            e.g: [("North", 5000), ("South", 3000)]
        """
        self.cursor.execute(f"""
            SELECT {group_col}, SUM({value_col}) AS total
            FROM {table}
            GROUP BY {group_col}
            ORDER BY total DESC
        """)
        return self.cursor.fetchall()


    def get_avg_by_group(self, table: str, group_col: str, value_col: str) -> list:
        """
        Get average value grouped by a specified column.

        Args:
            table (str): Name of the table.
            group_col (str): Column to group by (e.g. 'product_name').
            value_col (str): Column to aggregate using AVG.

        Returns:
            list[tuple]: List of (group_value, average) pairs sorted by average descending.
            e.g: [("Product A", 105.4), ("Product B", 89.2)]
        """
        self.cursor.execute(f"""
            SELECT {group_col}, AVG({value_col}) AS avg_value
            FROM {table}
            GROUP BY {group_col}
            ORDER BY avg_value DESC
        """)
        return self.cursor.fetchall()

    
    def get_total_by_month(self, table: str, date_col: str, value_col: str) -> list:
        """
        Get total value grouped by month (from a date column).

        Args:
            table (str): Name of the table.
            date_col (str): Column containing date values.
            value_col (str): Column to aggregate using SUM.

        Returns:
            list[tuple]: List of (month, total) pairs in chronological order.
            e.g: [("2024-01", 1200), ("2024-02", 1800)]
        """
        self.cursor.execute(f"""
            SELECT DATE_FORMAT({date_col}, '%Y-%m') AS month, SUM({value_col}) AS total
            FROM {table}
            GROUP BY month
            ORDER BY month
        """)
        return self.cursor.fetchall()


    def get_entity_trend(self, table: str, entity_col: str, entity_value: str, date_col: str, value_col: str) -> list:
        """
        Get monthly trend of total value for a specific entity (e.g. employee, product).

        Args:
            table (str): Name of the table.
            entity_col (str): Column to filter by (e.g. 'employee_name').
            entity_value (str): Value of the entity to track.
            date_col (str): Date column to group by month.
            value_col (str): Column to sum.

        Returns:
            list[tuple]: List of (month, total) for the specified entity.
            e.g: [("2024-01", 300), ("2024-02", 500)]
        """
        self.cursor.execute(f"""
            SELECT DATE_FORMAT({date_col}, '%Y-%m') AS month, SUM({value_col}) AS total
            FROM {table}
            WHERE {entity_col} = %s
            GROUP BY month
            ORDER BY month
        """, (entity_value,))
        return self.cursor.fetchall()


    def compare_plan_vs_actual(self, plan_table: str, actual_table: str, match_col: str, value_col: str) -> list:
        """
        Compare planned vs actual values for a common attribute (e.g. product_name).

        Args:
            plan_table (str): Table containing planned values.
            actual_table (str): Table containing actual values.
            match_col (str): Column used to join the two tables (e.g. 'product_name').
            value_col (str): Column to compare (e.g. 'quantity').

        Returns:
            list[tuple]: List of (item, planned, actual, difference) sorted by difference.
            e.g: [("Product A", 1000, 800, -200)]
        """
        self.cursor.execute(f"""
            SELECT 
                p.{match_col},
                SUM(p.{value_col}) AS planned,
                SUM(a.{value_col}) AS actual,
                SUM(a.{value_col}) - SUM(p.{value_col}) AS difference
            FROM {plan_table} p
            JOIN {actual_table} a ON p.{match_col} = a.{match_col}
            GROUP BY p.{match_col}
            ORDER BY difference DESC
        """)
        return self.cursor.fetchall()


    def get_monthly_growth(self, table: str, date_col: str, value_col: str) -> list:
        """
        Calculate monthly growth rate based on summed values.

        Args:
            table (str): Name of the table.
            date_col (str): Date column to group by month.
            value_col (str): Column to aggregate using SUM.

        Returns:
            list[tuple]: List of (month, total, previous_total, growth_rate) for each month.
            e.g: [("2024-02", 1200, 1000, 20.0)]
        """
        self.cursor.execute(f"""
            SELECT 
                month,
                total,
                LAG(total) OVER (ORDER BY month) AS prev_total,
                ROUND((total - LAG(total) OVER (ORDER BY month)) / LAG(total) OVER (ORDER BY month) * 100, 2) AS growth_rate
            FROM (
                SELECT DATE_FORMAT({date_col}, '%Y-%m') AS month, SUM({value_col}) AS total
                FROM {table}
                GROUP BY month
            ) AS subquery
        """)
        return self.cursor.fetchall()  


    def get_best_employees_by_score(self, kpi_table: str, salein_table: str, top_n: int = 5) -> List[Dict]:
        """
        Calculate a composite score for employees based on average KPI and total quantity.

        Args:
            kpi_table (str): Name of the KPI table (columns: employee_name, kpi_score).
            salein_table (str): Name of the actual sales table (columns: employee_name, quantity).
            top_n (int): Number of top employees to return.

        Returns:
            list[dict]: List of employees with their average KPI, total quantity, and composite score.
            Example:
                [{"employee_name": "A", "avg_kpi": 85.5, "quantity": 1200, "score": 91.3}]
        """
        # Join both tables on employee_name, then calculate weighted score
        self.cursor.execute(f"""
            SELECT 
                k.employee_name,
                AVG(k.kpi_score) AS avg_kpi,
                SUM(s.quantity) AS total_quantity,
                ROUND(0.6 * AVG(k.kpi_score) + 0.4 * SUM(s.quantity), 2) AS composite_score
            FROM {kpi_table} k
            JOIN {salein_table} s ON k.employee_name = s.employee_name
            GROUP BY k.employee_name
            ORDER BY composite_score DESC
            LIMIT %s
        """, (top_n,))
        return [
            {
                "employee_name": row[0],
                "avg_kpi": float(row[1]),
                "quantity": float(row[2]),
                "score": float(row[3])
            }
            for row in self.cursor.fetchall()
        ]


    def get_best_products_by_region(self, table: str, top_n: int = 5) -> List[Dict]:
        """
        Find the most prominent products across regions based on quantity and regional coverage.

        Args:
            table (str): Table name (columns: product_name, province, quantity).
            top_n (int): Number of top products to return.

        Returns:
            list[dict]: List of products with number of provinces, total quantity, and score.
            Example:
                [{"product_name": "X", "provinces": 8, "quantity": 3200, "score": 1604.0}]
        """
        # Count distinct provinces and sum quantity, then compute composite score
        self.cursor.execute(f"""
            SELECT 
                product_name,
                COUNT(DISTINCT province) AS province_coverage,
                SUM(quantity) AS total_quantity,
                ROUND(0.5 * COUNT(DISTINCT province) + 0.5 * SUM(quantity), 2) AS composite_score
            FROM {table}
            GROUP BY product_name
            ORDER BY composite_score DESC
            LIMIT %s
        """, (top_n,))
        return [
            {
                "product_name": row[0],
                "provinces": int(row[1]),
                "quantity": float(row[2]),
                "score": float(row[3])
            }
            for row in self.cursor.fetchall()
        ]

    def get_deliver_by_region_per_month(self, regions: List[str], department: str, year: int) -> List[dict]:
        """
        Get total deliver value by region per month for a specific department and year.
        """
        placeholders = ','.join(['%s'] * len(regions))
        query = f"""
            SELECT 
                Organization,
                DATE_FORMAT(Date, '%%Y-%%m') AS Month,
                SUM(Deliver) AS Total_Deliver
            FROM kpi_thuc_xuat
            WHERE YEAR(Date) = %s AND Department = %s AND Organization IN ({placeholders})
            GROUP BY Organization, Month
            ORDER BY Organization, Month
        """
        params = [year, department] + regions
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [{"organization": r[0], "month": r[1], "total_deliver": float(r[2])} for r in rows]

    def get_plan_vs_actual_same_day(self, date: str, department: str, regions: List[str]) -> List[dict]:
        """
        Compare planned vs actual values for a given date, department, and regions.
        """
        placeholders = ','.join(['%s'] * len(regions))

        self.cursor.execute(f"""
            SELECT Organization, SUM(Deliver)
            FROM kpi_thuc_xuat
            WHERE Date = %s AND Department = %s AND Organization IN ({placeholders})
            GROUP BY Organization
        """, [date, department] + regions)
        actual = {r[0]: float(r[1]) for r in self.cursor.fetchall()}

        self.cursor.execute(f"""
            SELECT Organization, SUM(SaleIn)
            FROM salein_class
            WHERE Date = %s AND Department = %s AND Organization IN ({placeholders})
            GROUP BY Organization
        """, [date, department] + regions)
        plan = {r[0]: float(r[1]) for r in self.cursor.fetchall()}

        all_keys = set(actual) | set(plan)
        return [{
            "organization": org,
            "planned": plan.get(org, 0),
            "actual": actual.get(org, 0),
            "difference": actual.get(org, 0) - plan.get(org, 0)
        } for org in all_keys]

    def get_completion_rate_by_department_per_month(self, year: int) -> List[dict]:
        """
        Get monthly completion rate (actual / planned) per department.
        """
        self.cursor.execute(f"""
            SELECT s.Department, DATE_FORMAT(s.Date, '%%Y-%%m') AS Month,
                ROUND(SUM(t.SaleIn) / SUM(s.SaleIn) * 100, 2) AS Completion_Rate
            FROM salein_class s
            JOIN salein_thuc_xuat t ON s.Department = t.Department AND DATE(s.Date) = DATE(t.Date)
            WHERE YEAR(s.Date) = %s
            GROUP BY s.Department, Month
        """, (year,))
        rows = self.cursor.fetchall()
        return [{"department": r[0], "month": r[1], "completion_rate": float(r[2])} for r in rows]

    def get_avg_kpi_by_month(self, year: int) -> List[dict]:
        """
        Get average KPI score per month for a given year.
        """
        self.cursor.execute(f"""
            SELECT DATE_FORMAT(Date, '%%Y-%%m') AS Month, ROUND(AVG(kpi_score), 2)
            FROM kpi_thuc_xuat
            WHERE YEAR(Date) = %s
            GROUP BY Month
        """, (year,))
        return [{"month": r[0], "avg_kpi": float(r[1])} for r in self.cursor.fetchall()]

    def get_salein_comparison_by_region_year(self, years: List[int]) -> List[dict]:
        """
        Compare sale-in performance by region across multiple years.
        """
        placeholders = ','.join(['%s'] * len(years))
        self.cursor.execute(f"""
            SELECT Organization, YEAR(Date), SUM(SaleIn)
            FROM salein_thuc_xuat
            WHERE YEAR(Date) IN ({placeholders})
            GROUP BY Organization, YEAR(Date)
            ORDER BY Organization, YEAR(Date)
        """, years)
        return [{"organization": r[0], "year": r[1], "total_salein": float(r[2])} for r in self.cursor.fetchall()]


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

def main():
    db = Database()
    
    db.create_tables()

    try:
        db.connect()

        print("\n📌 DISTINCT VALUES IN COLUMN:")
        regions = db.get_distinct_values("kpi_thuc_xuat", "region")
        print("Regions:", regions)

        print("\n📌 TOTAL KPI:")
        total_kpi = db.get_total("kpi_thuc_xuat", "kpi_score")
        print("Total KPI Score:", total_kpi)

        print("\n📌 RECORD COUNT:")
        row_count = db.get_count("salein_thuc_xuat")
        print("Rows in salein_thuc_xuat:", row_count)

        print("\n📌 TOTAL BY GROUP:")
        quantity_by_province = db.get_total_by_group("salein_thuc_xuat", "province", "quantity")
        print("Quantity by province:", quantity_by_province)

        print("\n📌 AVERAGE KPI BY REGION:")
        avg_kpi = db.get_avg_by_group("kpi_thuc_xuat", "region", "kpi_score")
        print("Avg KPI per region:", avg_kpi)

        print("\n📌 TOTAL BY MONTH:")
        total_monthly = db.get_total_by_month("salein_thuc_xuat", "date", "quantity")
        print("Monthly totals:", total_monthly)

        print("\n📌 EMPLOYEE TREND (test name in your dataset):")
        trend = db.get_entity_trend("salein_thuc_xuat", "employee_name", "Bảo Thế Nguyễn", "date", "quantity")
        print("Trend for 'Bảo Thế Nguyễn':", trend)

        print("\n📌 COMPARE PLAN VS ACTUAL:")
        comparison = db.compare_plan_vs_actual("salein_class", "salein_thuc_xuat", "product_name", "quantity")
        print("Plan vs Actual:", comparison)

        print("\n📌 MONTHLY GROWTH:")
        growth = db.get_monthly_growth("salein_thuc_xuat", "date", "quantity")
        print("Monthly Growth:", growth)

        print("\n📌 TOP EMPLOYEES BY KPI + QUANTITY:")
        top_employees = db.get_best_employees_by_score("kpi_thuc_xuat", "salein_thuc_xuat", top_n=5)
        print(json.dumps(top_employees, indent=4, ensure_ascii=False))

        print("\n📌 TOP PRODUCTS BY REGION + QUANTITY:")
        top_products = db.get_best_products_by_region("salein_thuc_xuat", top_n=5)
        print(json.dumps(top_products, indent=4, ensure_ascii=False))

        print("\n📌 DELIVERY BY REGION PER MONTH (BH1 - 2024):")
        delivery_stats = db.get_deliver_by_region_per_month(["TV01", "TV02", "TV03"], "BH1", 2024)
        print(json.dumps(delivery_stats, indent=4, ensure_ascii=False))

        print("\n📌 PLAN VS ACTUAL SAME DAY (1/2/2024):")
        plan_vs_actual = db.get_plan_vs_actual_same_day("2024-02-01", "BH1", ["TV01", "TV02", "TV03"])
        print(json.dumps(plan_vs_actual, indent=4, ensure_ascii=False))

        print("\n📌 COMPLETION RATE PER DEPARTMENT (2024):")
        completion_rate = db.get_completion_rate_by_department_per_month(2024)
        print(json.dumps(completion_rate, indent=4, ensure_ascii=False))

        print("\n📌 AVG KPI PER MONTH (2024):")
        avg_kpi_month = db.get_avg_kpi_by_month(2024)
        print(json.dumps(avg_kpi_month, indent=4, ensure_ascii=False))

        print("\n📌 COMPARE SALEIN BY REGION BY YEAR:")
        salein_years = db.get_salein_comparison_by_region_year([2023, 2024])
        print(json.dumps(salein_years, indent=4, ensure_ascii=False))

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()

