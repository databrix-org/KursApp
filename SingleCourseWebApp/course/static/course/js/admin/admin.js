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
                            roleCell.textContent = newRole.charAt(0).toUpperCase() + newRole.slice(1);
                        }
                    }

                    this.showNotification(data.message || 'Rolle erfolgreich aktualisiert', 'success');
                } else {
                    this.showNotification(data.error || 'Fehler beim Ändern der Rolle', 'danger');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showNotification('Ein Fehler ist beim Ändern der Rolle aufgetreten', 'danger');
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
            }
        }

        async handleEmailSubmit(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);

            try {
                const response = await fetch('/course/admin/send-email/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.csrfToken,
                    },
                    body: formData
                });

                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('E-Mail erfolgreich gesendet', 'success');
                    form.reset();
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