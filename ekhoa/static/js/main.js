/**
 * Web UI 前端交互逻辑
 */

// 全局状态
const state = {
    currentConversationId: null,
    conversations: {},
    isStreaming: false,
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    recordingStartTime: null,
    recordingTimer: null,
    currentAudio: null,
    currentAudioUrl: null,
    currentAudioButton: null,
    currentAudioRequestToken: null,
    editingMessageIndex: null
};

// DOM 元素
const elements = {
    sidebar: document.querySelector('.sidebar'),
    menuToggle: document.getElementById('menuToggle'),
    newChatBtn: document.getElementById('newChatBtn'),
    conversationsList: document.getElementById('conversationsList'),
    currentTitle: document.getElementById('currentTitle'),
    clearBtn: document.getElementById('clearBtn'),
    chatContainer: document.getElementById('chatContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    voiceBtn: document.getElementById('voiceBtn'),
    sendBtn: document.getElementById('sendBtn'),
    editIndicator: document.getElementById('editIndicator'),
    editIndicatorText: document.getElementById('editIndicatorText'),
    editCancelBtn: document.getElementById('editCancelBtn'),
    recordingIndicator: document.getElementById('recordingIndicator'),
    recordingTime: document.getElementById('recordingTime'),
    toastContainer: document.getElementById('toastContainer'),
    sensevoiceStatus: document.getElementById('sensevoiceStatus'),
    llamacppStatus: document.getElementById('llamacppStatus')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadConversations();
    checkServiceStatus();
});

// 事件监听器初始化
function initEventListeners() {
    // 菜单切换
    elements.menuToggle.addEventListener('click', toggleSidebar);
    
    // 新建对话
    elements.newChatBtn.addEventListener('click', createNewConversation);
    
    // 清空对话
    elements.clearBtn.addEventListener('click', clearAllConversations);
    
    // 发送消息
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 自动调整输入框高度
    elements.messageInput.addEventListener('input', autoResizeTextarea);
    
    // 语音按钮
    elements.voiceBtn.addEventListener('click', toggleRecording);
    elements.editCancelBtn.addEventListener('click', () => resetEditMode({ preserveInput: false }));
    
    // 点击侧边栏外部关闭
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            !elements.sidebar.contains(e.target) && 
            !elements.menuToggle.contains(e.target)) {
            elements.sidebar.classList.remove('open');
        }
    });
}

// 切换侧边栏
function toggleSidebar() {
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.toggle('open');
    } else {
        elements.sidebar.classList.toggle('collapsed');
    }
}

// 自动调整文本框高度
function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 150) + 'px';
}

// 加载对话列表
async function loadConversations(reloadCurrentConversation = false) {
    try {
        const response = await fetch('/api/conversations');
        const data = await response.json();
        
        if (data.success) {
            state.conversations = {};
            renderConversationsList(data.conversations);
            
            if (
                data.current_conversation_id &&
                (reloadCurrentConversation || state.currentConversationId !== data.current_conversation_id)
            ) {
                selectConversation(data.current_conversation_id, reloadCurrentConversation);
            }
        }
    } catch (error) {
        showToast('加载对话列表失败', 'error');
        console.error('加载对话列表失败:', error);
    }
}

