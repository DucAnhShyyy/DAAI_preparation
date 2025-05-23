from datetime import datetime
from langchain_community.tools import TavilySearchResults
from tools.sale_tools import (
    get_distinct_values_tool,
    get_total_tool,
    get_count_tool,
    get_total_by_group_tool,
    get_avg_by_group_tool,
    get_total_by_month_tool,
    get_entity_trend_tool,
    compare_plan_vs_actual_tool,
    get_monthly_growth_tool,
    get_best_employees_by_score_tool,
    get_best_products_by_region_tool,
    get_deliver_by_region_per_month_tool,
    get_plan_vs_actual_same_day_tool,
    get_completion_rate_by_department_per_month_tool,
    get_avg_kpi_by_month_tool,
    get_salein_comparison_by_region_year_tool,
)

def sale_system_prompt():
    today_date = datetime.now().strftime("%Y-%m-%d")
    return f"""
Bạn là chuyên gia phân tích dữ liệu vận hành nội bộ trong doanh nghiệp, có quyền truy cập vào dữ liệu KPI, sản lượng, và hoạt động thực tế tại các phòng ban. Khi trả lời:

1. QUAN TRỌNG: Luôn suy nghĩ theo các bước:
   - Bước 1: Phân tích để hiểu câu hỏi và xác định những thông tin cần thiết
   - Bước 2: Xác định công cụ cần gọi nếu thiếu dữ liệu
   - Bước 3: CHỈ TRẢ LỜI SAU KHI đã có đủ dữ liệu từ các công cụ

2. Nếu câu hỏi chưa rõ ràng, hãy hỏi lại để làm rõ.

3. Nếu dữ liệu chưa có trong lịch sử trò chuyện, hãy gọi tool phù hợp và CHỜ kết quả trước khi trả lời.

4. Với phân tích xu hướng hoặc so sánh (VD: "Ai làm tốt nhất?", "Xuất hàng tháng này tăng hay giảm?"), hãy sử dụng bảng và trình bày số liệu rõ ràng.

5. Với báo cáo dài, kết thúc bằng phần **# Kết luận** có tóm tắt nhanh và gạch ngang `---`.

6. Trả lời tiếng Việt, định dạng Markdown rõ ràng. Sử dụng bảng để trình bày kết quả dễ đọc.

7. Nếu có nhiều công cụ cần gọi, hãy gọi lần lượt, không đoán trước kết quả.

Ngày hôm nay là: {today_date}.
"""

SALE_TOOLS = [
    get_distinct_values_tool,
    get_total_tool,
    get_count_tool,
    get_total_by_group_tool,
    get_avg_by_group_tool,
    get_total_by_month_tool,
    get_entity_trend_tool,
    compare_plan_vs_actual_tool,
    get_monthly_growth_tool,
    get_best_employees_by_score_tool,
    get_best_products_by_region_tool,
    get_deliver_by_region_per_month_tool,
    get_plan_vs_actual_same_day_tool,
    get_completion_rate_by_department_per_month_tool,
    get_avg_kpi_by_month_tool,
    get_salein_comparison_by_region_year_tool,
    TavilySearchResults(max_results=3)
]

MAP_TOOLS_2_READABLE_NAME = {
    "get_distinct_values_tool": "Lấy danh sách giá trị duy nhất",
    "get_total_tool": "Tổng giá trị theo cột",
    "get_count_tool": "Đếm số dòng",
    "get_total_by_group_tool": "Tổng theo nhóm",
    "get_avg_by_group_tool": "Trung bình theo nhóm",
    "get_total_by_month_tool": "Tổng theo tháng",
    "get_entity_trend_tool": "Xu hướng theo thực thể",
    "compare_plan_vs_actual_tool": "So sánh kế hoạch và thực tế",
    "get_monthly_growth_tool": "Tăng trưởng hàng tháng",
    "get_best_employees_by_score_tool": "Top nhân viên theo điểm tổng hợp",
    "get_best_products_by_region_tool": "Top sản phẩm theo khu vực",
    "get_deliver_by_region_per_month_tool": "Tổng xuất theo khu vực và tháng",
    "get_plan_vs_actual_same_day_tool": "So sánh kế hoạch/thực tế cùng ngày",
    "get_completion_rate_by_department_per_month_tool": "Tỉ lệ hoàn thành theo phòng ban mỗi tháng",
    "get_avg_kpi_by_month_tool": "KPI trung bình theo tháng",
    "get_salein_comparison_by_region_year_tool": "So sánh SaleIn giữa các năm theo khu vực",
    "tavily_search_results_json": "Tìm kiếm thông tin"
}
