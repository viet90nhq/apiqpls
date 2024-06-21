from datetime import datetime, timezone

# múi giờ +7 từ API ban TKBT
time_str1 = '2024-06-06T15:30:00+07:00'
time_str2 = '2024-06-06T16:30:00+07:00'
# chuyển string thành định dạng datetime để tính toán
dt1 = datetime.fromisoformat(time_str1)
dt2 = datetime.fromisoformat(time_str2)
#
dt_utc = dt1.astimezone(timezone.utc)
time_str_utc = dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

duration = dt2 - dt1

print(f'duration = {duration.total_seconds()} giây')
print(f'thời gian theo chuẩn UTC là: {time_str_utc}')