// 渲染对话列表
function renderConversationsList(conversations) {
    elements.conversationsList.innerHTML = '';
    
    if (conversations.length === 0) {
        elements.conversationsList.innerHTML = `
            <div class="no-conversations">
                暂无对话
            </div>
        `;
        return;
    }
    
    conversations.forEach(conv => {
        state.conversations[conv.id] = conv;
        
        const item = document.createElement('div');
        item.className = 'conversation-item' + (conv.id === state.currentConversationId ? ' active' : '');
        item.dataset.id = conv.id;
        item.innerHTML = `
            <span class="conv-title">${escapeHtml(conv.title)}</span>
            <button class="delete-btn" onclick="deleteConversation('${conv.id}', event)">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        
        item.addEventListener('click', (e) => {
            if (!e.target.closest('.delete-btn')) {
                selectConversation(conv.id);
            }
        });
        
        elements.conversationsList.appendChild(item);
    });
}

// 选择对话
async function selectConversation(conversationId, force = false) {
    if (!force && state.currentConversationId === conversationId) return;
    
    state.currentConversationId = conversationId;
    
    // 更新UI
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id === conversationId);
    });
    
    // 加载对话内容
    try {
        const response = await fetch(`/api/conversation/${conversationId}`);
        const data = await response.json();
        
        if (data.success) {
            renderConversation(data.conversation);
            elements.currentTitle.textContent = data.conversation.title || '新对话';
            
            // 移动端关闭侧边栏
            if (window.innerWidth <= 768) {
                elements.sidebar.classList.remove('open');
            }
        }
    } catch (error) {
        showToast('加载对话失败', 'error');
        console.error('加载对话失败:', error);
    }
}

// 渲染对话内容
function renderConversation(conversation) {
    stopCurrentAudio();
    resetEditMode({ preserveInput: false });
    state.currentConversationId = conversation.id;
    
    if (!conversation.messages || conversation.messages.length === 0) {
        elements.welcomeScreen.classList.remove('hidden');
        elements.messagesContainer.classList.remove('visible');
        elements.messagesContainer.innerHTML = '';
        return;
    }
    
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('visible');
    elements.messagesContainer.innerHTML = '';
    
    conversation.messages.forEach((msg, index) => {
        appendMessage(msg, false, index);
    });
    
    scrollToBottom();
}

// 追加消息
function appendMessage(msg, scroll = true, index = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = msg.content;
    messageDiv.appendChild(contentDiv);

    if (msg.role === 'user') {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';

        if (msg.voice) {
            metaDiv.insertAdjacentHTML('beforeend', `
                <span class="voice-indicator">
                    <i class="fas fa-microphone"></i>
                    语音输入
                </span>
            `);
        }

        if (msg.edited) {
            metaDiv.insertAdjacentHTML('beforeend', `
                <span class="message-edited-flag">
                    <i class="fas fa-pen"></i>
                    已编辑
                </span>
            `);
        }

        if (index !== null) {
            metaDiv.appendChild(createEditButton(index, msg.content));
        }

        if (metaDiv.childElementCount > 0) {
            messageDiv.appendChild(metaDiv);
        }
    } else if (msg.role === 'assistant') {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';

        if (msg.timings) {
            metaDiv.insertAdjacentHTML('beforeend', renderTimings(msg.timings, msg.voice));
        }

        metaDiv.appendChild(createAudioPlayButton(msg.content));
        messageDiv.appendChild(metaDiv);
    }
    
    elements.messagesContainer.appendChild(messageDiv);
    
    if (scroll) {
        scrollToBottom();
    }
}

function createStreamingAssistantMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(metaDiv);
    elements.messagesContainer.appendChild(messageDiv);

    return { messageDiv, contentDiv, metaDiv };
}

function updateStreamingAssistantMessage(streamingMessage, content) {
    streamingMessage.contentDiv.textContent = content;
    scrollToBottom();
}

function finalizeStreamingAssistantMessage(streamingMessage, content, timings = null) {
    streamingMessage.contentDiv.textContent = content;
    streamingMessage.metaDiv.innerHTML = '';

    if (timings) {
        streamingMessage.metaDiv.insertAdjacentHTML('beforeend', renderTimings(timings));
    }

    streamingMessage.metaDiv.appendChild(createAudioPlayButton(content));

    scrollToBottom();
}

function createAudioPlayButton(text) {
    const button = document.createElement('button');
    button.className = 'audio-play-btn message-action-btn';
    button.dataset.audioText = text;
    setAudioButtonState(button, 'idle');
    button.addEventListener('click', () => toggleAudioPlayback(button));
    return button;
}

function createEditButton(index, text) {
    const button = document.createElement('button');
    button.className = 'message-action-btn';
    button.type = 'button';
    button.innerHTML = `
        <i class="fas fa-pen"></i>
        编辑
    `;
    button.addEventListener('click', () => enterEditMode(index, text));
    return button;
}

function setAudioButtonState(button, mode) {
    if (!button) return;

    button.classList.remove('is-loading', 'is-playing', 'is-paused');

    switch (mode) {
        case 'loading':
            button.classList.add('is-loading');
            button.disabled = true;
            button.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                生成中
            `;
            break;
        case 'playing':
            button.classList.add('is-playing');
            button.disabled = false;
            button.innerHTML = `
                <i class="fas fa-pause"></i>
                暂停
            `;
            break;
        case 'paused':
            button.classList.add('is-paused');
            button.disabled = false;
            button.innerHTML = `
                <i class="fas fa-play"></i>
                继续
            `;
            break;
        default:
            button.disabled = false;
            button.innerHTML = `
                <i class="fas fa-volume-up"></i>
                播放
            `;
            break;
    }
}

function stopCurrentAudio(resetButton = true) {
    if (state.currentAudio) {
        state.currentAudio.pause();
        state.currentAudio.currentTime = 0;
    }

    if (state.currentAudioUrl) {
        URL.revokeObjectURL(state.currentAudioUrl);
    }

    if (resetButton && state.currentAudioButton) {
        setAudioButtonState(state.currentAudioButton, 'idle');
    }

    state.currentAudio = null;
    state.currentAudioUrl = null;
    state.currentAudioButton = null;
    state.currentAudioRequestToken = null;
}

function bindAudioLifecycle(audio, button, audioUrl, requestToken) {
    audio.onended = () => {
        if (state.currentAudioRequestToken !== requestToken) return;
        stopCurrentAudio();
    };

    audio.onerror = () => {
        if (state.currentAudioRequestToken !== requestToken) return;
        showToast('播放失败', 'error');
        stopCurrentAudio();
    };
}

function enterEditMode(index, text) {
    if (state.isStreaming || state.isRecording) {
        showToast('当前处理中，暂时不能编辑消息', 'error');
        return;
    }

    stopCurrentAudio();
    state.editingMessageIndex = index;
    elements.messageInput.value = text;
    autoResizeTextarea();
    elements.messageInput.focus();
    elements.editIndicatorText.textContent = `正在编辑第 ${index + 1} 条用户消息，发送后将覆盖该轮内容`;
    elements.editIndicator.classList.add('visible');
}

function resetEditMode(options = {}) {
    const { preserveInput = true } = options;
    state.editingMessageIndex = null;
    elements.editIndicator.classList.remove('visible');
    elements.editIndicatorText.textContent = '正在编辑消息';

    if (!preserveInput) {
        elements.messageInput.value = '';
        elements.messageInput.style.height = 'auto';
    }
}

async function toggleAudioPlayback(button) {
    const text = button.dataset.audioText;
    if (!text) return;

    if (state.currentAudioButton === button && state.currentAudio) {
        if (state.currentAudio.paused) {
            try {
                await state.currentAudio.play();
                setAudioButtonState(button, 'playing');
            } catch (error) {
                showToast('继续播放失败', 'error');
                console.error('继续播放失败:', error);
                stopCurrentAudio();
            }
        } else {
            state.currentAudio.pause();
            setAudioButtonState(button, 'paused');
        }
        return;
    }

    await playAudio(text, button);
}

// 显示正在输入的动画
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// 隐藏正在输入的动画
function hideTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

function parseSsePayload(eventBlock) {
    const dataLines = eventBlock
        .split('\n')
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trim());

    if (dataLines.length === 0) {
        return null;
    }

    try {
        return JSON.parse(dataLines.join('\n'));
    } catch (error) {
        console.error('解析流式响应失败:', error);
        return null;
    }
}

