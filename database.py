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
            
#     def get_industries_list(self) -> list[dict]:
#         """Get list of industries.
#         Returns:
#             list[dict]: List of industries with industry_code_lv2 and industry_name_lv2
#             e.g: [{"industry_code_lv2": "1000", "industry_name_lv2": "Ngành nông nghiệp"},
#                   {"industry_code_lv2": "2000", "industry_name_lv2": "Ngành công nghiệp"}]
#         """
#         self.cursor.execute("""
#             SELECT DISTINCT industry_code_lv2, industry_name_lv2 FROM vn100_listing_by_industry
#         """)
#         results = self.cursor.fetchall()
#         return [{"industry_code_lv2": row[0], "industry_name_lv2": row[1]} for row in results]

#     def get_symbols_by_industry(self, industry_code_lv2: str) -> list[str]:
#         """Get list of symbols by industry.
#         Args:
#             industry_code_lv2 (str): Industry code of the industry
#         Returns:
#             list[str]: List of symbols
#             e.g: ["VCB", "BID", "CTG"]
#         """
#         self.cursor.execute("""
#             SELECT symbol FROM vn100_listing_by_industry WHERE industry_code_lv2 = %s
#         """, (industry_code_lv2,))
#         return [row[0] for row in self.cursor.fetchall()]
    
#     def get_financial_data(self, symbol: str) -> pd.DataFrame:
#         """Get financial data by symbol: income statement, balance sheet, cash flow statement and yearly stock price
#         Pay attention to percentage values, they may be stored as decimal values (e.g: 15% is stored as 0.15)
#         Args:
#             symbol (str): Symbol of the company
#         Returns:
#             dataframe: Financial data
#         """
#         self.cursor.execute("""
#             SELECT * FROM financial_data WHERE symbol = %s
#         """, (symbol,))
#         results = self.cursor.fetchall()
#         df = pd.DataFrame(results, columns=[i[0] for i in self.cursor.description])
#         # remove id column
#         df = df.drop(columns=['id'])
#         return df


#     def get_best_symbols_by_industry(self, industry_code_lv2: str, num_stocks: int = 5, missing_threshold: float = 0.5) -> List[str]:
#         """
#         Get list of best stocks by industry based on a composite score.
        
#         Handles missing values by using median imputation and removes metrics with excessive missing data.
        
#         Args:
#             industry_code_lv2 (str): Industry code of the industry
#             num_stocks (int): Number of stocks to return
#             missing_threshold (float): Threshold for missing data ratio to exclude a metric (0 to 1)
#         Returns:
#             list[str]: List of symbols
#         """
#         try:
#             # Get symbols for the industry
#             symbols = self.get_symbols_by_industry(industry_code_lv2)
#             if not symbols:
#                 return []

#             quoted_symbols = [f"'{symbol}'" for symbol in symbols]

#             # Define the metrics and their directions
#             metrics = {
#                 'return_on_equity_percent': 'higher',
#                 'net_profit_margin_percent': 'higher',
#                 'revenue_growth_percent': 'higher',
#                 'debt_to_equity': 'lower',
#                 'total_volume': 'higher'
#             }

#             # Query the financial data - only get the latest year for each symbol
#             query = f"""
#                 SELECT f1.symbol, f1.return_on_equity_percent, f1.net_profit_margin_percent, 
#                     f1.revenue_growth_percent, f1.total_liabilities_billion_vnd, f1.owner_equity_billion_vnd,
#                     f1.yearly_close_price_vnd, f1.yearly_volume, f1.year_report
#                 FROM financial_data f1
#                 INNER JOIN (
#                     SELECT symbol, MAX(year_report) as max_year
#                     FROM financial_data
#                     WHERE symbol IN ({', '.join(quoted_symbols)})
#                     GROUP BY symbol
#                 ) f2 ON f1.symbol = f2.symbol AND f1.year_report = f2.max_year
#             """

#             self.cursor.execute(query)
#             results = self.cursor.fetchall()
#             if not results:
#                 return []

#             # Convert results to a list of dictionaries
#             columns = ['symbol', 'return_on_equity_percent', 'net_profit_margin_percent', 
#                     'revenue_growth_percent', 'total_liabilities_billion_vnd', 'owner_equity_billion_vnd',
#                     'yearly_close_price_vnd', 'yearly_volume', 'year_report']
#             data = []
#             for row in results:
#                 converted_row = [float(val) if isinstance(val, decimal.Decimal) else val for val in row]
#                 company_data = dict(zip(columns, converted_row))
#                 data.append(company_data)

#             # Calculate derived metrics
#             for company in data:
#                 total_liabilities = company['total_liabilities_billion_vnd']
#                 owner_equity = company['owner_equity_billion_vnd']
#                 company['debt_to_equity'] = total_liabilities / owner_equity if owner_equity and owner_equity != 0 and total_liabilities is not None else None

