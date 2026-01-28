// App state
let messages = [];
let models = { aliyun: [], openai: [] };
let isLoading = false;
let showImageGen = false;
let showSettings = false;
let chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
let currentChatId = null;
let currentAgent = 'default';
let dailyFreeLimit = 10;

// 自动适配 SCRIPT_NAME 前缀
const BASE = window.location.pathname.startsWith('/openchatbox/') ? '/openchatbox' : '';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // 等待 lucide 加载
    function waitForLucide(cb) {
        if (window.lucide && typeof lucide.createIcons === 'function') {
            cb();
        } else {
            setTimeout(() => waitForLucide(cb), 50);
        }
    }
    waitForLucide(() => {
        lucide.createIcons();
    });

    // Load theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
        document.getElementById('themeIcon').setAttribute('data-lucide', 'sun');
    }
    waitForLucide(() => {
        lucide.createIcons();
    });

    // Load app config
    await loadConfig();
    

    
    // Load chat history
    loadChatHistory();
    
    // Load API key
    loadApiKey();
    
    loadCustomModel();
    loadEndpointUrl();

    // Update usage quota
    updateUsageQuota();
    
    // Load image generation settings
    loadImageEndpointUrl();
    loadImageApiKey();
    loadImageModel();

    loadImageSize();

    // Initialize marked.js
    marked.setOptions({
        breaks: true,
        gfm: true
    });
});

// Load app configuration
async function loadConfig() {
    try {
        const response = await fetch(`${BASE}/api/config`);
        const config = await response.json();
        const appNameElement = document.getElementById('appName');
        if (appNameElement) {
            appNameElement.textContent = currentLang === 'zh' ? config.appName : config.appNameEn;
        }
        // Update title
        document.title = currentLang === 'zh' ? config.appName : config.appNameEn;
        
        // Store daily free limit
        dailyFreeLimit = config.dailyFreeLimit || 10;
        updateUsageQuota();
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// Make loadConfig available globally
window.loadConfig = loadConfig;


// Theme toggle
function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    document.getElementById('themeIcon').setAttribute('data-lucide', isDark ? 'sun' : 'moon');
    lucide.createIcons();
}

// Settings toggle
function toggleSettings() {
    showSettings = !showSettings;
    const panelDisplay = showSettings ? 'block' : 'none';
    document.getElementById('settingsPanel').style.display = panelDisplay;
    document.getElementById('settingsBtn').classList.toggle('active', showSettings);

    // On small screens, auto-hide the sidebar when opening settings
    const sidebar = document.querySelector('.sidebar');
    if (window.innerWidth <= 768 && sidebar) {
        if (showSettings) {
            sidebar.classList.remove('open');
        }
    }

    // ensure lucide icons are (re)rendered for the close icon
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }

    // hide mobile hamburger while settings panel is open to avoid overlap
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    if (mobileBtn) {
        if (showSettings) {
            mobileBtn.style.display = 'none';
        } else {
            mobileBtn.style.display = window.innerWidth <= 768 ? 'block' : 'none';
        }
    }
}

// Image generation toggle
function toggleImageGen() {
    showImageGen = !showImageGen;
    document.getElementById('chatArea').style.display = showImageGen ? 'none' : 'flex';
    document.getElementById('imageGenArea').style.display = showImageGen ? 'block' : 'none';
    document.getElementById('inputArea').style.display = showImageGen ? 'none' : 'block';
    document.getElementById('imageGenBtn').classList.toggle('active', showImageGen);
    
    // Remove newChat highlight when switching to image gen
    if (showImageGen) {
        document.getElementById('newChatBtn').classList.remove('active');
        // also remove therapist highlight
        const therapistBtn = document.getElementById('therapistBtn');
        if (therapistBtn) therapistBtn.classList.remove('active');
    }
    // hide sidebar on mobile so user sees the image-gen UI
    hideSidebarIfMobile();
}

// Load custom model
function loadCustomModel() {
    const customModel = localStorage.getItem('customModel') || '';
    const modelInput = document.getElementById('customModel');
    if (modelInput) {
        modelInput.value = customModel;
    }
}

