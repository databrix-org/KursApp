/**
 * Home Page JavaScript Functions
 * Contains all functionality for the course home page including:
 * - Tab System
 * - Group Management
 * - Popup Handling
 */

// Global modal management functions
// These need to be in the global scope for HTML onclick attributes
function openGroupPopup() {
    console.log('Opening group popup');
    const popup = document.getElementById('groupPopup');
    if (popup) {
        popup.style.display = 'block';
        // Try to load groups if the search function is available
        if (window.searchGroup) {
            window.searchGroup();
        }
    }
}

function closeGroupPopup() {
    const popup = document.getElementById('groupPopup');
    if (popup) {
        popup.style.display = 'none';
    }
}

function openTicketModal() {
    const modal = document.getElementById('ticketModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeTicketModal() {
    const modal = document.getElementById('ticketModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openEnrollmentModal() {
    const modal = document.getElementById('enrollmentModal');
    if (modal) {
        modal.style.display = 'block';
        // Reset any previous error messages
        const errorDiv = document.getElementById('enrollmentError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }
        
        // Show key form, hide group selection
        document.getElementById('enrollmentKeyForm').style.display = 'block';
        document.getElementById('groupSelectionForm').style.display = 'none';
    }
}

function closeEnrollmentModal() {
    const modal = document.getElementById('enrollmentModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Helper function to get cookie by name
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function submitEnrollment() {
    const keyInput = document.getElementById('enrollmentKey');
    const errorDiv = document.getElementById('enrollmentError');
    const enrollmentButton = document.querySelector('#enrollmentKeyForm .action-btn');
    const courseId = document.querySelector('[data-course-id]')?.getAttribute('data-course-id');
    
    if (!keyInput || !errorDiv || !enrollmentButton || !courseId) {
        console.error('Missing required elements');
        return;
    }
    
    // Disable button and show loading state
    enrollmentButton.disabled = true;
    const originalButtonText = enrollmentButton.innerHTML;
    enrollmentButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verarbeitung...';
    
    try {
        // Get enrollment key from input
        const enrollmentKey = keyInput.value.trim();
        
        // Get CSRF token from the cookie
        const csrftoken = getCookie('csrftoken');
        
        // Debug logs
        // The correct URL pattern according to urls.py is 'enroll/<int:course_id>/'
        const enrollUrl = `/course/enroll/${courseId}/`;
        console.log('Enrollment URL:', enrollUrl);
        console.log('Course ID:', courseId);
        console.log('Enrollment key:', enrollmentKey);
        
        // Prepare the request body
        const requestBody = JSON.stringify({ enrollment_key: enrollmentKey });
        console.log('Request body:', requestBody);
        
        // Submit to enrollment endpoint - using the correct URL pattern
        const response = await fetch(enrollUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: requestBody,
            credentials: 'same-origin'
        });
        
        // Debug response
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        // Check for HTTP errors
        if (!response.ok) {
            const contentType = response.headers.get('content-type');
            console.log('Response content type:', contentType);
            
            // Try to parse the error response
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                console.log('Error data:', errorData);
                throw new Error(errorData.message || `Server error: ${response.status}`);
            } else {
                const errorText = await response.text();
                console.log('Error text:', errorText.substring(0, 500)); // Log first 500 chars
                throw new Error(`Server error: ${response.status}`);
            }
        }
        
        // Parse the JSON response
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const responseText = await response.text();
            console.log('Non-JSON response:', responseText.substring(0, 500)); // Log first 500 chars
            throw new Error('Server did not return JSON');
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            // If enrollment was successful
            if (data.requires_group) {
                // Show group selection form
                document.getElementById('enrollmentKeyForm').style.display = 'none';
                document.getElementById('groupSelectionForm').style.display = 'block';
                
                // Display available groups
                displayAvailableGroups(data.groups, courseId);
            } else {
                // No group needed, reload the page
                window.location.reload();
            }
        } else {
            // Show error message
            errorDiv.textContent = data.message || 'Fehler bei der Einschreibung. Bitte versuchen Sie es erneut.';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error during enrollment:', error);
        errorDiv.textContent = error.message || 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.';
        errorDiv.style.display = 'block';
    } finally {
        // Restore button state
        enrollmentButton.disabled = false;
        enrollmentButton.innerHTML = originalButtonText;
    }
}

function displayAvailableGroups(groups, courseId) {
    const container = document.getElementById('availableGroups');
    if (!container) return;
    
    if (!groups || groups.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users-slash"></i>
                <p>Keine freien Teams verfügbar.</p>
                <button class="action-btn secondary" onclick="window.location.reload()">
                    Seite aktualisieren
                </button>
            </div>
        `;
        return;
    }
    
    // Build group cards
    let html = '';
    groups.forEach(group => {
        html += `
            <div class="group-card">
                <div class="group-info">
                    <h4>Team ${group.id}</h4>
                    <p>Mitglieder: ${group.member_count}</p>
                    <p class="created-date">Erstellt: ${new Date(group.created_at).toLocaleDateString()}</p>
                </div>
                <button class="join-group-btn" 
                        onclick="joinGroupAndStart(${group.id}, ${courseId})">
                    <i class="fas fa-users"></i>
                    Beitreten
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

async function joinGroupAndStart(groupId, courseId) {
    try {
        // Get CSRF token
        const csrftoken = getCookie('csrftoken');
        
        // Prepare request body
        const requestBody = JSON.stringify({ group_id: groupId });
        console.log('Join group URL:', `/course/${courseId}/groups/join/`);
        console.log('Group ID:', groupId);
        
        // Join the group - using the correct URL pattern
        const response = await fetch(`/course/${courseId}/groups/join/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: requestBody,
            credentials: 'same-origin'
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        // Check for HTTP errors
        if (!response.ok) {
            const contentType = response.headers.get('content-type');
            
            // Try to parse the error response
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                console.log('Error data:', errorData);
                throw new Error(errorData.error || errorData.message || `Server error: ${response.status}`);
            } else {
                const errorText = await response.text();
                console.log('Error text:', errorText.substring(0, 500)); // Log first 500 chars
                throw new Error(`Server error: ${response.status}`);
            }
        }
        
        // Redirect to course overview page - using the correct URL pattern
        window.location.href = `/course/${courseId}/`;
    } catch (error) {
        console.error('Error joining group:', error);
        alert(error.message || 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
    }
}

// Tab System Management
class TabSystem {
    constructor() {
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabContents = document.querySelectorAll('.tab-content');
        
        console.log('Found tab buttons:', this.tabButtons.length);
        console.log('Found tab contents:', this.tabContents.length);
        
        this.initializeTabs();
        this.setupEventListeners();
    }

    initializeTabs() {
        this.tabContents.forEach((content, index) => {
            content.style.display = index === 0 ? 'block' : 'none';
        });
    }

    setupEventListeners() {
        this.tabButtons.forEach(button => {
            button.addEventListener('click', () => this.handleTabClick(button));
        });
    }

    handleTabClick(button) {
        console.log('Tab clicked:', button.getAttribute('data-tab'));
        
        // Hide all content
        this.tabContents.forEach(content => {
            content.style.display = 'none';
        });

        // Remove active class from all buttons
        this.tabButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected content and activate button
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        const selectedContent = document.getElementById(tabId);
        if (selectedContent) {
            selectedContent.style.display = 'block';
            console.log('Showing tab:', tabId);
        } else {
            console.error('Could not find tab content for:', tabId);
        }
    }
}

// Group Management System
class GroupManagement {
    constructor(courseId, csrfToken) {
        this.courseId = courseId;
        this.csrfToken = csrfToken;
    }

    async handleJoinGroup(groupId) {
        if (!confirm(`Are you sure you want to join this group?`)) return;

        try {
            // Get the current CSRF token from the cookie
            const csrftoken = this.getCookie('csrftoken');
            
            const response = await fetch(`/course/${this.courseId}/groups/join/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({ group_id: groupId }),
                credentials: 'same-origin'  // Include cookies in the request
            });

            if (response.ok) {
                window.location.reload();
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to join group');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while joining the group');
        }
    }

    // Helper function to get CSRF token from cookie
    getCookie(name) {
        return getCookie(name);
    }
}

// Popup Management System
class PopupManager {
    constructor() {
        this.setupOutsideClickHandler();
    }

    openGroupPopup() {
        const popup = document.getElementById('groupPopup');
        if (popup) {
            popup.style.display = 'block';
        }
    }

    closeGroupPopup() {
        const popup = document.getElementById('groupPopup');
        if (popup) {
            popup.style.display = 'none';
        }
    }

    setupOutsideClickHandler() {
        document.addEventListener('click', (event) => {
            const popup = document.getElementById('groupPopup');
            const popupContent = popup?.querySelector('.group-popup');
            const button = document.querySelector('.join-group-btn');
            
            if (!popup || !button) return;
            
            if (event.target === popup && event.target !== popupContent && event.target !== button) {
                this.closeGroupPopup();
            }
        });
    }
}

// Add this new GroupSearch class
class GroupSearch {
    constructor(courseId, groupManagement) {
        this.courseId = courseId;
        this.groupManagement = groupManagement;
        this.searchInput = document.getElementById('groupSearchInput');
        this.searchResults = document.getElementById('searchResults');
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.searchInput?.addEventListener('input', () => this.searchGroup());
    }

    async searchGroup() {
        try {
            console.log('Fetching groups...');
            const response = await fetch(`/course/${this.courseId}/groups/list/`);
            const data = await response.json();
            console.log('Received data:', data);
            
            if (data.success) {
                console.log('Groups to display:', data.groups);
                this.displayGroups(data.groups);
            } else {
                console.log('Error from server:', data.error);
                this.showError(data.error || 'Failed to load groups');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Error loading groups');
        }
    }

    displayGroups(groups) {
        console.log('Display groups called with:', groups);
        if (!this.searchResults) {
            console.error('searchResults element not found');
            return;
        }
        
        if (!Array.isArray(groups) || groups.length === 0) {
            this.searchResults.innerHTML = '<p class="no-groups-message">No groups available</p>';
            return;
        }

        this.searchResults.innerHTML = `
            <div class="groups-container single-column">
                ${groups.map(group => `
                    <div class="group-card">
                        <div class="group-info">
                            <h4>Group ${group.id}</h4>
                            <div class="member-list">
                                <strong>Members (${group.members.length}):</strong>
                                ${group.members.length > 0 ? `
                                    <ul>
                                        ${group.members.map(m => 
                                            `<li>${m}</li>`
                                        ).join('')}
                                    </ul>
                                ` : '<p>No members yet</p>'}
                            </div>
                            <p class="created-date">Created: ${new Date(group.created_at).toLocaleDateString()}</p>
                        </div>
                        <button class="join-group-btn" 
                                data-group-id="${group.id}"
                                onclick="window.groupManagement.handleJoinGroup(${group.id})">
                            Join Group
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    showError(message) {
        this.searchResults.innerHTML = `<div class="error-message">${message}</div>`;
    }
}

// Ticket System Management
class TicketSystem {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const ticketForm = document.getElementById('ticketForm');
        const imageInput = document.getElementById('ticketImage');
        
        if (ticketForm) {
            ticketForm.addEventListener('submit', (e) => this.handleTicketSubmit(e));
        }
        
        if (imageInput) {
            imageInput.addEventListener('change', (e) => this.handleImagePreview(e));
        }
    }

    handleImagePreview(event) {
        const file = event.target.files[0];
        const previewDiv = document.querySelector('.file-preview');
        
        if (!previewDiv) return;
        
        // Clear previous preview
        previewDiv.innerHTML = '';
        
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                alert('Please select an image file');
                event.target.value = '';
                return;
            }
            
            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('Image size should not exceed 5MB');
                event.target.value = '';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.createElement('div');
                preview.className = 'image-preview';
                preview.innerHTML = `
                    <img src="${e.target.result}" alt="Preview">
                    <button type="button" class="remove-image">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                
                previewDiv.appendChild(preview);
                
                // Add remove button functionality
                preview.querySelector('.remove-image').addEventListener('click', () => {
                    event.target.value = '';
                    previewDiv.innerHTML = '';
                });
            };
            reader.readAsDataURL(file);
        }
    }

    async handleTicketSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        
        // Remove any existing alerts
        const existingAlerts = form.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        try {
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            
            const formData = new FormData(form);
            
            const response = await fetch('/course/tickets/create/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server did not return JSON');
            }

            const data = await response.json();
            
            if (data.success) {
                // Close the modal
                closeTicketModal();
                
                // Show success message in a floating notification
                const notification = document.createElement('div');
                notification.className = 'floating-notification success';
                notification.innerHTML = `
                    <div class="notification-content">
                        <i class="fas fa-check-circle"></i>
                        <span>${data.message || 'Ihre Anfrage wurde erfolgreich gesendet.'}</span>
                    </div>
                `;
                
                document.body.appendChild(notification);
                
                // Reset form and clear image preview
                form.reset();
                const previewDiv = document.querySelector('.file-preview');
                if (previewDiv) {
                    previewDiv.innerHTML = '';
                }
                
                // Remove notification after 5 seconds
                setTimeout(() => {
                    notification.classList.add('fade-out');
                    setTimeout(() => notification.remove(), 300);
                }, 5000);
            } else {
                throw new Error(data.error || 'Failed to create ticket');
            }
        } catch (error) {
            console.error('Error:', error);
            
            // Show error message in the form
            const errorMessage = document.createElement('div');
            errorMessage.className = 'alert alert-danger';
            errorMessage.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                ${error.message || 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.'}
            `;
            form.insertBefore(errorMessage, form.firstChild);
        } finally {
            // Restore button state
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    }
}

// Initialize all systems when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const courseId = document.querySelector('[data-course-id]')?.getAttribute('data-course-id');
    console.log('Course ID:', courseId);
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    console.log('CSRF Token available:', !!csrfToken);

    // Initialize all systems
    const tabSystem = new TabSystem();
    const groupManagement = new GroupManagement(courseId, csrfToken);
    const popupManager = new PopupManager();
    const groupSearch = new GroupSearch(courseId, groupManagement);
    const ticketSystem = new TicketSystem();

    // Make instance methods available through the window object
    window.groupManagement = groupManagement;
    window.searchGroup = () => groupSearch.searchGroup();
}); 