// 格式化时间（毫秒转秒）
function formatTime(ms) {
    const seconds = ms / 1000;
    return seconds.toFixed(2) + 's';
}

// 渲染时间统计
function renderTimings(timings, isVoice = false) {
    const items = [];
    
    if (isVoice && timings.record) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-microphone"></i>
                录音: ${formatTime(timings.record)}
            </span>
        `);
    }
    
    if (timings.convert) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-exchange-alt"></i>
                转换: ${formatTime(timings.convert)}
            </span>
        `);
    }
    
    if (timings.asr) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-headphones"></i>
                识别: ${formatTime(timings.asr)}
            </span>
        `);
    }
    
    if (timings.classify) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-tags"></i>
                分类: ${formatTime(timings.classify)}
            </span>
        `);
    }
    
    if (timings.ai) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-brain"></i>
                AI: ${formatTime(timings.ai)}
            </span>
        `);
    }
    
    if (timings.total) {
        items.push(`
            <span class="timing-item timing-item-total">
                <i class="fas fa-clock"></i>
                总计: ${formatTime(timings.total)}
            </span>
        `);
    }
    
    return `<div class="timings">${items.join('')}</div>`;
}

// 创建新对话
async function createNewConversation() {
    try {
        resetEditMode({ preserveInput: false });
        const response = await fetch('/api/conversation/new', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            state.currentConversationId = data.conversation_id;
            loadConversations();
            renderConversation(data.conversation);
            elements.currentTitle.textContent = '新对话';
            
            // 移动端关闭侧边栏
            if (window.innerWidth <= 768) {
                elements.sidebar.classList.remove('open');
            }
        }
    } catch (error) {
        showToast('创建对话失败', 'error');
        console.error('创建对话失败:', error);
    }
}

// 删除对话
async function deleteConversation(conversationId, event) {
    event.stopPropagation();
    
    if (!confirm('确定要删除这个对话吗？')) return;
    
    try {
        const response = await fetch(`/api/conversation/${conversationId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            if (state.currentConversationId === conversationId) {
                stopCurrentAudio();
                resetEditMode({ preserveInput: false });
                state.currentConversationId = null;
                elements.welcomeScreen.classList.remove('hidden');
                elements.messagesContainer.classList.remove('visible');
                elements.messagesContainer.innerHTML = '';
                elements.currentTitle.textContent = '新对话';
            }
            loadConversations();
            showToast('对话已删除', 'success');
        }
    } catch (error) {
        showToast('删除对话失败', 'error');
        console.error('删除对话失败:', error);
    }
}

