/**
 * Home Page JavaScript Functions
 * Contains all functionality for the course home page including:
 * - Tab System
 * - Group Management
 * - Popup Handling
 */

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

    // Make necessary functions globally available
    window.openGroupPopup = () => {
        console.log('Opening group popup');
        popupManager.openGroupPopup();
        groupSearch.searchGroup(); // Load all groups immediately
    };
    window.closeGroupPopup = () => popupManager.closeGroupPopup();
    window.searchGroup = () => groupSearch.searchGroup();
    window.groupManagement = groupManagement;
}); 