// Save custom model
function saveCustomModel() {
    const customModel = document.getElementById('customModel').value.trim();
    localStorage.setItem('customModel', customModel || '');
}

// Get custom model
function getCustomModel() {
    return localStorage.getItem('customModel') || '';
}

// New chat
function newChat() {
    currentChatId = null;
    messages = [];
    currentAgent = 'default';
    
    // Switch back to chat view if in image generation mode
    if (showImageGen) {
        showImageGen = false;
        document.getElementById('chatArea').style.display = 'flex';
        document.getElementById('imageGenArea').style.display = 'none';
        document.getElementById('inputArea').style.display = 'block';
        document.getElementById('imageGenBtn').classList.remove('active');
    }
    
    // Highlight new chat button
    document.getElementById('newChatBtn').classList.add('active');
    document.getElementById('imageGenBtn').classList.remove('active');
    // ensure therapist tab is not active
    const therapistBtn = document.getElementById('therapistBtn');
    if (therapistBtn) therapistBtn.classList.remove('active');
    
    document.getElementById('chatArea').innerHTML = `
        <div class="welcome-screen">
            <div class="welcome-icon">
                <i data-lucide="sparkles" style="width: 64px; height: 64px;"></i>
            </div>
            <h1 data-i18n="title">${t('title')}</h1>
            <p data-i18n="subtitle">${t('subtitle')}</p>
        </div>
    `;
    lucide.createIcons();
    updateChatHistoryUI();
    hideSidebarIfMobile();
}

// Open Therapist (心理医生) chat view
function openTherapist() {
    currentChatId = null;
    messages = [];
    currentAgent = 'therapist';
    // Exit image generation mode if active and show chat UI
    if (showImageGen) {
        showImageGen = false;
        const chatAreaEl = document.getElementById('chatArea');
        const imageGenAreaEl = document.getElementById('imageGenArea');
        const inputAreaEl = document.getElementById('inputArea');
        if (chatAreaEl) chatAreaEl.style.display = 'flex';
        if (imageGenAreaEl) imageGenAreaEl.style.display = 'none';
        if (inputAreaEl) inputAreaEl.style.display = 'block';
        const imageGenBtnEl = document.getElementById('imageGenBtn');
        if (imageGenBtnEl) imageGenBtnEl.classList.remove('active');
    }

    // Render a welcome-style therapist intro (same structure as newChat)
    document.getElementById('chatArea').innerHTML = `
        <div class="welcome-screen">
            <div class="welcome-icon">
                <i data-lucide="user" style="width: 64px; height: 64px;"></i>
            </div>
            <h1>心理医生</h1>
            <p style="max-width:720px;margin:0 auto;color:var(--text-secondary);line-height:1.6;">
                欢迎来到心理医生对话。我会倾听并提供情绪调节与放松练习建议，帮助你梳理问题并给出可行的下一步方法。
                如处于紧急危机或有自伤倾向，请立刻联系当地紧急服务或信任的人。本工具不替代专业治疗。
                可先用一两句话描述你当前最困扰的事。
            </p>
        </div>
    `;

    // Button active states
    const therapistBtn = document.getElementById('therapistBtn');
    const newChatBtn = document.getElementById('newChatBtn');
    const imageGenBtn = document.getElementById('imageGenBtn');
    if (therapistBtn) therapistBtn.classList.add('active');
    if (newChatBtn) newChatBtn.classList.remove('active');
    if (imageGenBtn) imageGenBtn.classList.remove('active');

    // Ensure icons render
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }

    updateChatHistoryUI();
    hideSidebarIfMobile();
}

// Chat history management
function loadChatHistory() {
    chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    updateChatHistoryUI();
}

function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

