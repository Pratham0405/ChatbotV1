document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Add a welcome message when the page loads
    addBotMessage("Hello! How can I help you today?");
    
    // Send message when button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Send message when Enter key is pressed
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addUserMessage(message);
            userInput.value = '';
            
            // Call your API here
            fetchChatAPI(message).then(response => {
                addBotMessage(response);
            }).catch(error => {
                addBotMessage("Sorry, I'm having trouble connecting right now.");
                console.error('Error:', error);
            });
        }
    }
    
    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addBotMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Replace this with your actual API call
    async function fetchChatAPI(message) {
    try {
        const response = await fetch('https://chatbotv1-1.onrender.com/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_message: message })  // ✅ Must match FastAPI input
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const data = await response.json();
        return data; // Your API directly returns the bot message string
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

});
