// Translation data
const translations = {
    zh: {
        title: "多云聊天平台",
        subtitle: "支持阿里云通义千问和 OpenAI GPT",
        placeholder: "输入消息... (Shift + Enter 换行)",
        send: "发送",
        thinking: "思考中...",
        newChat: "新对话",
        imageGen: "生成图片",
        settings: "设置",
        provider: "云平台",
        model: "模型",
        temperature: "温度",
        maxTokens: "最大令牌数",
        clear: "清空对话",
        aliyun: "阿里云",
        aliyun_image: "阿里云图片",
        openai: "OpenAI",
        chat: "聊天",
        image: "图片生成",
        imagePromptPlaceholder: "描述你想要生成的图片...",
        generateImage: "生成图片",
        generating: "生成中...",
        language: "语言",
        darkMode: "深色模式",
        lightMode: "浅色模式",
        chatHistory: "聊天历史",
        chatHistoryEmpty: "暂无历史记录",
        apiKeySettings: "API 密钥设置",
        modelSettings: "模型设置",
        imageProvider: "图片生成平台",
        customApiKey: "自定义 API Key",
        apiKeyHint: "留空使用默认配置，根据选择的云平台输入对应的 API Key",
        freeUsage: "免费配额",
        quotaHint: "超出后需输入自己的 API Key",
        quotaExceeded: "免费配额已用完，请在设置中输入自己的 API Key",
        endpointUrl: "终端 URL",
        endpointHint: "可选，留空使用默认终端",
        openSourceProject: "开源项目"
    },
    en: {
        title: "Multi-Cloud Chat Platform",
        subtitle: "Powered by Alibaba Qwen and OpenAI GPT",
        placeholder: "Type a message... (Shift + Enter for new line)",
        send: "Send",
        thinking: "Thinking...",
        newChat: "New Chat",
        imageGen: "Generate Image",
        settings: "Settings",
        provider: "Provider",
        model: "Model",
        temperature: "Temperature",
        maxTokens: "Max Tokens",
        clear: "Clear Chat",
        aliyun: "Alibaba Cloud",
        aliyun_image: "Alibaba Cloud Image",
        openai: "OpenAI",
        chat: "Chat",
        image: "Image Generation",
        imagePromptPlaceholder: "Describe the image you want to generate...",
        generateImage: "Generate",
        generating: "Generating...",
        language: "Language",
        darkMode: "Dark Mode",
        lightMode: "Light Mode",
        chatHistory: "Chat History",
        chatHistoryEmpty: "No chat history",
        apiKeySettings: "API Key Settings",
        modelSettings: "Model Settings",
        imageProvider: "Image Generation Provider",
        customApiKey: "Custom API Key",
        apiKeyHint: "Leave empty to use default, enter the API Key for your selected provider",
        freeUsage: "Free Quota",
        quotaHint: "Enter your own API Key after exceeding",
        quotaExceeded: "Free quota exhausted, please enter your own API Key in settings",
        endpointUrl: "Endpoint URL",
        endpointHint: "Optional, leave blank to use default endpoint",
        openSourceProject: "Open Source"
    }
};

let currentLang = localStorage.getItem('language') || 'zh';

function t(key) {
    return translations[currentLang][key] || key;
}

function updateTranslations() {
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });

    // Update provider options
    const providerSelect = document.getElementById('provider');
    if (providerSelect) {
        providerSelect.options[0].text = t('aliyun');
        providerSelect.options[1].text = t('openai');
        providerSelect.options[2].text = t('aliyun_image');
    }
}

function toggleLanguage() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('language', currentLang);
    updateTranslations();
    // Reload app name in new language
    if (window.loadConfig) {
        window.loadConfig();
    }
}

// Initialize translations on load
document.addEventListener('DOMContentLoaded', () => {
    updateTranslations();
});
