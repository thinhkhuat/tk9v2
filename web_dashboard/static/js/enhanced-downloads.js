/**
 * Enhanced Download Features for Dashboard
 * Provides advanced file management and download capabilities
 */

class EnhancedDownloads {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.previewModal = null;
        this.searchTimeout = null;
        this.downloadQueue = [];

        this.initializeEnhancedFeatures();
    }

    /**
     * Initialize enhanced download features
     */
    initializeEnhancedFeatures() {
        // Create preview modal
        this.createPreviewModal();

        // Add search bar to UI
        this.addSearchBar();

        // Add download all button handler
        this.addDownloadAllHandler();

        // Initialize tooltips
        this.initializeTooltips();

        console.log('Enhanced download features initialized');
    }

    /**
     * Create preview modal for file preview
     */
    createPreviewModal() {
        const modalHTML = `
            <div id="file-preview-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="preview-filename">File Preview</h3>
                        <button class="modal-close" onclick="enhancedDownloads.closePreview()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <pre id="preview-content"></pre>
                        <div id="preview-loading" style="display: none;">
                            <i class="fas fa-spinner fa-spin"></i> Loading preview...
                        </div>
                        <div id="preview-error" style="display: none;" class="error-message">
                            Unable to preview this file
                        </div>
                    </div>
                    <div class="modal-footer">
                        <div id="preview-info"></div>
                        <button class="btn btn-primary" id="preview-download-btn">
                            <i class="fas fa-download"></i> Download Full File
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.previewModal = document.getElementById('file-preview-modal');
    }

    /**
     * Add search bar to the UI
     */
    addSearchBar() {
        const searchHTML = `
            <div class="search-container" id="file-search-container">
                <input type="text" id="file-search-input" placeholder="Search files..." class="search-input">
                <button id="file-search-btn" class="search-btn">
                    <i class="fas fa-search"></i>
                </button>
                <div id="search-results" class="search-results" style="display: none;"></div>
            </div>
        `;

        // Add to browse sessions section
        const browseSection = document.getElementById('browse-sessions');
        if (browseSection) {
            const firstChild = browseSection.firstElementChild;
            if (firstChild) {
                firstChild.insertAdjacentHTML('afterend', searchHTML);
            }
        }

        // Add event listeners
        const searchInput = document.getElementById('file-search-input');
        const searchBtn = document.getElementById('file-search-btn');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearchInput(e));
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch(e.target.value);
                }
            });
        }

        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const query = searchInput.value;
                this.performSearch(query);
            });
        }
    }

    /**
     * Handle search input with debouncing
     */
    handleSearchInput(event) {
        const query = event.target.value;

        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        // Set new timeout for debouncing
        this.searchTimeout = setTimeout(() => {
            if (query.length >= 2) {
                this.performSearch(query);
            } else {
                this.clearSearchResults();
            }
        }, 300);
    }

    /**
     * Perform file search
     */
    async performSearch(query) {
        if (!query || query.length < 2) return;

        try {
            const response = await fetch(`/api/search/files?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            this.displaySearchResults(data);
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError('Search failed. Please try again.');
        }
    }

    /**
     * Display search results
     */
    displaySearchResults(data) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        if (data.count === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No files found</div>';
        } else {
            const resultsHTML = data.results.map(result => `
                <div class="search-result-item">
                    <div class="result-session">
                        <i class="fas fa-folder"></i> ${this.escapeHtml(result.session_subject)}
                    </div>
                    <div class="result-file">
                        <span class="file-name">${this.escapeHtml(result.file.filename)}</span>
                        <div class="file-actions">
                            <button onclick="enhancedDownloads.previewFile('${result.session_id}', '${result.file.filename}')"
                                    class="btn-small" title="Preview">
                                <i class="fas fa-eye"></i>
                            </button>
                            <a href="${result.file.url}" download="${result.file.filename}"
                               class="btn-small" title="Download">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>
                    </div>
                    <div class="result-meta">
                        <span class="match-type">${result.match_type}</span>
                        <span class="file-size">${this.formatFileSize(result.file.size)}</span>
                    </div>
                </div>
            `).join('');

            resultsContainer.innerHTML = `
                <div class="search-results-header">
                    Found ${data.count} files matching "${this.escapeHtml(data.query)}"
                </div>
                ${resultsHTML}
            `;
        }

        resultsContainer.style.display = 'block';
    }

    /**
     * Clear search results
     */
    clearSearchResults() {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';
        }
    }

    /**
     * Show search error
     */
    showSearchError(message) {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="error-message">${message}</div>`;
            resultsContainer.style.display = 'block';
        }
    }

    /**
     * Add download all handler
     */
    addDownloadAllHandler() {
        // Add download all buttons to existing download sections
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('download-all-btn') ||
                e.target.closest('.download-all-btn')) {
                const btn = e.target.classList.contains('download-all-btn') ?
                           e.target : e.target.closest('.download-all-btn');
                const sessionId = btn.dataset.sessionId;
                if (sessionId) {
                    this.downloadAllAsZip(sessionId);
                }
            }
        });
    }

    /**
     * Download all files as ZIP
     */
    async downloadAllAsZip(sessionId) {
        try {
            // Show loading indicator
            this.showDownloadProgress('Preparing ZIP file...');

            // Trigger download
            const downloadUrl = `/api/session/${sessionId}/zip`;
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `${sessionId}_all_files.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Hide loading indicator
            setTimeout(() => {
                this.hideDownloadProgress();
                this.showNotification('ZIP download started', 'success');
            }, 1000);

        } catch (error) {
            console.error('Error downloading ZIP:', error);
            this.hideDownloadProgress();
            this.showNotification('Failed to download ZIP file', 'error');
        }
    }

    /**
     * Preview file
     */
    async previewFile(sessionId, filename) {
        if (!this.previewModal) return;

        // Show modal with loading state
        this.previewModal.style.display = 'flex';
        document.getElementById('preview-loading').style.display = 'block';
        document.getElementById('preview-content').style.display = 'none';
        document.getElementById('preview-error').style.display = 'none';
        document.getElementById('preview-filename').textContent = filename;

        try {
            // Encode the filename properly for the URL
            const encodedFilename = encodeURIComponent(filename);
            const response = await fetch(`/api/session/${sessionId}/file/${encodedFilename}/preview?lines=100`);

            if (!response.ok) {
                throw new Error('Preview not available');
            }

            const preview = await response.json();

            // Display preview
            document.getElementById('preview-content').textContent = preview.content;
            document.getElementById('preview-content').style.display = 'block';
            document.getElementById('preview-loading').style.display = 'none';

            // Set info
            const info = document.getElementById('preview-info');
            if (preview.truncated) {
                info.innerHTML = `
                    <span class="preview-info-item">
                        <i class="fas fa-info-circle"></i>
                        Showing ${preview.preview_lines} of ${preview.total_lines} lines
                    </span>
                    <span class="preview-info-item">
                        Size: ${this.formatFileSize(preview.file_size)}
                    </span>
                `;
            } else {
                info.innerHTML = `
                    <span class="preview-info-item">
                        ${preview.total_lines} lines
                    </span>
                    <span class="preview-info-item">
                        Size: ${this.formatFileSize(preview.file_size)}
                    </span>
                `;
            }

            // Set download button
            const downloadBtn = document.getElementById('preview-download-btn');
            downloadBtn.onclick = () => {
                window.location.href = `/download/${sessionId}/${filename}`;
            };

        } catch (error) {
            console.error('Preview error:', error);
            document.getElementById('preview-loading').style.display = 'none';
            document.getElementById('preview-error').style.display = 'block';
        }
    }

    /**
     * Close preview modal
     */
    closePreview() {
        if (this.previewModal) {
            this.previewModal.style.display = 'none';
        }
    }

    /**
     * Show file metadata
     */
    async showFileMetadata(sessionId, filename) {
        try {
            const encodedFilename = encodeURIComponent(filename);
            const response = await fetch(`/api/session/${sessionId}/file/${encodedFilename}/metadata`);

            if (!response.ok) throw new Error('Failed to get metadata');

            const metadata = await response.json();

            // Display metadata in a tooltip or modal
            this.displayMetadata(metadata);
        } catch (error) {
            console.error('Error getting metadata:', error);
        }
    }

    /**
     * Display file metadata
     */
    displayMetadata(metadata) {
        const metadataHTML = `
            <div class="metadata-container">
                <h4>${metadata.friendly_name}</h4>
                <table class="metadata-table">
                    <tr><td>Size:</td><td>${metadata.size_formatted}</td></tr>
                    <tr><td>Created:</td><td>${new Date(metadata.created).toLocaleString()}</td></tr>
                    <tr><td>Modified:</td><td>${new Date(metadata.modified).toLocaleString()}</td></tr>
                    <tr><td>Type:</td><td>${metadata.mime_type}</td></tr>
                    <tr><td>Hash:</td><td class="hash">${metadata.hash.substring(0, 12)}...</td></tr>
                </table>
            </div>
        `;

        // You can display this in a tooltip or modal
        this.showTooltip(metadataHTML);
    }

    /**
     * Get session statistics
     */
    async getSessionStatistics(sessionId) {
        try {
            const response = await fetch(`/api/session/${sessionId}/statistics`);
            if (!response.ok) throw new Error('Failed to get statistics');

            const stats = await response.json();
            return stats;
        } catch (error) {
            console.error('Error getting statistics:', error);
            return null;
        }
    }

    /**
     * Show download progress
     */
    showDownloadProgress(message) {
        const progressHTML = `
            <div id="download-progress" class="download-progress">
                <div class="progress-content">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>${message}</span>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', progressHTML);
    }

    /**
     * Hide download progress
     */
    hideDownloadProgress() {
        const progress = document.getElementById('download-progress');
        if (progress) {
            progress.remove();
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notificationHTML = `
            <div class="notification notification-${type}">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
                ${message}
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', notificationHTML);

        // Auto-hide after 3 seconds
        setTimeout(() => {
            const notification = document.querySelector('.notification');
            if (notification) {
                notification.remove();
            }
        }, 3000);
    }

    /**
     * Initialize tooltips
     */
    initializeTooltips() {
        // Add tooltip functionality to elements with title attribute
        document.addEventListener('mouseover', (e) => {
            if (e.target.hasAttribute('title')) {
                // Implementation would go here
            }
        });
    }

    /**
     * Show tooltip
     */
    showTooltip(content) {
        // Implementation for showing tooltips
        console.log('Tooltip:', content);
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
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Enhance existing download sections
     */
    enhanceDownloadSection(sessionId, files) {
        // Add download all button
        const downloadSection = document.getElementById('download-section');
        if (!downloadSection) return;

        const downloadHeader = downloadSection.querySelector('h2');
        if (downloadHeader && !downloadHeader.querySelector('.download-all-btn')) {
            downloadHeader.insertAdjacentHTML('beforeend', `
                <button class="download-all-btn btn btn-primary" data-session-id="${sessionId}">
                    <i class="fas fa-file-archive"></i> Download All as ZIP
                </button>
            `);
        }

        // Add preview buttons to files
        const fileElements = downloadSection.querySelectorAll('.download-file');
        fileElements.forEach((element, index) => {
            if (files && files[index]) {
                const file = files[index];
                const fileInfo = element.querySelector('.file-info');

                if (fileInfo && !fileInfo.querySelector('.preview-btn')) {
                    const previewBtn = document.createElement('button');
                    previewBtn.className = 'preview-btn btn-small';
                    previewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview';
                    previewBtn.onclick = () => this.previewFile(sessionId, file.filename);

                    fileInfo.appendChild(previewBtn);
                }
            }
        });
    }
}

// Initialize enhanced downloads when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for dashboard to be initialized
    setTimeout(() => {
        if (window.dashboard) {
            window.enhancedDownloads = new EnhancedDownloads(window.dashboard);
            console.log('Enhanced downloads initialized');
        }
    }, 100);
});

// Global function for closing preview (called from modal)
function closePreview() {
    if (window.enhancedDownloads) {
        window.enhancedDownloads.closePreview();
    }
}