from flask import Blueprint, request, jsonify
from ..services.chatbot_service import get_chatbot_response
from ..services.auth_service import is_customer
# import asyncio # Ya no es necesario

bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

@bp.route('/message', methods=['POST'])
def message():
    if not is_customer():
        return jsonify({'error': 'Debes iniciar sesión para usar el chat.'}), 403

    data = request.get_json()
    user_message = data.get('message')
    chat_history = data.get('history', [])

    if not user_message:
        return jsonify({'error': 'Mensaje vacío.'}), 400

    # La llamada ahora es directa, sin asyncio
    bot_response = get_chatbot_response(user_message, chat_history)

    return jsonify({'response': bot_response})
