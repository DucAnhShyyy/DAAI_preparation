import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("vi_VN")

# Các field được dùng chung giữa nhiều bảng
COMMON_FIELDS = ["Date", "Employee_Name", "product_name"]

def random_date(start_date, end_date):
    return start_date + timedelta(days=random.randint(0, (end_date - start_date).days))

def random_code(length=6):
    return ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=random.randint(5, length)))

def generate_common_row():
    return {
        "Date": random_date(datetime(2024, 1, 1), datetime(2024, 4, 10)).strftime("%Y-%m-%d"),
        "Employee_Name": fake.name(),
        "product_name": random.choice(["đèn LED tròn", "đèn bàn học", "đèn LED âm trần", "đèn cảm ứng"])
    }

def generate_full_row(field_names, common_data):
    row = {}
    for field in field_names:
        f_lower = field.lower()

        # Ưu tiên dùng dữ liệu chung
        if field in common_data:
            row[field] = common_data[field]
        elif "department" in f_lower or "phòng" in f_lower:
            row[field] = random.choice(["phòng kinh doanh", "phòng kỹ thuật", "phòng nhân sự", "phòng R&D"])
        elif "unit" in f_lower or "đơn vị" in f_lower:
            row[field] = random.choice(["công ty TNHH ABC", "công ty cổ phần XYZ", "công ty TNHH Một Thành Viên 123"])
        elif "province" in f_lower or "tỉnh" in f_lower:
            row[field] = random.choice(["Hà Nội", "TP Hồ Chí Minh", "Đà Nẵng", "Cần Thơ"])
        elif "region" in f_lower or "vùng" in f_lower:
            row[field] = random.choice(["miền Bắc", "miền Trung", "miền Nam"])
        elif "code" in f_lower:
            row[field] = random_code()
        elif "số lượng" in f_lower:
            row[field] = random.randint(1, 100)
        elif "số" in f_lower:
            row[field] = random.randint(1, 1000)
        else:
            row[field] = fake.word()
    return row

def generate_data_with_consistency(field_names_dict, row_count=2000):
    data = {table: [] for table in field_names_dict}

    for _ in range(row_count):
        common_row = generate_common_row()
        for table, fields in field_names_dict.items():
            full_row = generate_full_row(fields, common_row)
            data[table].append(full_row)

    return {table: pd.DataFrame(rows) for table, rows in data.items()}

# 🎯 Khai báo các fields cho từng bảng (lấy từ Excel nếu muốn)
fields_salein_class = ["Date", "Employee_Name", "Department", "item_code", "product_name", "Số lượng"]
fields_salein_thuc_xuat = ["Date", "Employee_Name", "unit_code", "product_name", "Số lượng xuất", "province"]
fields_kpi_thuc_xuat = ["Date", "Employee_Name", "KPI_code", "region", "product_name", "Số KPI"]

# Tạo dữ liệu
field_map = {
    "salein_class": fields_salein_class,
    "salein_thuc_xuat": fields_salein_thuc_xuat,
    "kpi_thuc_xuat": fields_kpi_thuc_xuat
}

df_map = generate_data_with_consistency(field_map)

# Xuất ra file CSV
for table_name, df in df_map.items():
    df.to_csv(f"{table_name}.csv", index=False, encoding='utf-8-sig')

print("✅ Hoàn tất sinh dữ liệu! Các file CSV đã được tạo.")
