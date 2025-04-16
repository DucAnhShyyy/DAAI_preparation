from langchain_core.tools import tool
from database import Database
@tool
def get_industries_list() -> list[str]:
    """Get list of industries.
    Returns:
        list[dict]: List of industries with industry_code_lv2 and industry_name_lv2
        e.g: [{"industry_code_lv2": "1000", "industry_name_lv2": "Ngành nông nghiệp"},
              {"industry_code_lv2": "2000", "industry_name_lv2": "Ngành công nghiệp"}]
    """
    try:
        database = Database()
        industries = database.get_industries_list()
        return industries
    except Exception as e:
        return f"Error getting industries list: {e}"
    finally:
        database.close()

@tool
def get_symbols_by_industry(industry_code_lv2: str) -> list[str]:
    """Get list of symbols by industry.
    Args:
        industry_code_lv2 (str): Industry code of the industry
    """
    try:
        database = Database()
        symbols = database.get_symbols_by_industry(industry_code_lv2)
        return symbols
    except Exception as e:
        return f"Error getting symbols by industry: {e}"
    finally:
        database.close()

@tool
def get_financial_data(symbol: str, year: list[int] = None) -> dict:
    """Get financial data for a given symbol and year.
    Args:
        symbol (str): Symbol of the stock
        year (list[int]): List of years, if None, get all years
    """
    try:
        database = Database()
        financial_data = database.get_financial_data(symbol, year)
        return financial_data
    except Exception as e:
        return f"Error getting financial data: {e}"
    finally:
        database.close()

@tool
def get_best_stocks_by_industry(industry_code_lv2: str, num_stocks: int = 5) -> list[str]:
    """Get list of best stocks by industry.
    Args:
        industry_code_lv2 (str): Industry code of the industry
        num_stocks (int): Number of stocks to return
    Returns:
        list[str]: List of symbols
    """
    try:
        database = Database()
        symbols = database.get_best_stocks_by_industry(industry_code_lv2, num_stocks)
        return symbols
    except Exception as e:
        return f"Error getting best stocks by industry: {e}"
    finally:
        database.close()
