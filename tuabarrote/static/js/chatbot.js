document.addEventListener('DOMContentLoaded', () => {
    const chatbotToggleButton = document.getElementById('chatbot-toggle-button');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeChatbotButton = document.getElementById('close-chatbot');
    const chatbotForm = document.getElementById('chatbot-form');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatBody = document.getElementById('chat-body');
    const suggestionChipsContainer = document.getElementById('suggestion-chips');

    if (!chatbotToggleButton) return;

    let chatHistory = [];
    const initialSuggestions = [
        'Dirección de la tienda',
        'Número de contacto',
        'Dame una sugerencia'
    ];

    const addMessageToUI = (sender, message) => {
        const messageContainer = document.createElement('div');
        messageContainer.className = `chat-message ${sender}`;
        
        let messageContent = '';
        if (sender === 'bot') {
            messageContent = `<div class="avatar"></div>`;
        }
        messageContent += `<p>${message}</p>`;

        messageContainer.innerHTML = messageContent;
        chatBody.insertBefore(messageContainer, suggestionChipsContainer);
        chatBody.scrollTop = chatBody.scrollHeight;
    };

    const showTypingIndicator = () => {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chat-message bot';
        typingDiv.innerHTML = `<div class="avatar"></div><p>Escribiendo...</p>`;
        chatBody.insertBefore(typingDiv, suggestionChipsContainer);
        chatBody.scrollTop = chatBody.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    };

    const displaySuggestionChips = (suggestions) => {
        suggestionChipsContainer.innerHTML = '';
        suggestions.forEach(text => {
            const chip = document.createElement('button');
            chip.className = 'suggestion-chip';
            chip.textContent = text;
            suggestionChipsContainer.appendChild(chip);
        });
        suggestionChipsContainer.style.display = 'flex';
    };

    const sendMessage = async (message) => {
        if (message.trim() === '') return;

        addMessageToUI('user', message);
        chatHistory.push({ sender: 'user', text: message });
        
        suggestionChipsContainer.style.display = 'none';
        showTypingIndicator();

        try {
            const response = await fetch('/chatbot/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, history: chatHistory })
            });

            removeTypingIndicator();
            if (!response.ok) {
                addMessageToUI('bot', 'Lo siento, hubo un error de conexión.');
                return;
            }

            const data = await response.json();
            const botMessage = data.response;
            addMessageToUI('bot', botMessage);
            chatHistory.push({ sender: 'bot', text: botMessage });

        } catch (error) {
            removeTypingIndicator();
            console.error('Error en el chatbot:', error);
            addMessageToUI('bot', 'No pude procesar tu solicitud en este momento.');
        }
    };

    chatbotForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const userMessage = chatbotInput.value;
        sendMessage(userMessage);
        chatbotInput.value = '';
    });

    suggestionChipsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('suggestion-chip')) {
            const message = e.target.textContent;
            sendMessage(message);
        }
    });

    const toggleChatWindow = () => {
        chatbotWindow.classList.toggle('hidden');
        if (!chatbotWindow.classList.contains('hidden')) {
            displaySuggestionChips(initialSuggestions);
            chatbotInput.focus();
        }
    };

    chatbotToggleButton.addEventListener('click', toggleChatWindow);
    closeChatbotButton.addEventListener('click', toggleChatWindow);
    
    // Mostrar sugerencias al inicio
    displaySuggestionChips(initialSuggestions);
});