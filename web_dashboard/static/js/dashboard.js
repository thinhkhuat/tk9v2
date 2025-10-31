/**
 * Dashboard Main JavaScript
 * Handles form submission, real-time updates, and file downloads
 */
class Dashboard {
    constructor() {
        this.wsClient = new WebSocketClient();
        this.currentSessionId = null;
        this.scrollLocked = false;
        this.currentView = 'new-research'; // 'new-research' or 'browse-sessions'
        
        this.initializeElements();
        this.setupEventListeners();
        this.startHealthCheck();
        
        console.log('Dashboard initialized');
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // Form elements
        this.researchSubject = document.getElementById('research-subject');
        this.languageSelect = document.getElementById('language-select');
        this.submitBtn = document.getElementById('submit-btn');
        this.charCount = document.getElementById('char-count');
        
        // Section elements
        this.researchForm = document.getElementById('research-form');
        this.progressSection = document.getElementById('progress-section');
        this.logSection = document.getElementById('log-section');
        this.downloadSection = document.getElementById('download-section');
        this.errorSection = document.getElementById('error-section');
        this.loadingOverlay = document.getElementById('loading-overlay');
        
        // Tab elements
        this.newResearchTab = document.getElementById('new-research-tab');
        this.browseSessionsTab = document.getElementById('browse-sessions-tab');
        this.browseSessionsSection = document.getElementById('browse-sessions');
        
        // Browse sessions elements
        this.sessionsLoading = document.getElementById('sessions-loading');
        this.sessionsList = document.getElementById('sessions-list');
        this.sessionsEmpty = document.getElementById('sessions-empty');
        this.refreshSessionsBtn = document.getElementById('refresh-sessions');
        
        // Progress elements
        this.sessionIdSpan = document.getElementById('session-id');
        this.progressFill = document.getElementById('progress-fill');
        this.statusItems = {
            connecting: document.getElementById('status-connecting'),
            running: document.getElementById('status-running'),
            processing: document.getElementById('status-processing'),
            complete: document.getElementById('status-complete')
        };
        
        // Log elements
        this.logOutput = document.getElementById('log-output');
        this.clearLogBtn = document.getElementById('clear-log');
        this.scrollLockBtn = document.getElementById('scroll-lock');
        
        // Download elements
        this.downloadFiles = document.getElementById('download-files');
        
        // Action buttons
        this.newResearchBtn = document.getElementById('new-research');
        this.newResearchErrorBtn = document.getElementById('new-research-error');
        this.retryResearchBtn = document.getElementById('retry-research');
        
        // Tab navigation
        this.newResearchTab.addEventListener('click', () => this.switchView('new-research'));
        this.browseSessionsTab.addEventListener('click', () => this.switchView('browse-sessions'));
        
        // Browse sessions controls
        this.refreshSessionsBtn.addEventListener('click', () => this.loadResearchSessions());
        
        // Error elements
        this.errorMessage = document.getElementById('error-message');
        
        // Health indicator
        this.healthIndicator = document.getElementById('health-indicator');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Form submission
        this.submitBtn.addEventListener('click', () => this.submitResearch());
        this.researchSubject.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.submitResearch();
            }
        });
        
        // Character counter
        this.researchSubject.addEventListener('input', () => this.updateCharCount());
        
        // Log controls
        this.clearLogBtn.addEventListener('click', () => this.clearLog());
        this.scrollLockBtn.addEventListener('click', () => this.toggleScrollLock());
        
        // Action buttons
        this.newResearchBtn.addEventListener('click', () => this.startNewResearch());
        this.newResearchErrorBtn.addEventListener('click', () => this.startNewResearch());
        this.retryResearchBtn.addEventListener('click', () => this.retryResearch());
        
        // WebSocket event handlers
        this.setupWebSocketHandlers();
        
        // Initialize character counter
        this.updateCharCount();
    }

    /**
     * Setup WebSocket message handlers
     */
    setupWebSocketHandlers() {
        this.wsClient.on('connection', (data) => {
            console.log('Connected to research session');
            this.updateStatus('connecting', true);
        });

        this.wsClient.on('log', (data) => {
            this.appendLog(data.message);
            this.updateStatus('running', true);
        });

        this.wsClient.on('completed', (data) => {
            console.log('Research completed');
            this.updateStatus('complete', true);
            this.setProgress(100);
            
            // Wait a moment then check for files
            setTimeout(() => {
                this.checkForFiles();
            }, 2000);
        });

        this.wsClient.on('files_ready', (data) => {
            console.log('Files ready for download', data.files);
            this.showDownloadSection(data.files);
        });

        this.wsClient.on('error', (data) => {
            console.error('Research error:', data.message);
            this.showError(data.message);
        });
    }

    /**
     * Submit research request
     */
    async submitResearch() {
        const subject = this.researchSubject.value.trim();
        const language = this.languageSelect.value;
        
        if (!subject) {
            alert('Please enter a research subject');
            return;
        }
        
        if (subject.length < 3) {
            alert('Research subject must be at least 3 characters long');
            return;
        }
        
        try {
            this.showLoading(true);
            this.submitBtn.disabled = true;
            
            console.log('Submitting research request:', { subject, language });
            
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    subject: subject,
                    language: language,
                    save_files: true
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit research request');
            }
            
            const data = await response.json();
            console.log('Research request submitted:', data);
            
            this.currentSessionId = data.session_id;
            this.startResearchSession(data.session_id);
            
        } catch (error) {
            console.error('Error submitting research:', error);
            this.showError(error.message);
            this.submitBtn.disabled = false;
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Start research session
     */
    startResearchSession(sessionId) {
        console.log('Starting research session:', sessionId);
        
        // Show progress section
        this.showSection('progress');
        this.sessionIdSpan.textContent = sessionId;
        
        // Reset progress
        this.resetProgress();
        this.clearLog();
        
        // Connect to WebSocket
        this.wsClient.connect(sessionId);
        
        // Show log section
        setTimeout(() => {
            this.showSection('log');
        }, 1000);
    }

    /**
     * Show specific section
     */
    showSection(sectionName) {
        // Hide all sections first
        this.researchForm.style.display = 'none';
        this.progressSection.style.display = 'none';
        this.logSection.style.display = 'none';
        this.downloadSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        
        // Show specific section
        switch (sectionName) {
            case 'form':
                this.researchForm.style.display = 'block';
                break;
            case 'progress':
                this.progressSection.style.display = 'block';
                break;
            case 'log':
                this.logSection.style.display = 'block';
                break;
            case 'download':
                this.downloadSection.style.display = 'block';
                break;
            case 'error':
                this.errorSection.style.display = 'block';
                break;
        }
    }

    /**
     * Update character counter
     */
    updateCharCount() {
        const count = this.researchSubject.value.length;
        this.charCount.textContent = count;
        
        if (count > 450) {
            this.charCount.style.color = '#dc3545';
        } else if (count > 400) {
            this.charCount.style.color = '#ffc107';
        } else {
            this.charCount.style.color = '#666';
        }
    }

    /**
     * Append log message
     */
    appendLog(message) {
        this.logOutput.textContent += message + '\n';
        
        // Auto-scroll to bottom unless locked
        if (!this.scrollLocked) {
            this.logOutput.scrollTop = this.logOutput.scrollHeight;
        }
    }

    /**
     * Clear log output
     */
    clearLog() {
        this.logOutput.textContent = '';
    }

    /**
     * Toggle scroll lock
     */
    toggleScrollLock() {
        this.scrollLocked = !this.scrollLocked;
        this.scrollLockBtn.classList.toggle('active', this.scrollLocked);
        
        const icon = this.scrollLockBtn.querySelector('i');
        if (this.scrollLocked) {
            icon.className = 'fas fa-lock';
            this.scrollLockBtn.querySelector('span') ? 
                this.scrollLockBtn.querySelector('span').textContent = ' Lock Scroll' : null;
        } else {
            icon.className = 'fas fa-unlock';
            this.scrollLockBtn.querySelector('span') ? 
                this.scrollLockBtn.querySelector('span').textContent = ' Unlock Scroll' : null;
        }
    }

    /**
     * Update status indicators
     */
    updateStatus(statusName, active) {
        if (this.statusItems[statusName]) {
            if (active) {
                this.statusItems[statusName].classList.add('active');
            } else {
                this.statusItems[statusName].classList.remove('active');
            }
        }
    }

    /**
     * Set progress percentage
     */
    setProgress(percentage) {
        this.progressFill.style.width = `${percentage}%`;
    }

    /**
     * Reset progress indicators
     */
    resetProgress() {
        Object.values(this.statusItems).forEach(item => {
            item.classList.remove('active', 'completed');
        });
        this.setProgress(0);
    }

    /**
     * Check for files
     */
    async checkForFiles() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/api/session/${this.currentSessionId}`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.files && data.files.length > 0) {
                    this.showDownloadSection(data.files);
                } else {
                    // Wait a bit more and check again
                    setTimeout(() => this.checkForFiles(), 3000);
                }
            }
        } catch (error) {
            console.error('Error checking for files:', error);
        }
    }

    /**
     * Show download section
     */
    showDownloadSection(files) {
        this.updateStatus('processing', true);
        
        // Clear existing download files
        this.downloadFiles.innerHTML = '';
        
        if (!files || files.length === 0) {
            this.downloadFiles.innerHTML = `
                <div class="no-files-message">
                    <i class="fas fa-info-circle"></i>
                    <p>No files were generated for this research session.</p>
                    <p>This might be due to an error during the research process.</p>
                </div>
            `;
        } else {
            // Add download all button at the top
            const downloadHeader = document.createElement('div');
            downloadHeader.className = 'download-header';
            downloadHeader.innerHTML = `
                <h3>Download Files</h3>
                <button class="download-all-btn btn btn-primary" data-session-id="${this.currentSessionId}">
                    <i class="fas fa-file-archive"></i> Download All as ZIP
                </button>
            `;
            this.downloadFiles.appendChild(downloadHeader);

            // Group files by language and type for better organization
            const groupedFiles = this.groupFilesByLanguage(files);

            // Create sections for different languages
            Object.keys(groupedFiles).forEach(language => {
                const languageSection = this.createLanguageSection(language, groupedFiles[language]);
                this.downloadFiles.appendChild(languageSection);
            });

            // Enhance download section with preview buttons
            if (window.enhancedDownloads) {
                window.enhancedDownloads.enhanceDownloadSection(this.currentSessionId, files);
            }
        }
        
        // Show download section
        setTimeout(() => {
            this.showSection('download');
            this.updateStatus('complete', true);
        }, 1000);
    }

    /**
     * Create download file element
     */
    createDownloadFileElement(file) {
        const div = document.createElement('div');
        div.className = 'download-file';
        
        const fileSize = file.size ? this.formatFileSize(file.size) : 'Unknown size';
        const fileType = this.getFileTypeIcon(file.filename);
        
        div.innerHTML = `
            <div class="file-info">
                <div class="file-name">
                    <i class="fas ${fileType}"></i> ${file.filename}
                </div>
                <div class="file-meta">
                    Size: ${fileSize} • Created: ${new Date(file.created).toLocaleString()}
                </div>
            </div>
            <a href="${file.url}" class="download-btn" download="${file.filename}">
                <i class="fas fa-download"></i> Download
            </a>
        `;
        
        return div;
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Get file type icon
     */
    getFileTypeIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'pdf': return 'fa-file-pdf';
            case 'docx': return 'fa-file-word';
            case 'md': return 'fa-file-alt';
            default: return 'fa-file';
        }
    }
    
    /**
     * Group files by language for better organization
     */
    groupFilesByLanguage(files) {
        const groups = {
            'English': [],
            'Vietnamese': [],
            'Other': []
        };
        
        files.forEach(file => {
            if (file.filename.includes('_vi.')) {
                groups['Vietnamese'].push(file);
            } else if (file.filename.includes('_en.') || !file.filename.includes('_')) {
                groups['English'].push(file);
            } else {
                groups['Other'].push(file);
            }
        });
        
        // Remove empty groups
        Object.keys(groups).forEach(key => {
            if (groups[key].length === 0) {
                delete groups[key];
            }
        });
        
        return groups;
    }
    
    /**
     * Create a language section for downloads
     */
    createLanguageSection(language, files) {
        const section = document.createElement('div');
        section.className = 'language-section';
        
        const header = document.createElement('h4');
        header.className = 'language-header';
        header.innerHTML = `
            <i class="fas fa-language"></i> ${language} 
            <span class="file-count">(${files.length} files)</span>
        `;
        
        const filesContainer = document.createElement('div');
        filesContainer.className = 'language-files';
        
        files.forEach(file => {
            const fileElement = this.createDownloadFileElement(file);
            filesContainer.appendChild(fileElement);
        });
        
        section.appendChild(header);
        section.appendChild(filesContainer);
        
        return section;
    }

    /**
     * Show error message
     */
    showError(message) {
        this.errorMessage.textContent = message;
        this.showSection('error');
        this.showLoading(false);
        this.submitBtn.disabled = false;
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    /**
     * Start new research
     */
    startNewResearch() {
        // Close WebSocket connection
        this.wsClient.close();
        this.currentSessionId = null;
        
        // Reset form
        this.researchSubject.value = '';
        this.languageSelect.value = 'vi';
        this.updateCharCount();
        this.submitBtn.disabled = false;
        
        // Show form
        this.showSection('form');
        
        // Focus on input
        this.researchSubject.focus();
    }

    /**
     * Retry research with same parameters
     */
    retryResearch() {
        this.submitResearch();
    }

    /**
     * Start health check
     */
    startHealthCheck() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/health');
                if (response.ok) {
                    this.healthIndicator.className = 'health-ok';
                    this.healthIndicator.innerHTML = '<i class="fas fa-circle"></i> System Healthy';
                } else {
                    this.healthIndicator.className = 'health-error';
                    this.healthIndicator.innerHTML = '<i class="fas fa-circle"></i> System Error';
                }
            } catch (error) {
                this.healthIndicator.className = 'health-error';
                this.healthIndicator.innerHTML = '<i class="fas fa-circle"></i> Connection Error';
            }
        }, 30000); // Check every 30 seconds
    }

    /**
     * Switch between views (new research vs browse sessions)
     */
    switchView(view) {
        this.currentView = view;
        
        // Update tab states
        this.newResearchTab.classList.toggle('active', view === 'new-research');
        this.browseSessionsTab.classList.toggle('active', view === 'browse-sessions');
        
        // Show/hide sections
        if (view === 'new-research') {
            this.showSection('form');
            this.browseSessionsSection.style.display = 'none';
        } else if (view === 'browse-sessions') {
            this.hideAllSections();
            this.browseSessionsSection.style.display = 'block';
            this.loadResearchSessions();
        }
    }
    
    /**
     * Hide all main sections
     */
    hideAllSections() {
        this.researchForm.style.display = 'none';
        this.progressSection.style.display = 'none';
        this.logSection.style.display = 'none';
        this.downloadSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }

    /**
     * Load and display all research sessions
     */
    async loadResearchSessions() {
        console.log('Loading research sessions...');
        
        // Show loading state
        this.sessionsLoading.style.display = 'block';
        this.sessionsList.style.display = 'none';
        this.sessionsEmpty.style.display = 'none';
        
        try {
            const response = await fetch('/api/sessions');
            
            if (!response.ok) {
                throw new Error('Failed to fetch sessions');
            }
            
            const sessions = await response.json();
            console.log('Loaded sessions:', sessions);
            
            // Hide loading state
            this.sessionsLoading.style.display = 'none';
            
            if (sessions.length === 0) {
                this.sessionsEmpty.style.display = 'block';
            } else {
                this.displaySessions(sessions);
                this.sessionsList.style.display = 'block';
            }
            
        } catch (error) {
            console.error('Error loading sessions:', error);
            this.sessionsLoading.style.display = 'none';
            this.sessionsEmpty.style.display = 'block';
        }
    }

    /**
     * Display research sessions in the UI
     */
    displaySessions(sessions) {
        this.sessionsList.innerHTML = '';
        
        sessions.forEach(session => {
            const sessionElement = this.createSessionElement(session);
            this.sessionsList.appendChild(sessionElement);
        });
    }

    /**
     * Create a session element for display
     */
    createSessionElement(session) {
        const div = document.createElement('div');
        div.className = 'session-item';
        
        const createdDate = new Date(session.created).toLocaleString();
        const fileCount = session.file_count || 0;
        
        div.innerHTML = `
            <div class="session-header">
                <div class="session-info">
                    <h3 class="session-subject">${this.escapeHtml(session.subject)}</h3>
                    <div class="session-meta">
                        <span class="session-date">
                            <i class="fas fa-calendar"></i> ${createdDate}
                        </span>
                        <span class="session-files">
                            <i class="fas fa-file"></i> ${fileCount} files
                        </span>
                    </div>
                </div>
                <button class="expand-btn" onclick="dashboard.toggleSession('${session.session_id}')">
                    <i class="fas fa-chevron-down"></i>
                </button>
            </div>
            <div class="session-files" id="session-files-${session.session_id}" style="display: none;">
                ${this.createSessionFilesHTML(session.files)}
            </div>
        `;
        
        return div;
    }

    /**
     * Create HTML for session files
     */
    createSessionFilesHTML(files) {
        if (!files || files.length === 0) {
            return '<p class="no-files">No files available for this session.</p>';
        }
        
        // Group files by language for better organization in sessions too
        const groupedFiles = this.groupFilesByLanguage(files);
        
        return Object.keys(groupedFiles).map(language => {
            const languageFiles = groupedFiles[language];
            const filesHTML = languageFiles.map(file => {
                const fileSize = this.formatFileSize(file.size);
                const fileIcon = this.getFileTypeIcon(file.filename);
                
                return `
                    <div class="session-file">
                        <div class="file-info">
                            <div class="file-name">
                                <i class="fas ${fileIcon}"></i> ${this.escapeHtml(file.filename)}
                            </div>
                            <div class="file-meta">
                                Size: ${fileSize}
                            </div>
                        </div>
                        <a href="${file.url}" class="download-btn" download="${file.filename}">
                            <i class="fas fa-download"></i> Download
                        </a>
                    </div>
                `;
            }).join('');
            
            return `
                <div class="session-language-group">
                    <h5 class="session-language-title">
                        <i class="fas fa-language"></i> ${language} (${languageFiles.length} files)
                    </h5>
                    ${filesHTML}
                </div>
            `;
        }).join('');
    }

    /**
     * Toggle session file visibility
     */
    toggleSession(sessionId) {
        const filesContainer = document.getElementById(`session-files-${sessionId}`);
        const button = filesContainer.previousElementSibling.querySelector('.expand-btn i');
        
        if (filesContainer.style.display === 'none') {
            filesContainer.style.display = 'block';
            button.className = 'fas fa-chevron-up';
        } else {
            filesContainer.style.display = 'none';
            button.className = 'fas fa-chevron-down';
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

/**
 * Global function to switch to new research (called from browse sessions)
 */
function switchToNewResearch() {
    if (window.dashboard) {
        window.dashboard.switchView('new-research');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.wsClient.close();
    }
});