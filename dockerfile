# Sử dụng Python chính thức làm base image
FROM python:3.11

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file yêu cầu để cài đặt các dependency
COPY requirements.txt .

# Cài đặt các gói yêu cầu
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào trong container
COPY . .

# Thiết lập biến môi trường (nếu cần)
ENV PYTHONUNBUFFERED=1

# Mở các cổng mà ứng dụng sẽ sử dụng
EXPOSE 8000 8501

# Lệnh để chạy ứng dụng - Chạy FastAPI với Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
