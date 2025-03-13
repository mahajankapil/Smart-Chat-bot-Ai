const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
sendBtn.addEventListener('click', () => {
    sendMessage();
});
userInput.addEventListener('keyup', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});
function sendMessage() {
    const userMessage = userInput.value.trim();
    if (userMessage === '') return;
    const question = "Placeholder Question"; // Replace with the actual question
    const data = {
        query: userMessage,
        question: question // Include the 'question' key
    };
    appendMessage('user', userMessage);
    userInput.value = '';
    fetch('/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(data => {
            console.log('data', data);
            const botMessage = data.answer.result;
            // console.log(botMessage);
            appendMessage('bot', botMessage);
        })
        .catch(error => console.error('Error:', error));
}
function convertURLsToLinks(inputText) {
    // Regular expression pattern to match URLs
    var urlPattern = /(\bhttps?:\/\/\S+)/gi;
    // Replace URLs with anchor tags with custom href and text
    return inputText.replace(urlPattern, function(match) {
        return '<a href="' + match + '" target="_blank">' + match + '</a>';
    });
}
function appendMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('chat-message');
    if (sender === 'user') {
        messageElement.classList.add('user-message');
    } else if (sender === 'bot') {
        messageElement.classList.add('bot-message');
    }
    message = convertURLsToLinks(message);
    messageElement.innerHTML = `<p>${message}</p>`;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}