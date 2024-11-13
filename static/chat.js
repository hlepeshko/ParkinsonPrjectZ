// Handle connection errors
socket.on('connect_error', (err) => {
    console.error('Connection error:', err);
});

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const username = "{{ username }}"; // Get the username from the template

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const message = input.value.trim(); // Trim whitespace

        // Prevent sending empty messages
        if (message === '') return;

        console.log(`Sending message: ${message}`); // Debugging log
        socket.emit('send_message', { message: message, username: username }); // Send message with username
        input.value = ''; // Clear input field
    });

    socket.on('receive_message', function(data) {
        const messageElement = document.createElement('div');
        messageElement.textContent = `${data.username}: ${data.message}`; // Display received message
        messageElement.classList.add('chat-message'); // Add class for styling
        chatMessages.appendChild(messageElement);const socket = io.connect('http://127.0.0.1:5000');
    });

    // Handle disconnections
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });

    // Handle reconnections
    socket.on('reconnect', (attemptNumber) => {
        console.log(`Reconnected after ${attemptNumber} attempts`);
    });
});