// 清空所有对话
async function clearAllConversations() {
    if (!confirm('确定要清空所有对话吗？此操作不可恢复。')) return;
    
    try {
        const response = await fetch('/api/clear', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            stopCurrentAudio();
            resetEditMode({ preserveInput: false });
            state.currentConversationId = null;
            state.conversations = {};
            elements.welcomeScreen.classList.remove('hidden');
            elements.messagesContainer.classList.remove('visible');
            elements.messagesContainer.innerHTML = '';
            elements.currentTitle.textContent = '新对话';
            loadConversations();
            showToast('所有对话已清空', 'success');
        }
    } catch (error) {
        showToast('清空失败', 'error');
        console.error('清空失败:', error);
    }
}

// 发送消息
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || state.isStreaming) return;

    if (state.editingMessageIndex !== null) {
        await submitEditedMessage(message);
        return;
    }
    
    // 显示消息容器
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('visible');
    
    // 添加用户消息
    appendMessage({ role: 'user', content: message });
    
    // 清空输入框
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    
    // 显示正在输入动画
    showTypingIndicator();
    state.isStreaming = true;
    elements.sendBtn.disabled = true;
    elements.voiceBtn.disabled = true;

    let streamingMessage = null;
    let fullReply = '';
    let streamCompleted = false;
    
    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: state.currentConversationId
            })
        });

        if (!response.ok) {
            let errorMessage = '发送失败';
            try {
                const data = await response.json();
                errorMessage = data.error || errorMessage;
            } catch {
                // 非 JSON 错误响应时使用默认文案
            }
            throw new Error(errorMessage);
        }

        if (!response.body) {
            throw new Error('当前环境不支持流式响应');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        const handlePayload = (payload) => {
            if (!payload) return;

            if (payload.type === 'start') {
                if (payload.conversation_id) {
                    state.currentConversationId = payload.conversation_id;
                }
                return;
            }

            if (payload.type === 'chunk') {
                if (!streamingMessage) {
                    hideTypingIndicator();
                    streamingMessage = createStreamingAssistantMessage();
                }

                if (payload.conversation_id) {
                    state.currentConversationId = payload.conversation_id;
                }

                fullReply += payload.content || '';
                updateStreamingAssistantMessage(streamingMessage, fullReply);
                return;
            }

            if (payload.type === 'done') {
                hideTypingIndicator();

                if (!streamingMessage) {
                    streamingMessage = createStreamingAssistantMessage();
                }

                if (payload.conversation_id) {
                    state.currentConversationId = payload.conversation_id;
                }

                finalizeStreamingAssistantMessage(
                    streamingMessage,
                    fullReply,
                    payload.timings || null
                );

                elements.currentTitle.textContent = message.slice(0, 20) + (message.length > 20 ? '...' : '');
                loadConversations(true);
                streamCompleted = true;
                return;
            }

            if (payload.type === 'error') {
                throw new Error(payload.error || '发送失败');
            }
        };

        while (true) {
            const { value, done } = await reader.read();
            buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });

            const events = buffer.split('\n\n');
            buffer = events.pop() || '';

            for (const eventBlock of events) {
                handlePayload(parseSsePayload(eventBlock));
            }

            if (done) {
                break;
            }
        }

        if (buffer.trim()) {
            handlePayload(parseSsePayload(buffer.trim()));
        }

        if (!streamCompleted) {
            throw new Error('流式响应已中断，请重试');
        }

    } catch (error) {
        hideTypingIndicator();
        if (streamingMessage && fullReply) {
            finalizeStreamingAssistantMessage(streamingMessage, fullReply);
        }
        showToast(error.message || '发送失败，请检查网络连接', 'error');
        console.error('发送失败:', error);
    } finally {
        state.isStreaming = false;
        elements.sendBtn.disabled = false;
        elements.voiceBtn.disabled = false;
    }
}