#                 price = company['yearly_close_price_vnd']
#                 volume = company['yearly_volume']
#                 company['total_volume'] = price * volume if price is not None and volume is not None else None

#             # Step 1: Check missing data ratio and filter metrics
#             valid_metrics = {}
#             for metric in metrics:
#                 values = [c.get(metric) for c in data if c.get(metric) is not None]
#                 missing_ratio = 1 - len(values) / len(data) if data else 1
#                 if missing_ratio <= missing_threshold:
#                     valid_metrics[metric] = metrics[metric]
#                 else:
#                     print(f"Warning: Metric {metric} has {missing_ratio:.2%} missing values, excluded from scoring.")
#             if not valid_metrics:
#                 return []

#             # Step 2: Calculate statistics and impute missing values with median
#             metric_stats: Dict[str, tuple] = {}
#             for metric in valid_metrics:
#                 values = [c.get(metric) for c in data if c.get(metric) is not None]
#                 if values:
#                     min_val = min(values)
#                     max_val = max(values)
#                     median_val = np.median(values)
#                     variance = np.var(values) if len(values) > 1 else 0
#                     metric_stats[metric] = (min_val, max_val, median_val, variance)
#                 else:
#                     metric_stats[metric] = (0, 1, 0.5, 0)  # Default if no data

#             # Step 3: Adjust weights based on variance
#             total_variance = sum(stats[3] for stats in metric_stats.values())
#             metric_weights = {
#                 metric: stats[3] / total_variance if total_variance > 0 else 1 / len(valid_metrics)
#                 for metric, stats in metric_stats.items()
#             }
#             weight_sum = sum(metric_weights.values())
#             if weight_sum > 0:
#                 metric_weights = {k: v / weight_sum for k, v in metric_weights.items()}

#             # Step 4: Handle outliers for debt_to_equity
#             debt_values = [c.get('debt_to_equity') for c in data if c.get('debt_to_equity') is not None]
#             if debt_values:
#                 debt_p75 = np.percentile(debt_values, 75)
#                 for company in data:
#                     debt = company.get('debt_to_equity')
#                     if debt is not None and debt > debt_p75 * 1.5:
#                         company['debt_to_equity_adjusted'] = max(0, 1 - (debt - debt_p75) / debt_p75)
#                     else:
#                         company['debt_to_equity_adjusted'] = 1.0 if debt is not None else None

#             # Step 5: Normalize and calculate scores
#             for company in data:
#                 company_score = 0
#                 total_weight = 0
#                 for metric in valid_metrics:
#                     value = company.get(metric if metric != 'debt_to_equity' else 'debt_to_equity_adjusted')
#                     if value is None:
#                         # Impute with median normalized value
#                         _, _, median_val, _ = metric_stats[metric]
#                         min_val, max_val, _, _ = metric_stats[metric]
#                         if max_val == min_val:
#                             company[f"{metric}_normalized"] = 1.0
#                         else:
#                             if valid_metrics[metric] == 'higher':
#                                 company[f"{metric}_normalized"] = (median_val - min_val) / (max_val - min_val)
#                             else:
#                                 company[f"{metric}_normalized"] = (max_val - median_val) / (max_val - min_val)
#                     else:
#                         min_val, max_val, _, _ = metric_stats[metric]
#                         if max_val == min_val:
#                             company[f"{metric}_normalized"] = 1.0
#                         else:
#                             if valid_metrics[metric] == 'higher':
#                                 company[f"{metric}_normalized"] = (value - min_val) / (max_val - min_val)
#                             else:
#                                 company[f"{metric}_normalized"] = (max_val - value) / (max_val - min_val)

#                     normalized_value = company[f"{metric}_normalized"]
#                     weight = metric_weights[metric]
#                     company_score += normalized_value * weight
#                     total_weight += weight

#                 company['composite_score'] = company_score / total_weight if total_weight > 0 else 0

#             # Step 6: Sort and return top companies
#             sorted_companies = sorted(data, key=lambda x: x.get('composite_score', 0), reverse=True)

#             # Debug output
#             print(f"\nTop {num_stocks} companies in industry {industry_code_lv2}:")
#             for i, company in enumerate(sorted_companies[:num_stocks]):
#                 print(f"{i+1}. {company['symbol']} (Year: {company['year_report']}) - Score: {company['composite_score']:.2f}")
#                 for metric in valid_metrics:
#                     print(f"   {metric}: {company.get(metric):.2f}, Normalized: {company.get(f'{metric}_normalized'):.2f}, Weight: {metric_weights[metric]:.2f}")
#                 print()

#             return [company['symbol'] for company in sorted_companies[:num_stocks]]

#         except Error as e:
#             print(f"Error getting best stocks by industry: {e}")
#             return []