function updateChatHistoryUI() {
    const listEl = document.getElementById('chatHistoryList');
    if (!listEl) return;

    if (chatHistory.length === 0) {
        listEl.innerHTML = '<div class="chat-history-empty" data-i18n="chatHistoryEmpty"></div>';
        if (typeof updateTranslations === 'function') updateTranslations();
    } else {
        listEl.innerHTML = chatHistory.map(chat => `
            <div class="chat-history-item ${chat.id === currentChatId ? 'active' : ''}" 
                 onclick="loadChat('${chat.id}')">
                <span class="chat-history-title">${escapeHtml(chat.title)}</span>
                <button class="chat-history-delete" onclick="event.stopPropagation(); deleteChat('${chat.id}')">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        `).join('');
    }

    // 只有 lucide 已加载时才调用
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

function saveCurrentChat() {
    if (messages.length === 0) return;
    
    const title = messages.find(m => m.role === 'user')?.content.substring(0, 30) || '新对话';
    
    if (currentChatId) {
        // Update existing chat
        const chat = chatHistory.find(c => c.id === currentChatId);
        if (chat) {
            chat.messages = [...messages];
            chat.title = title;
            chat.updatedAt = new Date().toISOString();
        }
    } else {
        // Create new chat
        currentChatId = Date.now().toString();
        chatHistory.unshift({
            id: currentChatId,
            title: title,
            messages: [...messages],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        });
    }
    
    // Keep only last 50 chats
    if (chatHistory.length > 50) {
        chatHistory = chatHistory.slice(0, 50);
    }
    
    saveChatHistory();
    updateChatHistoryUI();
}

function loadChat(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;
    
    currentChatId = chatId;
    messages = [...chat.messages];
    renderMessages();
    updateChatHistoryUI();
    // set UI active states: this is a loaded chat (regular chat)
    const newChatBtn = document.getElementById('newChatBtn');
    const imageGenBtn = document.getElementById('imageGenBtn');
    const therapistBtn = document.getElementById('therapistBtn');
    if (newChatBtn) newChatBtn.classList.add('active');
    if (imageGenBtn) imageGenBtn.classList.remove('active');
    if (therapistBtn) therapistBtn.classList.remove('active');
    // hide sidebar on mobile after selecting a saved chat
    hideSidebarIfMobile();
}

function deleteChat(chatId) {
    if (confirm('确定要删除这个对话吗？')) {
        chatHistory = chatHistory.filter(c => c.id !== chatId);
        saveChatHistory();
        
        if (currentChatId === chatId) {
            newChat();
        } else {
            updateChatHistoryUI();
        }
    }
}

// API key management
function loadApiKey() {
    const customKey = localStorage.getItem('customApiKey') || '';
    const keyInput = document.getElementById('customApiKey');
    if (keyInput) {
        keyInput.value = customKey;
    }
}

// Load endpoint URL
function loadEndpointUrl() {
    const endpointUrl = localStorage.getItem('endpointUrl') || '';
    const endpointInput = document.getElementById('endpointUrl');
    if (endpointInput) {
        endpointInput.value = endpointUrl;
    }
}

// Save endpoint URL
function saveEndpointUrl() {
    const endpointUrl = document.getElementById('endpointUrl').value.trim();
    localStorage.setItem('endpointUrl', endpointUrl);
}

// Get endpoint URL
function getEndpointUrl() {
    return localStorage.getItem('endpointUrl') || '';
}

function saveApiKey() {
    const customKey = document.getElementById('customApiKey').value.trim();
    localStorage.setItem('customApiKey', customKey);
    updateUsageQuota();
}

function getApiKey() {
    return localStorage.getItem('customApiKey') || '';
}

// Usage quota management
async function updateUsageQuota() {
    const customKey = getApiKey();
    const quotaEl = document.getElementById('usageQuota');
    const quotaCountEl = document.getElementById('quotaCount');
    
    if (!quotaEl || !quotaCountEl) return;
    
    // Only show quota if using default key
    if (customKey) {
        quotaEl.style.display = 'none';
    } else {
        try {
            const response = await fetch(`${BASE}/api/usage`);
            const usage = await response.json();
            
            quotaEl.style.display = 'block';
            quotaCountEl.textContent = `${usage.used}/${usage.limit}`;
            
            // Highlight if near or over limit
            if (usage.remaining === 0) {
                quotaCountEl.style.color = '#f85149';
            } else if (usage.remaining <= usage.limit * 0.2) {
                quotaCountEl.style.color = '#d29922';
            } else {
                quotaCountEl.style.color = 'var(--text-primary)';
            }
        } catch (error) {
            console.error('Failed to fetch usage:', error);
            quotaEl.style.display = 'none';
        }
    }
}

// Send message
async function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) {
        console.error('messageInput element not found');
        return;
    }
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    const endpointUrl = getEndpointUrl();
    const customModel = getCustomModel();
    const customApiKey = getApiKey();

    // Add user message
    messages.push({ role: 'user', content: message });
    input.value = '';
    input.style.height = 'auto'; // Reset textarea height
    renderMessages();
    
    // Show loading
    isLoading = true;
    showThinking();
    
    try {
        const temperature = 0.7;
        const maxTokens = 2000;

        let response, data;
        if (currentAgent === 'therapist') {
            // Use agent completion proxy on the backend
            const agentBody = {
                input: { prompt: message },
                parameters: {}
            };

            response = await fetch(`${BASE}/api/agent-completion`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(agentBody)
            });
            data = await response.json();
        } else {
            const requestBody = {
                messages,
                model: customModel,
                temperature,
                max_tokens: maxTokens,
                endpoint_url: endpointUrl,
                api_key: customApiKey
            };

            response = await fetch(`${BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            data = await response.json();
        }
        
        if (response.ok) {
            messages.push({
                role: 'assistant',
                content: data.message.content
            });
            
            // Update usage quota after successful request
            updateUsageQuota();
            
            // Save chat history after successful response
            saveCurrentChat();
        } else if (response.status === 429) {
            // Quota exceeded
            alert(data.detail || t('quotaExceeded'));
            // Open settings panel
            if (!showSettings) {
                toggleSettings();
            }
            return; // Don't add error message to chat
        } else {
            messages.push({
                role: 'assistant',
                content: `Error: ${data.detail || 'Unknown error'}`
            });
        }
    } catch (error) {
        messages.push({
            role: 'assistant',
            content: `Error: ${error.message}`
        });
    } finally {
        isLoading = false;
        renderMessages();
    }
}

// Render messages
function renderMessages() {
    const chatArea = document.getElementById('chatArea');
    chatArea.innerHTML = '';
    
    messages.forEach(msg => {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${msg.role}`;
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (msg.role === 'user') {
            content.innerHTML = `<div class="message-text">${escapeHtml(msg.content)}</div>`;
        } else {
            content.innerHTML = `<div class="message-markdown">${marked.parse(msg.content)}</div>`;
        }
        
        wrapper.appendChild(content);
        chatArea.appendChild(wrapper);
    });
    
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Show thinking indicator
function showThinking() {
    const chatArea = document.getElementById('chatArea');
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper assistant';
    wrapper.id = 'thinkingIndicator';
    
    wrapper.innerHTML = `
        <div class="message-content">
            <div class="thinking-indicator">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
        </div>
    `;
    
    chatArea.appendChild(wrapper);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Generate image
async function generateImage() {
    const prompt = document.getElementById('imagePrompt').value.trim();
    if (!prompt || isLoading) return;
    
    isLoading = true;
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = `<span data-i18n="generating">${t('generating')}</span>`;
    
    try {
        // 获取图片生成配置
        const endpointUrl = getImageEndpointUrl();
        const apiKey = getImageApiKey();
        const model = getImageModel();
        const size = getImageSize(); 
        
        console.log('config:', { endpointUrl, model, size, apiKey: apiKey ? '***' + apiKey.slice(-4) : 'empty' });
        // 如果没有配置图片生成终端，使用聊天API配置
        const effectiveEndpoint = endpointUrl || getEndpointUrl();
        const effectiveApiKey = apiKey || getApiKey();
        const effectiveModel = model || 'dall-e-3';
        
        
        // 构建完整的图片生成端点
        let finalEndpoint = effectiveEndpoint;
        
        // 如果是OpenAI格式，需要添加图片生成路径
        if (effectiveEndpoint.includes('api.openai.com') && !effectiveEndpoint.includes('/images/generations')) {
            finalEndpoint = effectiveEndpoint.replace(/\/$/, '') + '/images/generations';
        }
        
        const requestBody = {
            prompt,
            model: model || 'qwen-image-plus',
            size: size || '1024*1024',
            n: 1,
            api_key: apiKey,
            endpoint_url: endpointUrl,
            api_type: endpointUrl.includes('dashscope') ? 'aliyun_multimodal' : 'openai'
        };
        
        console.log('发送的请求体:', requestBody);
        const response = await fetch(`${BASE}/api/generate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (response.ok && data.images) {
            const gallery = document.getElementById('imageGallery');
            gallery.innerHTML = '';
            
            data.images.forEach(img => {
                const imgEl = document.createElement('img');
                imgEl.src = img.url;
                imgEl.className = 'generated-image';
                gallery.appendChild(imgEl);
            });
        } else {
            alert(`Error: ${data.detail || 'Failed to generate image'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        isLoading = false;
        btn.disabled = false;
        btn.innerHTML = `<span data-i18n="generateImage">${t('generateImage')}</span>`;
    }
}

// Handle keyboard shortcuts
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Auto resize textarea
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function loadImageEndpointUrl() {
    const imageEndpointUrl = localStorage.getItem('imageEndpointUrl') || '';
    const endpointInput = document.getElementById('imageEndpointUrl');
    if (endpointInput) {
        endpointInput.value = imageEndpointUrl;
    }
}

function saveImageEndpointUrl() {
    const endpointInput = document.getElementById('imageEndpointUrl');
    if (!endpointInput) return;
    const endpointUrl = endpointInput.value.trim();
    localStorage.setItem('imageEndpointUrl', endpointUrl);
}

function getImageEndpointUrl() {
    return localStorage.getItem('imageEndpointUrl') || '';
}

function loadImageApiKey() {
    const imageApiKey = localStorage.getItem('imageApiKey') || '';
    const keyInput = document.getElementById('imageApiKey');
    if (keyInput) {
        keyInput.value = imageApiKey;
    }
}

function saveImageApiKey() {
    const keyInput = document.getElementById('imageApiKey');
    if (!keyInput) return;
    const apiKey = keyInput.value.trim();
    localStorage.setItem('imageApiKey', apiKey);
}

function getImageApiKey() {
    return localStorage.getItem('imageApiKey') || getApiKey(); // 默认使用聊天API Key
}

function loadImageModel() {
    const imageModel = localStorage.getItem('imageModel') || 'qwen-image-plus';
    const modelInput = document.getElementById('imageModel');
    if (modelInput) {
        modelInput.value = imageModel;
    }
}

function saveImageModel() {
    const modelInput = document.getElementById('imageModel');
    if (!modelInput) return;
    const model = modelInput.value.trim();
    localStorage.setItem('imageModel', model || 'qwen-image-plus');
}

function getImageModel() {
    return localStorage.getItem('imageModel') || 'qwen-image-plus';
}

function loadImageSize() {
    const imageSize = localStorage.getItem('imageSize') || '1024*1024';
    const sizeInput = document.getElementById('imageSize');
    if (sizeInput) {
        sizeInput.value = imageSize;
    }
}

function saveImageSize() {
    const sizeInput = document.getElementById('imageSize');
    if (!sizeInput) return;
    const size = sizeInput.value.trim();
    localStorage.setItem('imageSize', size || '1024*1024');
}

function getImageSize() {
    return localStorage.getItem('imageSize') || '1024*1024';
}

// Hide sidebar on small screens so content is visible after selecting a tab
function hideSidebarIfMobile() {
    const sidebar = document.querySelector('.sidebar');
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    if (window.innerWidth <= 768) {
        if (sidebar) sidebar.classList.remove('open');
        if (mobileBtn) mobileBtn.style.display = 'block';
    }
}