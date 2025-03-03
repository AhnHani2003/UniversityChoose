import os
from prophet import Prophet
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Tạo thư mục nếu chưa tồn tại
os.makedirs('./data/generate', exist_ok=True)
os.makedirs('./static', exist_ok=True)

# 1. Load dữ liệu
file_path = "./data/Rounded_Top_20_Industries_VN_2019_2024.xlsx"
data = pd.read_excel(file_path)

# 2. Chuẩn bị dữ liệu
data_melted = data.melt(id_vars=["nganh_nghe"], var_name="nam", value_name="so_luong_tuyen_dung")
data_melted["nam"] = data_melted["nam"].astype(int)
data_melted["ds"] = pd.to_datetime(data_melted["nam"], format='%Y')
data_melted = data_melted.rename(columns={"so_luong_tuyen_dung": "y"})

# Kiểm tra dữ liệu
print("Số lượng dữ liệu lịch sử theo từng ngành:")
print(data_melted.groupby('nganh_nghe').count())

# 3. Dự báo với Prophet
future_predictions = []
skipped_industries = []

for nganh in data_melted["nganh_nghe"].unique():
    nganh_data = data_melted[data_melted["nganh_nghe"] == nganh][["ds", "y"]]
    
    if nganh_data.empty:
        skipped_industries.append(nganh)
        continue
    
    try:
        # Khởi tạo mô hình Prophet
        model = Prophet(
            yearly_seasonality=True,
            seasonality_prior_scale=10,
            changepoint_prior_scale=0.05
        )
        model.fit(nganh_data)
        
        # Dự báo 6 năm tới để đảm bảo đủ 2025–2028
        future = model.make_future_dataframe(periods=6, freq='YE')
        forecast = model.predict(future)
        
        # Lọc dữ liệu từ 2025–2028
        forecast = forecast[(forecast["ds"].dt.year >= 2025) & (forecast["ds"].dt.year <= 2028)]
        
        if len(forecast) < 4:
            print(f"⚠️ Không đủ dữ liệu cho các năm 2025–2028 của ngành {nganh}. Sử dụng giá trị gần nhất.")
            last_value = nganh_data["y"].iloc[-1] if not nganh_data.empty else 0
            for year in range(2025, 2029):
                forecast = forecast.append({
                    "ds": pd.Timestamp(f"{year}-12-31"),
                    "yhat": last_value,
                    "nganh_nghe": nganh
                }, ignore_index=True)
        
        forecast["nganh_nghe"] = nganh
        future_predictions.append(forecast[["ds", "yhat", "nganh_nghe"]])
    except Exception as e:
        print(f"Lỗi dự báo ngành {nganh}: {e}")
        skipped_industries.append(nganh)

# Kết hợp dữ liệu dự báo
if future_predictions:
    forecast_df = pd.concat(future_predictions)
else:
    raise ValueError("Không có dữ liệu dự báo hợp lệ.")

# 4. Tạo bảng số liệu nhu cầu hàng năm (2025–2028)
annual_demand_data = []
for nganh in forecast_df["nganh_nghe"].unique():
    subset = forecast_df[forecast_df["nganh_nghe"] == nganh]
    yearly_data = {
        "nganh_nghe": nganh,
        "2025": round(subset[subset["ds"].dt.year == 2025]["yhat"].values[0], -2) if len(subset[subset["ds"].dt.year == 2025]) > 0 else None,
        "2026": round(subset[subset["ds"].dt.year == 2026]["yhat"].values[0], -2) if len(subset[subset["ds"].dt.year == 2026]) > 0 else None,
        "2027": round(subset[subset["ds"].dt.year == 2027]["yhat"].values[0], -2) if len(subset[subset["ds"].dt.year == 2027]) > 0 else None,
        "2028": round(subset[subset["ds"].dt.year == 2028]["yhat"].values[0], -2) if len(subset[subset["ds"].dt.year == 2028]) > 0 else None,
    }
    annual_demand_data.append(yearly_data)

annual_demand_df = pd.DataFrame(annual_demand_data)
annual_demand_file = "./data/generate/bang_so_lieu_nhu_cau_2025_2028.xlsx"
annual_demand_df.to_excel(annual_demand_file, index=False)

# 5. Tính toán AAGR (2025–2028)
adjusted_growth_data = []

for nganh in forecast_df["nganh_nghe"].unique():
    subset = forecast_df[forecast_df["nganh_nghe"] == nganh].sort_values(by="ds")
    
    values = subset[subset["ds"].dt.year.isin([2025, 2026, 2027, 2028])]["yhat"].values
    
    if len(values) < 4:
        print(f"⚠️ Không đủ dữ liệu để tính AAGR cho ngành {nganh}.")
        adjusted_growth_data.append({
            "nganh_nghe": nganh,
            "2025": None,
            "2028": None,
            "AAGR (%)": None
        })
        continue
    
    try:
        agr_values = [(values[i] / values[i-1] - 1) for i in range(1, len(values))]
        aagr = (sum(agr_values) / len(agr_values)) * 100
    except ZeroDivisionError:
        aagr = 0
    
    adjusted_growth_data.append({
        "nganh_nghe": nganh,
        "2025": round(values[0], -2),
        "2028": round(values[-1], -2),
        "AAGR (%)": round(aagr, 2)
    })

# Xuất bảng xếp hạng AAGR
adjusted_ranking_df = pd.DataFrame(adjusted_growth_data).sort_values(by="AAGR (%)", ascending=False)
adjusted_ranking_file = "./data/generate/bang_xep_hang_nganh_nghe_AAGR_2025_2028.xlsx"
adjusted_ranking_df.to_excel(adjusted_ranking_file, index=False)

print(f"Bảng xếp hạng AAGR đã lưu: {adjusted_ranking_file}")

# 6. Vẽ biểu đồ
plt.figure(figsize=(14, 8))
for nganh in forecast_df["nganh_nghe"].unique():
    subset = forecast_df[forecast_df["nganh_nghe"] == nganh]
    plt.plot(subset["ds"].dt.year, subset["yhat"], label=nganh)

plt.title("Dự báo số lượng tuyển dụng và AAGR (2025–2028)")
plt.xlabel("Năm")
plt.ylabel("Số lượng tuyển dụng dự báo")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
chart_path = "./data/generate/du_bao_AAGR_2025_2028.png"
plt.savefig(chart_path)
plt.show()

print(f"Bảng số liệu đã lưu: {annual_demand_file}")
print(f"Bảng xếp hạng đã lưu: {adjusted_ranking_file}")