# @tool
# def get_financial_data_tool(symbol: str) -> str:
#     """Get financial data by symbol: income statement, balance sheet, cash flow statement and yearly stock price
#     Pay attention to percentage values, they may be stored as decimal values (e.g: 15% is stored as 0.15)
#     Args:
#         symbol (str): Symbol of the company
#     Returns:
#         str: a string representation of the financial data in csv format
#     """
#     try:
#         db = Database()
#         db.connect()
#         financial_data = db.get_financial_data(symbol)
#         return financial_data.to_csv(index=False)
#     except Error as e:
#         print(f"Error getting financial data: {e}")
#         return "Error getting financial data"
#     finally:
#         db.close()

# @tool
# def get_industries_list_tool() -> list[dict]:
#     """Get list of industries.
#     Pay attention that the input industry name may be not the exact name, try to find the matched industry name in the list
#     Returns:
#         list[dict]: List of industries with industry_code_lv2 and industry_name_lv2
#         e.g: [{"industry_code_lv2": "1000", "industry_name_lv2": "Ngành nông nghiệp"},
#               {"industry_code_lv2": "2000", "industry_name_lv2": "Ngành công nghiệp"}]
#     """
#     try:
#         db = Database()
#         db.connect()
#         industries = db.get_industries_list()
#         return industries
#     except Error as e:
#         print(f"Error getting industries list: {e}")
#         return []
#     finally:
#         db.close()

# @tool
# def get_symbols_by_industry_tool(industry_code_lv2: str) -> list[str]:
#     """Get list of symbols by industry.
#     Args:
#         industry_code_lv2 (str): Industry code of the industry
#     Returns:
#         list[str]: List of symbols
#         e.g: ["VCB", "BID", "CTG"]
#     """
#     try:
#         db = Database()
#         db.connect()
#         symbols = db.get_symbols_by_industry(industry_code_lv2)
#         return symbols
#     except Error as e:
#         print(f"Error getting symbols by industry: {e}")
#         return []
#     finally:
#         db.close()

# @tool
# def get_all_symbols_tool() -> list[str]:
#     """Get list of all symbols in the database.
#     Returns:
#         list[str]: List of all symbols
#         e.g: ["VCB", "BID", "CTG", ...]
#     """
#     try:
#         db = Database()
#         db.connect()
#         db.cursor.execute("SELECT symbol FROM vn100_listing")
#         symbols = [row[0] for row in db.cursor.fetchall()]
#         return symbols
#     except Error as e:
#         print(f"Error getting all symbols: {e}")
#         return []
#     finally:
#         db.close()

# @tool
# def get_company_info_tool(symbol: str) -> dict:
#     """Get company information by symbol.
#     Args:
#         symbol (str): Symbol of the company
#     Returns:
#         dict: Company information including industry and organization name
#     """
#     try:
#         db = Database()
#         db.connect()
#         db.cursor.execute("""
#             SELECT symbol, organ_name, industry_name_lv2, industry_code_lv2 
#             FROM vn100_listing_by_industry 
#             WHERE symbol = %s
#         """, (symbol,))
#         result = db.cursor.fetchone()
#         if result:
#             return {
#                 "symbol": result[0],
#                 "organ_name": result[1],
#                 "industry_name_lv2": result[2],
#                 "industry_code_lv2": result[3]
#             }
#         return {}
#     except Error as e:
#         print(f"Error getting company info: {e}")
#         return {}
#     finally:
#         db.close()

# @tool
# def get_best_symbols_by_industry_tool(industry_code_lv2: str, num_stocks: int = 5) -> list[str]:
#     """Get list of best stocks by industry based on a composite score, with 50% weight on total trading volume (price * volume).
#     Args:
#         industry_code_lv2 (str): Industry code of the industry
#         num_stocks (int): Number of stocks to return
#     Returns:
#         list[str]: List of symbols
#     """
#     try:
#         db = Database()
#         db.connect()
#         return db.get_best_symbols_by_industry(industry_code_lv2, num_stocks)
#     except Error as e:
#         print(f"Error getting best stocks by industry: {e}")
#         return []
#     finally:
#         db.close()

def main():
    # Create tables and insert data into the database
    db = Database()
    db.create_tables()  

    try:
        db.connect()
        
        # Check if the tables have been created by querying the table information
        print("\n==============================================\n")
        print("List of tables in the database:")
        db.cursor.execute("SHOW TABLES")
        tables = db.cursor.fetchall()
        for table in tables:
            print(table[0])  
        
        # Check if data has been inserted into the tables (check with the salein_class table)
        print("\n==============================================\n")
        print("Checking data in the salein_class table:")
        db.cursor.execute("SELECT * FROM salein_class LIMIT 5")
        data = db.cursor.fetchall()
        for row in data:
            print(row)

    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
