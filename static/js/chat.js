
class ChatApp {
    constructor() {
        this.messages = [];
        this.sessionId = this.generateSessionId();
        this.isProcessing = false;
        this.voiceEnabled = false;
        this.currentUser = this.getCurrentUser();

        this.init();
    }

    init() {
        this.bindEvents();
        this.updateUI();
        this.startSession();
    }

    generateSessionId() {
        return 'CHAT-' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
    }

    getCurrentUser() {
        try {
            const usernameElement = document.getElementById('usernameDisplay');
            return {
                username: usernameElement ? usernameElement.textContent : 'User',
                id: window.userId || 'unknown'
            };
        } catch (e) {
            return { username: 'User', id: 'unknown' };
        }
    }

    bindEvents() {
        // Send message
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');

        if (sendBtn && messageInput) {
            sendBtn.addEventListener('click', () => this.sendMessage());

            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            messageInput.addEventListener('input', (e) => {
                this.updateCharCount();
                this.autoResizeTextarea(e.target);
            });
        }

        
        const clearBtn = document.getElementById('clearChat');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearChat());
        }

        
        const saveBtn = document.getElementById('saveChat');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveChat());
        }

        
        const exportBtn = document.getElementById('exportChat');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportChat());
        }

        
        const emergencyBtn = document.getElementById('emergencyBtn');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => this.showEmergencyModal());
        }

        
        const promptBtns = document.querySelectorAll('.prompt-btn');
        promptBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const prompt = e.target.getAttribute('data-prompt');
                this.insertPrompt(prompt);
            });
        });

        
        const modeBtns = document.querySelectorAll('.mode-btn');
        modeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.target.getAttribute('data-mode');
                this.switchInputMode(mode);
            });
        });

        
        const sidebarItems = document.querySelectorAll('.sidebar-item');
        sidebarItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.target.getAttribute('data-section');
                this.switchSidebarSection(section);
            });
        });

        
        const templateBtns = document.querySelectorAll('.template-btn');
        templateBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const template = e.target.getAttribute('data-template');
                this.loadTemplate(template);
            });
        });

       
        const emergencyModal = document.getElementById('emergencyModal');
        if (emergencyModal) {
            const confirmBtn = document.getElementById('confirmEmergency');
            const cancelBtn = document.getElementById('cancelEmergency');

            if (confirmBtn) {
                confirmBtn.addEventListener('click', () => {
                    window.location.href = 'tel:911';
                    this.hideEmergencyModal();
                });
            }

            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    this.hideEmergencyModal();
                });
            }

            
            emergencyModal.addEventListener('click', (e) => {
                if (e.target === emergencyModal) {
                    this.hideEmergencyModal();
                }
            });
        }

        
        const callEmergencyBtn = document.getElementById('callEmergency');
        if (callEmergencyBtn) {
            callEmergencyBtn.addEventListener('click', () => {
                this.showEmergencyModal();
            });
        }

        
        const emergencyInfoBtn = document.getElementById('emergencyInfo');
        if (emergencyInfoBtn) {
            emergencyInfoBtn.addEventListener('click', () => {
                this.showEmergencyInfo();
            });
        }

        
        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                const messageInput = document.getElementById('messageInput');
                if (messageInput) {
                    messageInput.value = '';
                    messageInput.style.height = 'auto';
                    this.updateCharCount();
                }
            });
        }

        // Voice input button
        const voiceBtn = document.querySelector('.tool-btn:nth-child(2)'); 
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.startVoiceInput());
        }

        // Attach file button
        const attachBtn = document.querySelector('.tool-btn:nth-child(1)'); 
        if (attachBtn) {
            attachBtn.addEventListener('click', () => this.attachFile());
        }

        
        const emojiBtn = document.querySelector('.tool-btn:nth-child(3)'); 
        if (emojiBtn) {
            emojiBtn.style.display = 'none';
        }

        
        const formatBtn = document.querySelector('.tool-btn:nth-child(4)'); 
        if (formatBtn) {
            formatBtn.style.display = 'none'; 
        }

        
        const quickResponseBtns = document.querySelectorAll('.quick-response');
        quickResponseBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const responseType = e.currentTarget.getAttribute('data-response-type') ||
                    e.currentTarget.querySelector('span').textContent.toLowerCase();
                this.sendQuickResponse(responseType);
            });
        });
    }

    startSession() {
        this.updateSessionInfo();
        console.log('Chat session started:', this.sessionId);
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput?.value.trim();

        if (!message) {
            Utils.showAlert('Please enter a message', 'warning');
            return;
        }

        // Safety check for emergency keywords 
        if (this.isEmergencyMessage(message)) {
            this.showEmergencyModal();
            return; 
        }

       
        this.addMessage(message, 'user');

        // Clear input
        if (messageInput) {
            messageInput.value = '';
            messageInput.style.height = 'auto';
            this.updateCharCount();
        }

        // Show typing indicator
        const typingId = this.showTypingIndicator();

        try {
            
            const response = await APIService.post('/api/chat', {
                message: message,
                session_id: this.sessionId
            });

            
            this.removeTypingIndicator(typingId);

            if (response.error) {
                this.addMessage(`Error: ${response.error}`, 'ai', true);
                Utils.showAlert(response.error, 'error');
                return;
            }

            
            if (response.emergency) {
                this.showEmergencyModal();
            }

            
            if (response.response) {
                this.addMessage(response.response, 'ai');

                
                this.updateChatStats(response);

                
                if (response.success) {
                    Utils.showAlert('Response received successfully', 'success', 3000);
                }
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.removeTypingIndicator(typingId);

            this.addMessage('Sorry, there was an error processing your request. Please try again.', 'ai', true);
            Utils.showAlert('Failed to get response. Please check your connection.', 'error');
        }
    }

    addMessage(text, sender, isError = false) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageId = 'msg-' + Date.now();
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message ${sender}-message ${isError ? 'error' : ''}`;

        const avatarIcon = sender === 'ai' ? 'fas fa-robot' : 'fas fa-user';
        const senderName = sender === 'ai' ? 'MedAI Assistant' : 'You';

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <strong>${senderName}</strong>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-text">${this.formatMessageText(text)}</div>
                ${sender === 'ai' ? this.createMessageActions(messageId) : ''}
            </div>
        `;

        chatMessages.appendChild(messageDiv);

        // Store message
        this.messages.push({
            id: messageId,
            text: text,
            sender: sender,
            timestamp: new Date().toISOString(),
            isError: isError
        });

        
        this.scrollToBottom();
    }

    formatMessageText(text) {
        
        let formatted = text.replace(/\n/g, '<br>');

        
        formatted = formatted.replace(/\n• /g, '<br>• ');
        formatted = formatted.replace(/\n\d+\. /g, '<br>$&');

        
        formatted = formatted.replace(/⚠️/g, '<span class="warning">⚠️</span>');
        formatted = formatted.replace(/🚨/g, '<span class="emergency">🚨</span>');

        return formatted;
    }

    createMessageActions(messageId) {
        return `
            <div class="message-actions">
                <button class="action-btn copy-btn" data-message-id="${messageId}" title="Copy">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="action-btn save-btn" data-message-id="${messageId}" title="Save">
                    <i class="fas fa-bookmark"></i>
                </button>
                <button class="action-btn feedback-btn" data-message-id="${messageId}" title="Feedback">
                    <i class="fas fa-thumbs-up"></i>
                </button>
            </div>
        `;
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return null;

        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.id = typingId;
        typingDiv.className = 'message ai-message typing';

        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <strong>MedAI Assistant</strong>
                    <span class="message-time">Just now</span>
                </div>
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        this.scrollToBottom();

        return typingId;
    }

    removeTypingIndicator(typingId) {
        if (!typingId) return;

        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
    }

    clearChat() {
        if (!confirm('Clear the current chat? This will only clear the display, not your history.')) {
            return;
        }

        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            
            const welcomeMessage = chatMessages.querySelector('.message.ai-message:first-child');
            chatMessages.innerHTML = '';

            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            } else {
                
                this.addMessage('Chat cleared. How can I assist you today?', 'ai');
            }
        }

        this.messages = [];
        Utils.showAlert('Chat cleared successfully', 'success');
    }

    saveChat() {
        const chatData = {
            session_id: this.sessionId,
            messages: this.messages,
            timestamp: new Date().toISOString()
        };

        try {
            const savedChats = JSON.parse(localStorage.getItem('savedChats') || '[]');
            savedChats.push(chatData);
            localStorage.setItem('savedChats', JSON.stringify(savedChats));

            Utils.showAlert('Chat saved successfully!', 'success');
        } catch (error) {
            console.error('Error saving chat:', error);
            Utils.showAlert('Failed to save chat', 'error');
        }
    }

    

    showEmergencyModal() {
        const modal = document.getElementById('emergencyModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    hideEmergencyModal() {
        const modal = document.getElementById('emergencyModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    showEmergencyInfo() {
        this.addMessage(
            `🚨 **Emergency First Aid Information**\n\n` +
            `**For medical emergencies:**\n` +
            `1. **Call emergency services immediately** (911/112)\n` +
            `2. **Stay calm** and provide clear information\n` +
            `3. **Do not move** injured person unless in danger\n` +
            `4. **Apply first aid** if trained to do so\n\n` +
            `**Common emergencies:**\n` +
            `• **Heart attack:** Chest pain, shortness of breath\n` +
            `• **Stroke:** Face drooping, arm weakness, speech difficulty\n` +
            `• **Choking:** Unable to breathe or speak\n` +
            `• **Severe bleeding:** Apply pressure with clean cloth\n\n` +
            `⚠️ **This AI cannot provide emergency care. Always call professional help.**`,
            'ai'
        );
    }

    isEmergencyMessage(text) {
        const emergencyKeywords = [
            'heart attack', 'stroke', 'chest pain', 'can\'t breathe',
            'difficulty breathing', 'severe pain', 'unconscious',
            'bleeding heavily', 'suicide', 'overdose', 'poison',
            'seizure', 'choking', 'paralysis'
        ];

        const textLower = text.toLowerCase();
        return emergencyKeywords.some(keyword => textLower.includes(keyword));
    }

    insertPrompt(prompt) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = prompt;
            messageInput.focus();
            this.updateCharCount();
            this.autoResizeTextarea(messageInput);
        }
    }

    switchInputMode(mode) {
        const modeBtns = document.querySelectorAll('.mode-btn');
        modeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
        });

        this.voiceEnabled = mode === 'voice';

        if (mode === 'voice') {
            this.startVoiceInput();
        }
    }
    
    async readFileContent(file) {
        return new Promise((resolve, reject) => {
            if (file.type.startsWith('text/') || file.type === 'application/pdf') {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = (e) => reject(new Error('Failed to read file'));
                reader.readAsText(file);
            } else if (file.type.startsWith('image/')) {
                resolve(`[Image file: ${file.name}]`);
            } else {
                resolve(`[File: ${file.name}]`);
            }
        });
    }

    async sendFileToServer(file, content) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('content', content);
            formData.append('user_id', this.currentUser.id);

            const response = await fetch('/api/upload_file', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const result = await response.json();
            console.log('File uploaded:', result);

        } catch (error) {
            console.error('Upload error:', error);
            
        }
    }

   
    sendQuickResponse(responseType) {
        const messageInput = document.getElementById('messageInput');
        let responseText = '';

        switch (responseType.toLowerCase()) {
            case 'ask for symptom details':
            case 'symptom':
                responseText = "I understand you're asking about symptoms. Could you please describe them in more detail? (e.g., location, severity, duration, triggers)";
                break;
            case 'medication disclaimer':
            case 'medication':
                responseText = "For medication information, please consult with a healthcare provider who knows your medical history. They can consider: your specific condition, other medications, allergies, and medical history. Never change medication without professional advice.";
                break;
            case 'emergency response':
            case 'emergency':
                responseText = "🚨 EMERGENCY: If this is a medical emergency, please:\n\n1. Call emergency services (911/112) immediately\n2. Do NOT wait for AI response\n3. Stay calm and follow instructions\n4. If alone, try to get help from neighbors\n\n⚠️ This AI cannot provide emergency medical care.";
                break;
        }

        if (responseText && messageInput) {
            messageInput.value = responseText;
            this.updateCharCount();
            this.autoResizeTextarea(messageInput); 
            messageInput.focus(); 
        }
    }

    
    scrollToChatInput() {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            messageInput.focus();
        }
    }

    
    sendQuickResponse(responseType) {
        const messageInput = document.getElementById('messageInput');
        let responseText = '';

        switch (responseType.toLowerCase()) {
            case 'ask for symptom details':
            case 'symptom':
                responseText = "I understand you're asking about symptoms. Could you please describe them in more detail? (e.g., location, severity, duration, triggers)";
                break;
            case 'medication disclaimer':
            case 'medication':
                responseText = "For medication information, please consult with a healthcare provider who knows your medical history. They can consider: your specific condition, other medications, allergies, and medical history. Never change medication without professional advice.";
                break;
            case 'emergency response':
            case 'emergency':
                responseText = "🚨 EMERGENCY: If this is a medical emergency, please:\n\n1. Call emergency services (911/112) immediately\n2. Do NOT wait for AI response\n3. Stay calm and follow instructions\n4. If alone, try to get help from neighbors\n\n⚠️ This AI cannot provide emergency medical care.";
                break;
        }

        if (responseText && messageInput) {
            messageInput.value = responseText;
            this.updateCharCount();
            this.autoResizeTextarea(messageInput);
            messageInput.focus();

            
            this.scrollToChatInput();
        }
    }

    switchSidebarSection(section) {
        
        const sidebarItems = document.querySelectorAll('.sidebar-item');
        sidebarItems.forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-section') === section);
        });

        
        const sections = document.querySelectorAll('.sidebar-section');
        sections.forEach(sec => {
            sec.classList.toggle('active', sec.id === section + '-section');
        });
    }

    loadTemplate(template) {
        const templates = {
            'symptom-check': 'I\'m experiencing [describe symptoms]. They started [when]. The severity is [mild/moderate/severe]. Other symptoms include [list any].',
            'medication-info': 'I have questions about [medication name]. I want to know about [side effects/dosage/interactions].',
            'lifestyle-advice': 'I want to improve my [diet/exercise/sleep/stress]. My current situation is [describe]. My goals are [what you want to achieve].',
            'emergency-guide': 'What should I do in case of [emergency type]? The symptoms are [describe].'
        };

        const templateText = templates[template] || '';
        this.insertPrompt(templateText);
    }

    updateCharCount() {
        const messageInput = document.getElementById('messageInput');
        const charCount = document.querySelector('.char-count');

        if (messageInput && charCount) {
            const count = messageInput.value.length;
            charCount.textContent = `${count}/1000 characters`;

            if (count > 900) {
                charCount.style.color = 'var(--danger-color)';
            } else if (count > 700) {
                charCount.style.color = 'var(--warning-color)';
            } else {
                charCount.style.color = 'var(--gray-600)';
            }
        }
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    updateSessionInfo() {
        const sessionIdElement = document.getElementById('sessionId');
        const startTimeElement = document.getElementById('startTime');

        if (sessionIdElement) {
            sessionIdElement.textContent = this.sessionId;
        }

        if (startTimeElement) {
            startTimeElement.textContent = new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    updateChatStats(response) {
        
        const responseTimeElement = document.getElementById('responseTime');
        if (responseTimeElement) {
            responseTimeElement.textContent = '0.8s avg';
        }

        
        if (response.confidence) {
            const safetyScore = Math.round(response.confidence * 100);
            const safetyFill = document.querySelector('.meter-fill');
            const safetyScoreElement = document.querySelector('.safety-score');

            if (safetyFill) {
                safetyFill.style.width = `${safetyScore}%`;
            }

            if (safetyScoreElement) {
                safetyScoreElement.textContent = `${safetyScore}% Safe`;
            }
        }
    }

    updateUI() {
        // Initial UI updates
        this.updateCharCount();
    }
}


document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});