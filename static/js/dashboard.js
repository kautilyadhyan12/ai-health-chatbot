
class DashboardApp {
    constructor() {
        this.currentUser = null;
        this.chatHistory = [];
        this.analyticsData = null;
        this.chartInstances = {};
        this.currentPage = 1;
        this.totalPages = 1;

        this.init();
    }

    async init() {
        
        if (window.dashboardInitialized) {
            console.log('⚠️ Dashboard already initialized, skipping...');
            return;
        }
        window.dashboardInitialized = true;

        
        await this.loadUserData();

        
        this.initCharts();
        this.initChat();
        this.initAnalytics();
        this.initHistory();
        this.initSettings();

        
        await this.loadDashboardData();

        
        this.setupEventListeners();

        
        this.startPeriodicUpdates();

        console.log('Dashboard initialized for user:', this.currentUser?.username);
    }

    async loadUserData() {
        try {
            
            const response = await APIService.get('/api/user');
            if (response && response.username) {
                this.currentUser = response;
            } else {
                
                const usernameElement = document.getElementById('usernameDisplay');
                if (usernameElement) {
                    this.currentUser = { username: usernameElement.textContent };
                }
            }
        } catch (error) {
            console.log('User data not available, using fallback');
            const usernameElement = document.getElementById('usernameDisplay');
            if (usernameElement) {
                this.currentUser = { username: usernameElement.textContent };
            }
        }
    }

    async loadDashboardData() {
        try {
            
            await this.loadDashboardStats();

            
            this.loadAnalyticsAsync();

            
            await this.loadHistoryPage(1);

            
            this.updateHealthTip();

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            Utils.showAlert('Could not load dashboard data. Please refresh the page.', 'error');
        }
    }

    async loadDashboardStats() {
        try {
            
            const response = await APIService.get('/api/dashboard/stats');

            if (response && response.success) {
                this.updateDashboardStats(response.stats);

                
                if (response.activity) {
                    this.updateActivityChart(response.activity);
                }

                return;
            }

            
            const analytics = await APIService.get('/api/analytics');
            if (analytics && analytics.summary) {
                this.updateDashboardStats({
                    total_chats: analytics.summary.total_chats || 0,
                    avg_confidence: analytics.summary.avg_confidence || 0,
                    most_common_intent: analytics.summary.most_common_intent || 'N/A',
                    last_active: 'Just now'
                });
            }

        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
            
            this.updateDashboardStats({
                total_chats: 0,
                avg_confidence: 0,
                most_common_intent: 'N/A',
                last_active: 'Never'
            });
        }
    }

    updateDashboardStats(stats) {
        console.log('🔄 Updating dashboard stats:', stats);

        
        const totalChatsEl = document.getElementById('totalChats');
        if (totalChatsEl) {
            const currentValue = parseInt(totalChatsEl.textContent) || 0;
            const newValue = stats.total_chats || 0;

            if (currentValue === 0 && newValue > 0) {
                
                this.animateCounter(totalChatsEl, 0, newValue, 1000);
            } else {
                totalChatsEl.textContent = newValue;
            }
        }

        // Update Average Confidence
        const avgConfidenceEl = document.getElementById('avgConfidence');
        if (avgConfidenceEl) {
            const currentValue = parseFloat(avgConfidenceEl.textContent) || 0;
            const newValue = stats.avg_confidence || 0;

            if (currentValue === 0 && newValue > 0) {
                this.animateCounter(avgConfidenceEl, 0, newValue, 1000, true);
            } else {
                avgConfidenceEl.textContent = newValue.toFixed(1) + '%';
            }

            // Color coding
            if (newValue >= 80) {
                avgConfidenceEl.style.color = '#48bb78';
            } else if (newValue >= 60) {
                avgConfidenceEl.style.color = '#ed8936';
            } else {
                avgConfidenceEl.style.color = '#f56565';
            }
        }

        
        const commonIntentEl = document.getElementById('commonIntent');
        if (commonIntentEl) {
            const newValue = stats.most_common_intent || '--';
            if (commonIntentEl.textContent === '--' || commonIntentEl.textContent === 'N/A') {
                commonIntentEl.textContent = newValue;
                commonIntentEl.classList.add('highlight');
                setTimeout(() => commonIntentEl.classList.remove('highlight'), 1000);
            } else {
                commonIntentEl.textContent = newValue;
            }
        }

        // Update Last Active
        const lastActiveEl = document.getElementById('lastActive');
        if (lastActiveEl) {
            const newValue = stats.last_active || 'Never';
            lastActiveEl.textContent = newValue;

            if (newValue === 'Just now' || newValue.includes('min ago')) {
                lastActiveEl.style.color = '#48bb78';
                lastActiveEl.style.fontWeight = 'bold';
            } else {
                lastActiveEl.style.color = '';
                lastActiveEl.style.fontWeight = '';
            }
        }
    }

