/**
 * Admin Dashboard JavaScript
 * Handles user management, role requests, and bug reports
 */

(() => {
    class AdminDashboard {
        constructor() {
            // Wait for DOM to be ready
            document.addEventListener('DOMContentLoaded', () => {
                // Only initialize if we're on the admin dashboard page
                if (document.querySelector('.admin-layout')) {
                    this.initialize();
                }
            });
        }

        initialize() {
            // Get CSRF token from the form
            const form = document.querySelector('#roleChangeForm');
            if (!form) {
                console.warn('Rollenänderungsformular nicht gefunden');
                return;
            }

            const csrfInput = form.querySelector('[name="csrfmiddlewaretoken"]');
            if (!csrfInput) {
                console.warn('CSRF-Token nicht gefunden');
                return;
            }

            this.csrfToken = csrfInput.value;
            
            this.initializeEventListeners();
            this.initializeSearch();
            this.initializeEmailForm();
        }

        initializeEventListeners() {
            // Role change buttons
            document.querySelectorAll('.change-role').forEach(button => {
                button.addEventListener('click', (e) => this.handleRoleChange(e));
            });

            // Confirm role change button in modal
            const confirmButton = document.getElementById('confirmRoleChange');
            if (confirmButton) {
                confirmButton.addEventListener('click', () => this.confirmRoleChange());
            }
            
            // Delete user buttons
            document.querySelectorAll('.delete-user').forEach(button => {
                button.addEventListener('click', (e) => this.handleDeleteUser(e));
            });
            
            // Confirm delete user button in modal
            const confirmDeleteButton = document.getElementById('confirmDeleteUser');
            if (confirmDeleteButton) {
                confirmDeleteButton.addEventListener('click', () => this.confirmDeleteUser());
            }
        }

        async handleRoleChange(event) {
            const userId = event.target.dataset.userId;
            const modalElement = document.getElementById('roleModal');
            
            if (!modalElement) {
                console.error('Role modal not found');
                return;
            }

            const modal = new bootstrap.Modal(modalElement);
            
            // Store the user ID for use in confirmation
            this.currentUserId = userId;
            
            // Show the modal
            modal.show();
        }

        async confirmRoleChange() {
            const roleSelect = document.querySelector('#roleChangeForm select[name="role"]');
            if (!roleSelect || !this.currentUserId || !this.csrfToken) {
                console.error('Missing required data for role change');
                return;
            }

            const newRole = roleSelect.value;
            
            try {
                const response = await fetch('/course/admin/change-role/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken,
                    },
                    body: JSON.stringify({
                        user_id: this.currentUserId,
                        new_role: newRole
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                if (data.success) {
                    // Close modal
                    const modalElement = document.getElementById('roleModal');
                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        if (modal) modal.hide();
                    }
                    
                    // Update the role in the table without reloading
                    const userRow = document.querySelector(`tr[data-user-id="${this.currentUserId}"]`);
                    if (userRow) {
                        const roleCell = userRow.querySelector('td:nth-child(3)');
                        if (roleCell) {
                            if (newRole === 'admin') {
                                roleCell.textContent = 'Administrator';
                            } else if (newRole === 'instructor') {
                                roleCell.textContent = 'Dozent';
                            } else {
                                roleCell.textContent = 'Student';
                            }
                        }
                    }

                    this.showNotification(data.message || 'Rolle erfolgreich aktualisiert', 'success');
                    
                    // If the role was changed to admin, refresh the page after a short delay
                    if (newRole === 'admin') {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    }
                } else {
                    this.showNotification(data.error || 'Fehler beim Ändern der Rolle', 'danger');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showNotification('Ein Fehler ist beim Ändern der Rolle aufgetreten', 'danger');
            }
        }

        async handleDeleteUser(event) {
            const userId = event.target.dataset.userId;
            const userName = event.target.dataset.userName;
            const modalElement = document.getElementById('deleteUserModal');
            
            if (!modalElement) {
                console.error('Delete user modal not found');
                return;
            }

            const modal = new bootstrap.Modal(modalElement);
            
            // Store the user ID for use in confirmation
            document.getElementById('deleteUserId').value = userId;
            
            // Set the user name in the modal
            document.getElementById('deleteUserName').textContent = userName;
            
            // Show the modal
            modal.show();
        }

        async confirmDeleteUser() {
            const deleteUserForm = document.getElementById('deleteUserForm');
            const userId = document.getElementById('deleteUserId').value;
            
            if (!userId || !this.csrfToken) {
                console.error('Missing required data for user deletion');
                return;
            }
            
            try {
                const response = await fetch('/course/admin/delete-user/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken,
                    },
                    body: JSON.stringify({
                        user_id: userId
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                if (data.success) {
                    // Close modal
                    const modalElement = document.getElementById('deleteUserModal');
                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        if (modal) modal.hide();
                    }
                    
                    // Remove the user row from the table
                    const userRow = document.querySelector(`tr[data-user-id="${userId}"]`);
                    if (userRow) {
                        userRow.remove();
                    }

                    this.showNotification(data.message || 'Benutzer erfolgreich gelöscht', 'success');
                } else {
                    this.showNotification(data.error || 'Fehler beim Löschen des Benutzers', 'danger');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showNotification('Ein Fehler ist beim Löschen des Benutzers aufgetreten', 'danger');
            }
        }

        // Helper method to show notifications
        showNotification(message, type = 'success') {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const container = document.querySelector('.container-fluid');
            if (container) {
                container.insertBefore(alertDiv, container.firstChild);
                
                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    alertDiv.remove();
                }, 5000);
            }
        }

        initializeSearch() {
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
            }
        }

        handleSearch(query) {
            const userRows = document.querySelectorAll('#usersTable tbody tr');
            query = query.toLowerCase();

            userRows.forEach(row => {
                const name = row.querySelector('td:first-child').textContent.toLowerCase();
                const email = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                
                if (name.includes(query) || email.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        initializeEmailForm() {
            const emailForm = document.getElementById('emailForm');
            if (emailForm) {
                emailForm.addEventListener('submit', (e) => this.handleEmailSubmit(e));
                
                // Handle recipient type selection
                const recipientSelect = document.getElementById('emailRecipients');
                const userSelectionContainer = document.getElementById('userSelectionContainer');
                
                if (recipientSelect && userSelectionContainer) {
                    recipientSelect.addEventListener('change', () => {
                        if (recipientSelect.value === 'selected') {
                            userSelectionContainer.style.display = 'block';
                        } else {
                            userSelectionContainer.style.display = 'none';
                        }
                    });
                }
                
                // Initialize user search
                const userSearch = document.getElementById('userSearch');
                const clearSearch = document.getElementById('clearSearch');
                
                if (userSearch) {
                    userSearch.addEventListener('input', (e) => this.handleUserSearch(e.target.value));
                }
                
                if (clearSearch) {
                    clearSearch.addEventListener('click', () => {
                        if (userSearch) {
                            userSearch.value = '';
                            this.handleUserSearch('');
                        }
                    });
                }
                
                // Select/deselect all users
                const selectAllBtn = document.getElementById('selectAllUsers');
                const deselectAllBtn = document.getElementById('deselectAllUsers');
                
                if (selectAllBtn) {
                    selectAllBtn.addEventListener('click', () => this.toggleAllUsers(true));
                }
                
                if (deselectAllBtn) {
                    deselectAllBtn.addEventListener('click', () => this.toggleAllUsers(false));
                }
            }
        }
        
        handleUserSearch(query) {
            const userItems = document.querySelectorAll('#userList .list-group-item');
            query = query.toLowerCase();
            
            userItems.forEach(item => {
                const label = item.querySelector('label').textContent.toLowerCase();
                
                if (label.includes(query)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }
        
        toggleAllUsers(select) {
            const checkboxes = document.querySelectorAll('.user-checkbox');
            checkboxes.forEach(checkbox => {
                const item = checkbox.closest('.list-group-item');
                if (item.style.display !== 'none') {
                    checkbox.checked = select;
                }
            });
        }

        async handleEmailSubmit(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            
            // Handle selected users
            if (formData.get('recipients') === 'selected') {
                const selectedUsers = [];
                document.querySelectorAll('.user-checkbox:checked').forEach(checkbox => {
                    selectedUsers.push(checkbox.value);
                });
                
                if (selectedUsers.length === 0) {
                    this.showNotification('Bitte wählen Sie mindestens einen Benutzer aus', 'warning');
                    return;
                }
                
                formData.set('selected_users', JSON.stringify(selectedUsers));
            }

            try {
                const response = await fetch('/course/admin/send-email/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                if (data.success) {
                    this.showNotification(data.message || 'E-Mail wurde erfolgreich gesendet', 'success');
                    form.reset();
                    // restore default No Reply subject and notice
                    const subjectInput = document.getElementById('emailSubject');
                    const contentTextarea = document.getElementById('emailContent');
                    if (subjectInput) subjectInput.value = '[No Reply] ';
                    if (contentTextarea) contentTextarea.value = 'Bitte beachten Sie: Diese E-Mail wurde von einer No-Reply-Adresse gesendet. Antworten auf diese E-Mail werden nicht gelesen.\n\n';
                    // Hide user selection container
                    const userSelectionContainer = document.getElementById('userSelectionContainer');
                    if (userSelectionContainer) {
                        userSelectionContainer.style.display = 'none';
                    }
                } else {
                    this.showNotification(data.error || 'Fehler beim Senden der E-Mail', 'danger');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showNotification('Ein Fehler ist beim Senden der E-Mail aufgetreten', 'danger');
            }
        }
    }

    // Create single instance
    new AdminDashboard();
})(); 