async function submitEditedMessage(message) {
    if (!state.currentConversationId) {
        resetEditMode({ preserveInput: false });
        return;
    }

    state.isStreaming = true;
    elements.sendBtn.disabled = true;
    elements.voiceBtn.disabled = true;
    stopCurrentAudio();

    const messageIndex = state.editingMessageIndex;

    try {
        const response = await fetch(`/api/conversation/${state.currentConversationId}/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_index: messageIndex,
                message
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || '编辑失败');
        }

        renderConversation(data.conversation);
        elements.currentTitle.textContent = data.conversation.title || '新对话';
        loadConversations();
        showToast('已覆盖原输入并重新生成回复', 'success');
    } catch (error) {
        showToast(error.message || '编辑失败', 'error');
        console.error('编辑失败:', error);
    } finally {
        state.isStreaming = false;
        elements.sendBtn.disabled = false;
        elements.voiceBtn.disabled = false;
    }
}

// 切换录音状态
async function toggleRecording() {
    if (state.isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

// 开始录音
async function startRecording() {
    if (state.editingMessageIndex !== null) {
        resetEditMode({ preserveInput: false });
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        state.recordingStartTime = Date.now();
        
        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };
        
        state.mediaRecorder.onstop = () => {
            processRecording();
            stream.getTracks().forEach(track => track.stop());
        };
        
        state.mediaRecorder.start();
        state.isRecording = true;
        
        // 更新UI
        elements.voiceBtn.classList.add('recording');
        elements.recordingIndicator.classList.add('visible');
        
        // 开始计时
        state.recordingTimer = setInterval(updateRecordingTime, 100);
        
    } catch (error) {
        showToast('无法访问麦克风，请检查权限设置', 'error');
        console.error('麦克风访问失败:', error);
    }
}

// 停止录音
function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        
        // 更新UI
        elements.voiceBtn.classList.remove('recording');
        elements.recordingIndicator.classList.remove('visible');
        
        // 停止计时
        if (state.recordingTimer) {
            clearInterval(state.recordingTimer);
            state.recordingTimer = null;
        }
    }
}

// 更新录音时间显示
function updateRecordingTime() {
    const elapsed = Date.now() - state.recordingStartTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const displaySeconds = seconds % 60;
    elements.recordingTime.textContent = 
        `${minutes.toString().padStart(2, '0')}:${displaySeconds.toString().padStart(2, '0')}`;
}

// 处理录音
async function processRecording() {
    if (state.audioChunks.length === 0) {
        showToast('录音为空', 'error');
        return;
    }
    
    const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
    
    // 显示消息容器
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('visible');
    
    // 显示正在输入动画
    showTypingIndicator();
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        if (state.currentConversationId) {
            formData.append('conversation_id', state.currentConversationId);
        }
        
        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // 隐藏正在输入动画
        hideTypingIndicator();
        
        if (data.success) {
            state.currentConversationId = data.conversation_id;
            
            // 添加用户消息
            appendMessage({
                role: 'user',
                content: data.recognized_text,
                voice: true
            });
            
            // 添加助手消息
            appendMessage({
                role: 'assistant',
                content: data.reply,
                voice: true,
                timings: data.timings
            });
            
            // 更新标题
            loadConversations(true);
            elements.currentTitle.textContent = data.recognized_text.slice(0, 20) + 
                (data.recognized_text.length > 20 ? '...' : '');
        } else {
            showToast(data.error || '语音识别失败', 'error');
        }
    } catch (error) {
        hideTypingIndicator();
        showToast('语音处理失败', 'error');
        console.error('语音处理失败:', error);
    }
}

// 播放音频
async function playAudio(text, button = null) {
    const activeButton = button || state.currentAudioButton;
    const requestToken = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    stopCurrentAudio();

    state.currentAudioButton = activeButton;
    state.currentAudioRequestToken = requestToken;
    setAudioButtonState(activeButton, 'loading');

    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            let errorMessage = '语音合成失败';
            try {
                const data = await response.json();
                errorMessage = data.error || errorMessage;
            } catch {
                // 忽略非 JSON 错误响应
            }
            throw new Error(errorMessage);
        }

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('audio/wav')) {
            let errorMessage = '服务器未返回可播放音频';
            try {
                const data = await response.json();
                errorMessage = data.error || errorMessage;
            } catch {
                // 响应不是 JSON 时使用默认文案
            }
            throw new Error(errorMessage);
        }

        const audioBlob = await response.blob();

        if (!audioBlob.size) {
            throw new Error('生成的音频内容为空');
        }

        if (state.currentAudioRequestToken !== requestToken) {
            return;
        }

        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        state.currentAudio = audio;
        state.currentAudioUrl = audioUrl;
        state.currentAudioButton = activeButton;

        bindAudioLifecycle(audio, activeButton, audioUrl, requestToken);

        await audio.play();
        setAudioButtonState(activeButton, 'playing');
    } catch (error) {
        showToast(error.message || '播放失败', 'error');
        console.error('播放失败:', error);
        if (state.currentAudioRequestToken === requestToken) {
            stopCurrentAudio();
        }
    }
}

// 检查服务状态
async function checkServiceStatus() {
    // 检查 SenseVoice 状态
    try {
        const response = await fetch('/api/conversations', { 
            method: 'GET',
            signal: AbortSignal.timeout(3000)
        });
        if (response.ok) {
            elements.sensevoiceStatus.classList.add('online');
        } else {
            elements.sensevoiceStatus.classList.add('offline');
        }
    } catch {
        elements.sensevoiceStatus.classList.add('offline');
    }
    
    // llama.cpp 状态通过实际调用才能确认，这里暂时显示为在线
    elements.llamacppStatus.classList.add('online');
}

// 显示 Toast 提示
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 滚动到底部
function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 全局函数暴露
window.deleteConversation = deleteConversation;
window.playAudio = playAudio;
