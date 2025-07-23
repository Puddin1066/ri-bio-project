// Chat functionality
let isWaitingForResponse = false;

// Initialize the chat
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    
    // Handle Enter key press
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Focus on input
    messageInput.focus();
});

// Send message function
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || isWaitingForResponse) return;
    
    // Clear input and hide suggested queries
    messageInput.value = '';
    hideSuggestedQueries();
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Show loading indicator
    showLoading();
    isWaitingForResponse = true;
    
    try {
        // Send message to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                timestamp: new Date().toISOString()
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide loading and add bot response
        hideLoading();
        addMessage(data.response, 'bot', data.data);
        
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        addMessage('Sorry, I encountered an error while processing your request. Please try again.', 'bot', null, true);
    } finally {
        isWaitingForResponse = false;
    }
}

// Send suggested query
function sendSuggestedQuery(query) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = query;
    sendMessage();
}

// Add message to chat
function addMessage(text, sender, data = null, isError = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (isError) {
        messageDiv.classList.add('error-message');
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    
    // Process message text for data visualization
    if (data && data.type === 'table') {
        messageText.innerHTML = text + formatDataTable(data.content);
    } else if (data && data.type === 'metrics') {
        messageText.innerHTML = text + formatMetrics(data.content);
    } else {
        messageText.innerHTML = formatMessageText(text);
    }
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-time';
    timestamp.textContent = new Date().toLocaleTimeString();
    
    content.appendChild(messageText);
    content.appendChild(timestamp);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message text with basic HTML support
function formatMessageText(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

// Format data as table
function formatDataTable(tableData) {
    if (!tableData || !tableData.headers || !tableData.rows) return '';
    
    let html = '<table class="data-table">';
    
    // Headers
    html += '<thead><tr>';
    tableData.headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead>';
    
    // Rows
    html += '<tbody>';
    tableData.rows.forEach(row => {
        html += '<tr>';
        row.forEach(cell => {
            html += `<td>${cell}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    
    return html;
}

// Format metrics cards
function formatMetrics(metrics) {
    if (!metrics || !Array.isArray(metrics)) return '';
    
    let html = '<div class="metrics-container">';
    
    metrics.forEach(metric => {
        html += `
            <div class="metric-card">
                <h4>${metric.label}</h4>
                <div class="metric-value">${metric.value}</div>
                ${metric.change ? `<div class="metric-change">${metric.change}</div>` : ''}
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// Show loading indicator
function showLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const sendButton = document.getElementById('sendButton');
    
    loadingIndicator.classList.add('show');
    sendButton.disabled = true;
}

// Hide loading indicator
function hideLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const sendButton = document.getElementById('sendButton');
    
    loadingIndicator.classList.remove('show');
    sendButton.disabled = false;
}

// Hide suggested queries
function hideSuggestedQueries() {
    const suggestedQueries = document.getElementById('suggestedQueries');
    if (suggestedQueries) {
        suggestedQueries.style.display = 'none';
    }
}

// Auto-resize chat messages area
function resizeChatArea() {
    const chatMessages = document.getElementById('chatMessages');
    const container = document.querySelector('.chat-container');
    const header = document.querySelector('.chat-header');
    const input = document.querySelector('.chat-input-container');
    const suggested = document.getElementById('suggestedQueries');
    
    let availableHeight = container.clientHeight - header.clientHeight - input.clientHeight;
    
    if (suggested && suggested.style.display !== 'none') {
        availableHeight -= suggested.clientHeight;
    }
    
    chatMessages.style.height = availableHeight + 'px';
}

// Handle window resize
window.addEventListener('resize', resizeChatArea);

// Initialize chat area size
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(resizeChatArea, 100);
});

// Utility functions for data processing
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Export functions for use in other modules
window.chatUI = {
    sendMessage,
    sendSuggestedQuery,
    addMessage,
    formatCurrency,
    formatNumber,
    formatDate
};