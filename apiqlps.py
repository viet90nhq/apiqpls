from flask import Flask, Response, request
from zeep import Client, helpers
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dotenv import load_dotenv
import os

# Load biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)

# URL của dịch vụ ASMX từ biến môi trường load từ biến .env
asmx_url = os.getenv('ASMX_URL')

# Tạo một client để gọi dịch vụ ASMX
client = Client(asmx_url)


def create_xml(_total_event_list, _service_id, _name):
    # Tạo phần tử gốc 'eit'
    root = ET.Element('eit')
    root.set('total-events', str(len(_total_event_list)))

    for i in range(len(_total_event_list)):

        str_event_id = ''
        str_serice_id = ''
        str_start_time_UTC = ''
        str_duration = ''
        str_name = ''
        str_short_description = ''

        # Láy event hiện tại
        event = _total_event_list[i]

        # event id = định dạng ngày tháng năm + (i)
        current_date = datetime.now()
        date_as_integer = int(current_date.strftime('%Y%m%d')) + (i)
        str_event_id = str(date_as_integer)

        # service id
        str_serice_id = str(_service_id)

        # COnvert start time
        start_time_BTKBT = event['Table']['TGBatDau']
        start_time_UTC = start_time_BTKBT.astimezone(timezone.utc)
        str_start_time_UTC = start_time_UTC.strftime('%Y-%m-%dT%H:%M:%SZ')
        # print(type(event['Table']['TGBatDau']))

        # Tính duration hơi khó
        #  Nếu chưa đến event cuối thì lấy event tiếp theo để lấy dữ liệu start time
        if i < len(_total_event_list) - 1:
            next_event = _total_event_list[i + 1]
            next_start_time_btkbt = next_event['Table']['TGBatDau']
            duration = next_start_time_btkbt - start_time_BTKBT
            str_duration = str(duration.total_seconds())
        #   Đến Event cuối thì start time được set là end time = 0h ngày tiếp theo
        else:
            end_time = (start_time_BTKBT + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            duration = end_time - start_time_BTKBT
            str_duration = str(duration.total_seconds())

            # print(start_time_BTKBT)
            # print(start_time_UTC)
            # print(end_time_UTC)
            # print(str_duration)
            # print(str_duration1)

        # name
        if _name == 'VTV8' or _name == 'VTV9':
            str_name = event['Table']['TenChuyenMucCB']
        else:
            str_name = event['Table']['TenChinhThuc']

        str_short_description = event['Table']['TenChuongTrinh']

        event_element = ET.SubElement(root, 'event')

        # Tạo và thêm phần tử 'id'
        id_element = ET.SubElement(event_element, 'id', attrib={
            'event-id': str_event_id,
            'service-id': str_serice_id
        })

        # Tạo phần tử 'info'
        info_element = ET.SubElement(event_element, 'info')
        ET.SubElement(info_element, 'start-time').text = str_start_time_UTC
        ET.SubElement(info_element, 'duration').text = str_duration
        ET.SubElement(info_element, 'content-type').text = '0'
        ET.SubElement(info_element, 'free-ca-mode').text = '0'

        # Tạo phần tử 'description'
        description_element = ET.SubElement(event_element, 'description')
        ET.SubElement(description_element, 'language-code').text = 'vie'
        ET.SubElement(description_element, 'name').text = str_name
        ET.SubElement(description_element, 'short-description').text = str_short_description
        ET.SubElement(description_element, 'long-description')

        # Tạo và thêm phần tử 'rating'
        ET.SubElement(event_element, 'rating', attrib={
            'country_code': '902',
            'rating': '0',
            'position': '0'
        })

    # Chuyển đổi cây phần tử thành một chuỗi XML
    xml_str = ET.tostring(root, encoding='utf-8')

    # Làm đẹp XML với minidom
    dom = minidom.parseString(xml_str)
    pretty_xml_as_string = dom.toprettyxml(indent="    ")

    # Thêm khai báo DOCTYPE
    doctype_str = '<!DOCTYPE eit SYSTEM "eit.dtd">'
    # Chuyển đổi thành chuỗi XML hoàn chỉnh
    xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    pretty_xml_as_string = xml_declaration + doctype_str + '\n' + ''.join(pretty_xml_as_string.split('\n', 1)[1:])

    return pretty_xml_as_string


@app.route('/api/query', methods=['GET'])
def get_data():
    param_kenh = request.args.get('kenh')
    param_serviceid = request.args.get('serviceid')
    param_songay = int(request.args.get('songay'))
    print(f'{param_kenh} , {param_serviceid} , {param_songay}')

    total_event_list = []

    for i in range(param_songay):
        current_day = datetime.now()
        get_day = current_day + timedelta(days=i)
        str_get_day = get_day.strftime('%d/%m/%Y')
        print(str_get_day)
        try:
            response = client.service.GetChuongtrinh(str_get_day, param_kenh)

            # kiem tra dieu kien xem response co du lieu hay ko. Khac '<Element' la co du lieu
            if str(response['_value_1'])[:8] != '<Element':
                data_dict = helpers.serialize_object(response)
                data_dict_length = len(data_dict['_value_1']['_value_1'])
                print(f'Số event ngày thứ {i + 1} là: {data_dict_length} event')
                total_event_list.extend(data_dict['_value_1']['_value_1'])

        except Exception as e:
            return Response(f"<error>{str(e)}</error>", mimetype='text/html')

    print(f'Tổng số event sau khi update: {len(total_event_list)}')

    xml_data = create_xml(total_event_list, param_serviceid, param_kenh)

    return Response(xml_data, mimetype='application/xml')



@app.route('/', methods=['GET'])
def hello():
    return 'Xin chao Viet'

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