    animateCounter(element, start, end, duration, isPercent = false) {
        const range = end - start;
        const increment = end > start ? 1 : -1;
        const stepTime = Math.abs(Math.floor(duration / range));
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            element.textContent = isPercent ? current.toFixed(1) + '%' : current;

            if (current === end) {
                clearInterval(timer);
            }
        }, stepTime);
    }

    loadAnalyticsAsync() {
        
        APIService.get('/api/analytics')
            .then(analytics => {
                if (analytics && analytics.success) {
                    this.analyticsData = analytics;
                    this.updateCharts(analytics);
                }
            })
            .catch(error => {
                console.error('Failed to load analytics:', error);
            });
    }

    updateActivityChart(activityData) {
        if (!activityData || activityData.length === 0) return;

        const activityChart = this.chartInstances.activityChart;
        if (!activityChart) return;

        // Update chart data
        activityChart.data.labels = activityData.map(d => d.date);
        activityChart.data.datasets[0].data = activityData.map(d => d.chats);
        activityChart.update();
    }

    updateDashboardStats(data) {
        // Update quick stats
        const totalChats = document.getElementById('totalChats');
        const avgConfidence = document.getElementById('avgConfidence');
        const commonIntent = document.getElementById('commonIntent');
        const lastActive = document.getElementById('lastActive');

        if (totalChats) totalChats.textContent = data.total_chats || '0';
        if (avgConfidence) avgConfidence.textContent = `${(data.avg_confidence || 0).toFixed(1)}%`;

        
        if (commonIntent && data.daily_stats && data.daily_stats.length > 0) {
            const today = data.daily_stats[0];
            if (today.intents && Object.keys(today.intents).length > 0) {
                const mostCommon = Object.entries(today.intents)
                    .sort((a, b) => b[1] - a[1])[0];
                commonIntent.textContent = mostCommon[0].replace('_', ' ').toUpperCase();
            }
        }

        if (lastActive) lastActive.textContent = 'Just now';
    }

    initCharts() {
        
        Object.keys(this.chartInstances).forEach(chartName => {
            if (this.chartInstances[chartName]) {
                try {
                    this.chartInstances[chartName].destroy();
                } catch (e) {
                    console.log(`Error destroying ${chartName}:`, e);
                }
            }
        });
        this.chartInstances = {};

        
        const activityCtx = document.getElementById('activityChart');
        if (activityCtx) {
            
            activityCtx.style.width = '100%';
            activityCtx.style.height = '250px';

            
            const parent = activityCtx.parentElement;
            if (parent) {
                parent.style.position = 'relative';
                parent.style.height = '250px';
                parent.style.minHeight = '250px';
                parent.style.maxHeight = '250px';
                parent.style.width = '100%';
                parent.style.overflow = 'hidden';
            }

            this.chartInstances.activityChart = new Chart(activityCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Chats',
                        data: [12, 19, 15, 25, 22, 30, 28],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#667eea',
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,  
                    animation: {
                        duration: 1000 
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 50,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                stepSize: 10,
                                padding: 10
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                padding: 10
                            }
                        }
                    },
                    layout: {
                        padding: {
                            top: 10,
                            right: 10,
                            bottom: 10,
                            left: 10
                        }
                    }
                }
            });
        }

        
        const intentCtx = document.getElementById('intentChart');
        if (intentCtx) {
            
            intentCtx.style.width = '100%';
            intentCtx.style.height = '250px';

            const parent = intentCtx.parentElement;
            if (parent) {
                parent.style.position = 'relative';
                parent.style.height = '250px';
                parent.style.minHeight = '250px';
                parent.style.maxHeight = '250px';
                parent.style.width = '100%';
                parent.style.overflow = 'hidden';
            }

            this.chartInstances.intentChart = new Chart(intentCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Symptom Check', 'Medication Info', 'Lifestyle Advice', 'Condition Info', 'General Health'],
                    datasets: [{
                        data: [35, 25, 20, 15, 5],
                        backgroundColor: [
                            '#667eea',  
                            '#f093fb',  
                            '#4facfe',  
                            '#43e97b',  
                            '#fa709a'   
                        ],
                        borderWidth: 2,
                        borderColor: 'white',
                        hoverOffset: 15
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,  
                    animation: {
                        animateRotate: true,
                        animateScale: true,
                        duration: 1000
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} chats (${percentage}%)`;
                                }
                            }
                        }
                    },
                    cutout: '65%',
                    layout: {
                        padding: 20
                    }
                }
            });
        }

        
        const usageCtx = document.getElementById('usageChart');
        if (usageCtx) {
            usageCtx.style.width = '100%';
            usageCtx.style.height = '200px';

            const parent = usageCtx.parentElement;
            if (parent) {
                parent.style.position = 'relative';
                parent.style.height = '200px';
                parent.style.minHeight = '200px';
                parent.style.maxHeight = '200px';
                parent.style.width = '100%';
                parent.style.overflow = 'hidden';
            }

            this.chartInstances.usageChart = new Chart(usageCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    datasets: [{
                        label: 'Weekly Chats',
                        data: [45, 52, 48, 60],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: '#667eea',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1000
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                stepSize: 20,
                                padding: 10
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                padding: 10
                            }
                        }
                    },
                    layout: {
                        padding: {
                            left: 10,
                            right: 10,
                            top: 10,
                            bottom: 10
                        }
                    }
                }
            });
        }

        
        const peakCtx = document.getElementById('peakHoursChart');
        if (peakCtx) {
            peakCtx.style.width = '100%';
            peakCtx.style.height = '200px';

            const parent = peakCtx.parentElement;
            if (parent) {
                parent.style.position = 'relative';
                parent.style.height = '200px';
                parent.style.minHeight = '200px';
                parent.style.maxHeight = '200px';
                parent.style.width = '100%';
                parent.style.overflow = 'hidden';
            }

            this.chartInstances.peakHoursChart = new Chart(peakCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['6AM', '9AM', '12PM', '3PM', '6PM', '9PM', '12AM'],
                    datasets: [{
                        label: 'Activity',
                        data: [10, 25, 40, 35, 45, 30, 15],
                        borderColor: '#f093fb',
                        backgroundColor: 'rgba(240, 147, 251, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#f093fb'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1000
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 50,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                stepSize: 10,
                                padding: 10
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                padding: 10
                            }
                        }
                    },
                    layout: {
                        padding: 10
                    }
                }
            });
        }
    }

    updateCharts(data) {
        if (!data || !data.daily_stats) return;

        console.log('📊 Charts are STATIC - not updating to prevent infinite growth');

        

        return;
    }

    initChat() {
        const sendBtn = document.getElementById('sendMessageBtn');
        const userInput = document.getElementById('userInput');
        const clearChatBtn = document.getElementById('clearChatBtn');
        const chatMessages = document.getElementById('chatMessages');

        if (sendBtn && userInput) {
            
            sendBtn.addEventListener('click', () => this.sendMessage());

            
            userInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            userInput.addEventListener('input', function () {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 150) + 'px';
            });
        }

        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => this.clearChat());
        }

        // Quick prompts
        const quickPrompts = document.querySelectorAll('.quick-prompt');
        quickPrompts.forEach(prompt => {
            prompt.addEventListener('click', (e) => {
                const promptText = e.target.getAttribute('data-prompt');
                if (userInput) {
                    userInput.value = promptText;
                    userInput.dispatchEvent(new Event('input'));
                    userInput.focus();
                }
            });
        });

        // Quick responses
        const quickResponses = document.querySelectorAll('.quick-response');
        quickResponses.forEach(response => {
            response.addEventListener('click', (e) => {
                const responseText = e.currentTarget.getAttribute('data-response');
                this.addMessage(responseText, 'ai');
            });
        });
    }

    async sendMessage() {
        const userInput = document.getElementById('userInput');
        const message = userInput?.value.trim();

        if (!message) {
            Utils.showAlert('Please enter a message', 'warning');
            return;
        }

        
        this.addMessage(message, 'user');

        
        if (userInput) {
            userInput.value = '';
            userInput.style.height = 'auto';
        }

        
        const loadingId = this.addLoadingMessage();

        try {
            
            const response = await APIService.post('/api/chat', {
                message: message
            });

            
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) loadingElement.remove();

            
            if (response.emergency) {
                Utils.showAlert('Emergency detected! Please seek immediate medical help.', 'error', 10000);
            }

            // Add AI response
            if (response.response) {
                this.addMessage(response.response, 'ai');

                
                if (typeof showUpdateNotification === 'function') {
                    showUpdateNotification('Chat saved! Dashboard updated.');
                }

                
                if (response.intent || response.confidence) {
                    this.updateChatStats(response);
                }
            } else if (response.error) {
                this.addMessage(`Error: ${response.error}`, 'ai', true);
            }

            
            await this.loadDashboardData();

        } catch (error) {
            console.error('Chat error:', error);
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) loadingElement.remove();

            this.addMessage('Sorry, there was an error processing your request. Please try again.', 'ai', true);
            Utils.showAlert('Failed to get response. Please check your connection.', 'error');
        }
    }

    addMessage(text, sender, isError = false) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

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
                <p>${text}</p>
            </div>
        `;

        chatMessages.appendChild(messageDiv);

        
        chatMessages.scrollTop = chatMessages.scrollHeight;

        
        this.chatHistory.push({
            text: text,
            sender: sender,
            timestamp: new Date().toISOString(),
            isError: isError
        });
    }

    addLoadingMessage() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'message ai-message';

        loadingDiv.innerHTML = `
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

        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        
        const style = document.createElement('style');
        style.textContent = `
            .typing-indicator {
                display: flex;
                gap: 4px;
                padding: 8px 0;
            }
            .typing-indicator span {
                width: 8px;
                height: 8px;
                background: var(--gray-400);
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }
            .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
            .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
        `;
        loadingDiv.appendChild(style);

        return loadingId;
    }

    clearChat() {
        if (!confirm('Clear the current chat? This will only clear the display, not your history.')) {
            return;
        }

        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="message ai-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-header">
                            <strong>MedAI Assistant</strong>
                            <span class="message-time">Just now</span>
                        </div>
                        <p>Chat cleared. How can I assist you today?</p>
                    </div>
                </div>
            `;
        }

        this.chatHistory = [];
        Utils.showAlert('Chat cleared successfully', 'success');
    }

    updateChatStats(response) {
        
        console.log('Chat stats updated:', response);
    }

    initAnalytics() {
        
        const chartRange = document.getElementById('chartRange');
        if (chartRange) {
            chartRange.addEventListener('change', (e) => {
                this.updateAnalyticsChart(parseInt(e.target.value));
            });
        }

        
        this.updateIntentsList();
    }

    updateAnalyticsChart(days) {
        console.log('📊 Analytics charts are now static - not updating');
        
    }

    updateIntentsList() {
        const intentsList = document.getElementById('intentsList');
        if (!intentsList || !this.analyticsData?.daily_stats) return;

        const today = this.analyticsData.daily_stats[0];
        if (!today?.intents) return;

        const intents = Object.entries(today.intents)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);

        intentsList.innerHTML = intents.map(([intent, count]) => `
            <div class="intent-item">
                <span class="intent-name">${intent.replace('_', ' ')}</span>
                <span class="intent-count">${count}</span>
            </div>
        `).join('');
    }

    updateMonthlySummary() {
        const monthlySummary = document.getElementById('monthlySummary');
        if (!monthlySummary || !this.analyticsData?.daily_stats) return;

        // Group by month
        const monthlyData = {};
        this.analyticsData.daily_stats.forEach(day => {
            const date = new Date(day.date);
            const month = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

            if (!monthlyData[month]) {
                monthlyData[month] = { chats: 0, intents: {} };
            }

            monthlyData[month].chats += day.chats || 0;

            
            if (day.intents) {
                const intents = typeof day.intents === 'string' ? JSON.parse(day.intents) : day.intents;
                Object.entries(intents).forEach(([intent, count]) => {
                    monthlyData[month].intents[intent] = (monthlyData[month].intents[intent] || 0) + count;
                });
            }
        });

        // Display top 3 months
        const topMonths = Object.entries(monthlyData)
            .sort((a, b) => b[1].chats - a[1].chats)
            .slice(0, 3);

        monthlySummary.innerHTML = topMonths.map(([month, data]) => `
            <div class="summary-item">
                <span>${month}</span>
                <span>${data.chats} chats</span>
            </div>
        `).join('');
    }

    initHistory() {
        const historySearch = document.getElementById('historySearch');
        const historyFilter = document.getElementById('historyFilter');
        const deleteAllBtn = document.getElementById('deleteAllBtn');
        const downloadHistoryBtn = document.getElementById('downloadHistoryBtn');
        const startChatBtn = document.getElementById('startChatFromHistory');

        
        if (historySearch) {
            historySearch.addEventListener('input', Utils.debounce(() => {
                this.loadHistoryPage(1);
            }, 300));
        }

        
        if (historyFilter) {
            historyFilter.addEventListener('change', () => {
                this.loadHistoryPage(1);
            });
        }

        
        if (deleteAllBtn) {
            deleteAllBtn.addEventListener('click', () => this.deleteAllHistory());
        }

        
        if (downloadHistoryBtn) {
            downloadHistoryBtn.addEventListener('click', () => this.downloadHistory());
        }

        
        if (startChatBtn) {
            startChatBtn.addEventListener('click', () => {
                window.location.hash = 'chat';
                NavigationHandler.switchSection('chat');
            });
        }
    }

    async loadHistoryPage(page) {
        try {
            const search = document.getElementById('historySearch')?.value;
            const filter = document.getElementById('historyFilter')?.value;

            let url = `/api/history?page=${page}`;
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (filter && filter !== 'all') url += `&filter=${filter}`;

            const response = await APIService.get(url);

            if (response && !response.error) {
                this.currentPage = response.current_page || 1;
                this.totalPages = response.total_pages || 1;
                this.renderHistoryList(response.history || []);
                this.renderPagination();
            } else {
                this.renderHistoryList([]);
            }
        } catch (error) {
            console.error('Failed to load history:', error);
            this.renderHistoryList([]);
        }
    }

    renderHistoryList(history) {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;

        if (!history || history.length === 0) {
            historyList.innerHTML = `
                <div class="history-placeholder">
                    <i class="fas fa-history"></i>
                    <h3>No chat history found</h3>
                    <p>${this.currentPage > 1 ? 'Try going back to page 1' : 'Start a conversation with MedAI Assistant to see your history here.'}</p>
                    <button class="btn btn-primary" id="startChatFromHistory">
                        <i class="fas fa-comment-medical"></i>
                        Start a Chat
                    </button>
                </div>
            `;

            // Re-attach event listener
            const startChatBtn = document.getElementById('startChatFromHistory');
            if (startChatBtn) {
                startChatBtn.addEventListener('click', () => {
                    window.location.hash = 'chat';
                    NavigationHandler.switchSection('chat');
                });
            }

            return;
        }

        historyList.innerHTML = history.map(record => `
            <div class="history-item">
                <div class="history-item-header">
                    <span class="history-item-date">${Utils.formatDate(record.timestamp)}</span>
                    <div class="history-item-actions">
                        <button class="history-item-action" onclick="dashboard.deleteHistory(${record.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                        <button class="history-item-action" onclick="dashboard.viewHistory(${record.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
                <div class="history-item-preview">
                    <strong>You:</strong> ${record.user_query.substring(0, 100)}${record.user_query.length > 100 ? '...' : ''}<br>
                    <strong>AI:</strong> ${record.bot_response.substring(0, 100)}${record.bot_response.length > 100 ? '...' : ''}
                </div>
                <div class="history-item-footer">
                    <span class="history-item-intent">${record.intent || 'general'}</span>
                    <span>${record.confidence ? `Confidence: ${(record.confidence * 100).toFixed(1)}%` : ''}</span>
                </div>
            </div>
        `).join('');
    }

    renderPagination() {
        const pagination = document.getElementById('historyPagination');
        if (!pagination) return;

        if (this.totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';

        // Previous button
        paginationHTML += `
            <button class="pagination-btn" ${this.currentPage <= 1 ? 'disabled' : ''} 
                onclick="dashboard.loadHistoryPage(${this.currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisible - 1);

        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="pagination-number ${i === this.currentPage ? 'active' : ''}" 
                    onclick="dashboard.loadHistoryPage(${i})">
                    ${i}
                </button>
            `;
        }

        // Next button
        paginationHTML += `
            <button class="pagination-btn" ${this.currentPage >= this.totalPages ? 'disabled' : ''} 
                onclick="dashboard.loadHistoryPage(${this.currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        pagination.innerHTML = paginationHTML;
    }

    async deleteHistory(recordId) {
        if (!confirm('Delete this chat record?')) return;

        try {
            const response = await APIService.delete(`/api/delete_history/${recordId}`);

            if (response && response.message) {
                Utils.showAlert('Record deleted successfully', 'success');
                
                await this.loadHistoryPage(this.currentPage);
                
                await this.loadDashboardData();
            } else {
                Utils.showAlert(response.error || 'Failed to delete record', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            Utils.showAlert('Failed to delete record', 'error');
        }
    }

    async deleteAllHistory() {
        if (!confirm('Are you sure you want to delete ALL chat history? This action cannot be undone.')) {
            return;
        }

        try {
            
            Utils.showAlert('Bulk delete is not implemented in this demo', 'warning');

            
            this.renderHistoryList([]);
            this.currentPage = 1;
            this.totalPages = 1;
            this.renderPagination();

            Utils.showAlert('History cleared from view (demo only)', 'info');
        } catch (error) {
            console.error('Delete all error:', error);
            Utils.showAlert('Failed to delete history', 'error');
        }
    }

    async downloadHistory() {
        try {
            const response = await fetch('/api/download_history');

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `medai_history_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                Utils.showAlert('History downloaded successfully', 'success');
            } else {
                const error = await response.text();
                throw new Error(error || 'Download failed');
            }
        } catch (error) {
            console.error('Download error:', error);
            Utils.showAlert('Failed to download history', 'error');
        }
    }

    async viewHistory(recordId) {
        try {
            
            const response = await APIService.get(`/api/history/${recordId}`);

            if (response && response.success) {
                
                this.showConversationInPage(response.conversation);
            } else {
                Utils.showAlert('Could not load conversation details', 'error');
            }
        } catch (error) {
            console.error('View history error:', error);
            Utils.showAlert('Failed to load conversation', 'error');
        }
    }

    showConversationInPage(conversation) {
       
        NavigationHandler.switchSection('history');

        
        const detailHTML = `
        <div class="conversation-detail-view" id="conversationDetail">
            <div class="conversation-detail-header">
                <h3><i class="fas fa-conversation"></i> Conversation Details</h3>
                <button class="btn btn-secondary" onclick="dashboard.closeConversationDetail()">
                    <i class="fas fa-arrow-left"></i> Back to List
                </button>
            </div>
            
            <div class="conversation-detail-content">
                <div class="conversation-info-card">
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label"><i class="fas fa-calendar"></i> Date</span>
                            <span class="info-value">${Utils.formatDate(conversation.timestamp)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label"><i class="fas fa-tag"></i> Intent</span>
                            <span class="info-value">${conversation.intent || 'General'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label"><i class="fas fa-chart-line"></i> Confidence</span>
                            <span class="info-value">${conversation.confidence ? (conversation.confidence * 100).toFixed(1) + '%' : 'N/A'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label"><i class="fas fa-clock"></i> Processing Time</span>
                            <span class="info-value">${conversation.processing_time ? conversation.processing_time.toFixed(2) + 's' : 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="conversation-chat-view">
                    <div class="chat-messages">
                        <!-- User Message -->
                        <div class="conversation-message user-message">
                            <div class="message-avatar">
                                <i class="fas fa-user"></i>
                            </div>
                            <div class="message-content">
                                <div class="message-header">
                                    <strong>You</strong>
                                    <span class="message-time">${Utils.formatTimeAgo(conversation.timestamp)}</span>
                                </div>
                                <div class="message-text">
                                    ${this.formatMessageForDisplay(conversation.user_query)}
                                </div>
                            </div>
                        </div>
                        
                        <!-- AI Message -->
                        <div class="conversation-message ai-message">
                            <div class="message-avatar">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="message-content">
                                <div class="message-header">
                                    <strong>MedAI Assistant</strong>
                                    <span class="message-time">${Utils.formatTimeAgo(conversation.timestamp)}</span>
                                </div>
                                <div class="message-text">
                                    ${this.formatMessageForDisplay(conversation.bot_response)}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="conversation-actions">
                    <button class="btn btn-secondary" onclick="dashboard.copyConversationText(${conversation.id})">
                        <i class="fas fa-copy"></i> Copy Conversation
                    </button>
                    <button class="btn btn-primary" onclick="dashboard.startNewChatFromHistory('${conversation.user_query}')">
                        <i class="fas fa-comment-medical"></i> Continue This Conversation
                    </button>
                </div>
            </div>
        </div>
    `;

        
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.style.display = 'none';
        }

    
        const pagination = document.getElementById('historyPagination');
        if (pagination) {
            pagination.style.display = 'none';
        }

        
        const historySection = document.getElementById('historySection');
        historySection.insertAdjacentHTML('beforeend', detailHTML);

        
        setTimeout(() => {
            const detailElement = document.getElementById('conversationDetail');
            if (detailElement) {
                detailElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }, 100);
    }

    formatMessageForDisplay(text) {
       
        return text.replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    closeConversationDetail() {
        // Remove detail view
        const detailElement = document.getElementById('conversationDetail');
        if (detailElement) {
            detailElement.remove();
        }

        // Show history list
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.style.display = 'block';
        }

        // Show pagination
        const pagination = document.getElementById('historyPagination');
        if (pagination) {
            pagination.style.display = 'flex';
        }
    }

    copyConversationText(recordId) {
        const detailElement = document.getElementById('conversationDetail');
        if (!detailElement) return;

        const userQuery = detailElement.querySelector('.user-message .message-text').textContent;
        const aiResponse = detailElement.querySelector('.ai-message .message-text').textContent;

        const textToCopy = `User: ${userQuery}\n\nAI: ${aiResponse}`;

        navigator.clipboard.writeText(textToCopy)
            .then(() => Utils.showAlert('Copied to clipboard!', 'success'))
            .catch(() => Utils.showAlert('Failed to copy', 'error'));
    }

    startNewChatFromHistory(query) {
        
        NavigationHandler.switchSection('chat');

        
        const chatInput = document.getElementById('userInput') || document.getElementById('messageInput');
        if (chatInput) {
            chatInput.value = query;
            chatInput.focus();

            
            const inputEvent = new Event('input', { bubbles: true });
            chatInput.dispatchEvent(inputEvent);
        }
    }

    copyConversation(recordId) {
        
        const modal = document.getElementById('conversationModal');
        if (!modal) return;

        const userQuery = modal.querySelector('.user-message p').textContent;
        const aiResponse = modal.querySelector('.ai-message p').textContent;

        const textToCopy = `User: ${userQuery}\n\nAI: ${aiResponse}`;

        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                Utils.showAlert('Conversation copied to clipboard!', 'success');
            })
            .catch(err => {
                console.error('Copy failed:', err);
                Utils.showAlert('Failed to copy to clipboard', 'error');
            });
    }

    initSettings() {
        
        console.log('Settings initialized');
    }

    updateHealthTip() {
        const healthTips = [
            "Stay hydrated! Drink at least 8 glasses of water daily.",
            "Aim for 7-9 hours of quality sleep each night.",
            "Take regular breaks from screens to rest your eyes.",
            "Practice deep breathing to reduce stress and anxiety.",
            "Include fruits and vegetables in every meal.",
            "Walk for at least 30 minutes daily for better health.",
            "Practice good posture to prevent back and neck pain.",
            "Schedule regular health check-ups with your doctor.",
            "Limit processed foods and added sugars in your diet.",
            "Stay socially connected for mental well-being."
        ];

        const healthTipElement = document.getElementById('healthTip');
        if (healthTipElement) {
            const randomTip = healthTips[Math.floor(Math.random() * healthTips.length)];
            healthTipElement.textContent = randomTip;
        }
    }

    setupEventListeners() {
        // New chat button
        const newChatBtn = document.getElementById('newChatBtn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => {
                window.location.hash = 'chat';
                NavigationHandler.switchSection('chat');

                
                setTimeout(() => {
                    const userInput = document.getElementById('userInput');
                    if (userInput) userInput.focus();
                }, 100);
            });
        }

        // Quick action buttons
        const actionButtons = document.querySelectorAll('[data-action]');
        actionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });

        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                const sidebar = document.querySelector('.sidebar');
                sidebar.classList.toggle('collapsed');

                const icon = sidebarToggle.querySelector('i');
                if (sidebar.classList.contains('collapsed')) {
                    icon.className = 'fas fa-chevron-right';
                    sidebarToggle.style.transform = 'rotate(180deg)';
                } else {
                    icon.className = 'fas fa-chevron-left';
                    sidebarToggle.style.transform = 'rotate(0deg)';
                }
            });
        }

        // Chart range selector
        const chartRange = document.getElementById('chartRange');
        if (chartRange) {
            chartRange.addEventListener('change', async (e) => {
                const days = parseInt(e.target.value);
                await this.updateAnalyticsWithRange(days);
            });
        }
    }

    handleQuickAction(action) {
        switch (action) {
            case 'emergency':
                Utils.showAlert('🚨 Emergency Mode Activated. Please call emergency services (911/112) immediately if you have a medical emergency!', 'error', 10000);
                break;
            case 'download':
                this.downloadHistory();
                break;
            case 'clear':
                this.clearChat();
                break;
            case 'faq':
                window.open('#', '_blank');
                break;
            default:
                console.log('Unknown action:', action);
        }
    }

    async updateAnalyticsWithRange(days) {
        try {
           
            console.log('📊 Charts are static - not updating with new range');
            Utils.showAlert(`Analytics charts are now static to prevent issues. Showing demo data only.`, 'info');
        } catch (error) {
            console.error('Failed to update analytics:', error);
        }
    }

    startPeriodicUpdates() {
        
        setInterval(() => {
            this.updateHealthTip();
        }, 5 * 60 * 1000);

        
    }
}


document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardApp();
});