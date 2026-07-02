# messenger/soap_handler.py

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import xml.etree.ElementTree as ET
from .chat_manager import send_message, get_messages

# Пространства имён SOAP
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
SOAP_ENC = "http://schemas.xmlsoap.org/soap/encoding/"
TNS = "http://messenger.soap/"

def _build_soap_response(body_xml):
    """Обёртка ответа в SOAP Envelope"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        {body_xml}
    </soap:Body>
</soap:Envelope>'''

def _build_soap_fault(faultstring):
    """SOAP Fault"""
    return _build_soap_response(f'''
<soap:Fault>
    <faultcode>soap:Server</faultcode>
    <faultstring>{faultstring}</faultstring>
</soap:Fault>
''')

@csrf_exempt
def soap_view(request):
    if request.method != 'POST':
        return HttpResponse("SOAP endpoint requires POST", status=405)

    # Парсим XML
    try:
        tree = ET.fromstring(request.body)
    except ET.ParseError as e:
        return HttpResponse(_build_soap_fault(f"Invalid XML: {e}"), content_type="text/xml", status=400)

    # Находим элемент Body и его первый дочерний элемент (метод)
    body = tree.find(f'.//{{{SOAP_NS}}}Body')
    if body is None:
        return HttpResponse(_build_soap_fault("Missing SOAP Body"), content_type="text/xml", status=400)

    # Получаем первый элемент внутри Body – это вызов метода
    method_node = None
    for child in body:
        method_node = child
        break

    if method_node is None:
        return HttpResponse(_build_soap_fault("No method specified"), content_type="text/xml", status=400)

    # Имя метода (без namespace)
    method_name = method_node.tag.split('}')[-1] if '}' in method_node.tag else method_node.tag

    # Извлекаем параметры из дочерних элементов
    params = {}
    for param in method_node:
        param_name = param.tag.split('}')[-1] if '}' in param.tag else param.tag
        params[param_name] = param.text if param.text is not None else ""

    try:
        if method_name == 'SendMessage':
            chat_id = int(params.get('chat_id', 0))
            sender_id = int(params.get('sender_id', 0))
            text = params.get('text', '')
            if not chat_id or not sender_id:
                raise ValueError("chat_id and sender_id are required")
            result = send_message(chat_id, sender_id, text)
            response_body = f'<SendMessageResponse xmlns="{TNS}"><result>Message sent with id {result.id}</result></SendMessageResponse>'

        elif method_name == 'GetMessages':
            chat_id = int(params.get('chat_id', 0))
            limit = int(params.get('limit', 50))
            if not chat_id:
                raise ValueError("chat_id is required")
            messages = get_messages(chat_id, limit)
            # Формируем XML с массивом сообщений
            items = ''.join(
                f'<message><id>{m.id}</id><sender>{m.sender.username}</sender>'
                f'<text>{m.text}</text><timestamp>{m.timestamp.isoformat()}</timestamp></message>'
                for m in messages
            )
            response_body = f'<GetMessagesResponse xmlns="{TNS}">{items}</GetMessagesResponse>'

        else:
            return HttpResponse(_build_soap_fault(f"Unknown method: {method_name}"), content_type="text/xml", status=400)

        return HttpResponse(_build_soap_response(response_body), content_type="text/xml", status=200)

    except Exception as e:
        return HttpResponse(_build_soap_fault(str(e)), content_type="text/xml", status=500)