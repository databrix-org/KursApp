class TicketManagement {
    constructor() {
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        this.ticketModal = new bootstrap.Modal(document.getElementById('ticketModal'));
        this.setupEventListeners();
        this.loadTickets();

        // Update status mappings to match backend values
        this.statusDisplayMap = {
            'open': 'Offen',
            'in_progress': 'In Bearbeitung',
            'closed': 'Geschlossen'
        };

        // Update status colors using backend values
        this.statusClassMap = {
            'open': 'danger',
            'in_progress': 'warning',
            'closed': 'success'
        };

        this.tickets = []; // Add this line to store all tickets
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        // Save ticket changes
        const saveButton = document.getElementById('saveTicket');
        if (saveButton) {
            saveButton.addEventListener('click', () => this.saveTicket());
        }

        // Delete ticket
        const deleteButton = document.getElementById('deleteTicket');
        if (deleteButton) {
            deleteButton.addEventListener('click', () => this.deleteTicket());
        }

        // Edit ticket button click delegation
        const ticketsTable = document.getElementById('ticketsTable');
        if (ticketsTable) {
            ticketsTable.addEventListener('click', (e) => {
                const editButton = e.target.closest('.edit-ticket');
                if (editButton) {
                    const ticketId = editButton.dataset.ticketId;
                    this.openEditModal(ticketId);
                }
                const deleteButton = e.target.closest('.delete-ticket');
                if (deleteButton) {
                    const ticketId = deleteButton.dataset.ticketId;
                    this.deleteTicketById(ticketId);
                }
            });
        }

        // Add status filter listener
        const statusFilter = document.querySelector('.status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterTickets());
        }
    }

    async loadTickets() {
        try {
            const response = await fetch('/course/tickets/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Failed to load tickets');

            const data = await response.json();
            if (data.success) {
                this.tickets = data.tickets; // Store all tickets
                this.filterTickets(); // Apply current filters
            } else {
                console.error('Error loading tickets:', data.error);
                this.showAlert('danger', data.error || 'Fehler beim Laden der Tickets');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('danger', 'Fehler beim Laden der Tickets');
        }
    }

    filterTickets() {
        const statusFilter = document.querySelector('.status-filter').value;
        const searchQuery = document.querySelector('.search-input')?.value.toLowerCase() || '';

        const filteredTickets = this.tickets.filter(ticket => {
            const matchesStatus = statusFilter === 'all' || ticket.status === statusFilter;
            const matchesSearch = Object.values(ticket).some(value => 
                String(value).toLowerCase().includes(searchQuery)
            );
            return matchesStatus && matchesSearch;
        });

        this.renderTickets(filteredTickets);
    }

    renderTickets(tickets) {
        const tbody = document.querySelector('#ticketsTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = tickets.map(ticket => `
            <tr>
                <td>#${ticket.id}</td>
                <td>${ticket.subject}</td>
                <td>${ticket.user}</td>
                <td><span class="badge bg-${this.statusClassMap[ticket.status]}">${this.statusDisplayMap[ticket.status]}</span></td>
                <td>${ticket.created_at}</td>
                <td>${ticket.assigned_to || '-'}</td>
                <td>${ticket.resolution_notes || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary edit-ticket" data-ticket-id="${ticket.id}">
                        <i class="fas fa-edit"></i> Bearbeiten
                    </button>
                    <button class="btn btn-sm btn-outline-danger ms-1 delete-ticket" data-ticket-id="${ticket.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async openEditModal(ticketId) {
        try {
            const response = await fetch(`/course/tickets/${ticketId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Failed to load ticket details');

            const data = await response.json();
            if (data.success) {
                this.populateModal(data.ticket);
                this.ticketModal.show();
            } else {
                console.error('Error loading ticket details:', data.error);
                this.showAlert('danger', data.error || 'Fehler beim Laden der Ticket-Details');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('danger', 'Fehler beim Laden der Ticket-Details');
        }
    }

    populateModal(ticket) {
        document.getElementById('ticketId').value = ticket.id;
        document.getElementById('ticketSubject').value = ticket.subject;
        
        // Update description textarea
        const descriptionArea = document.getElementById('ticketDescription');
        descriptionArea.value = ticket.description;
        
        document.getElementById('ticketStatus').value = this.getStatusValue(ticket.status);
        document.getElementById('ticketAssignedTo').value = ticket.assigned_to_id || '';
        document.getElementById('ticketResolutionNotes').value = ticket.resolution_notes || '';
        
        // Handle image link
        const imageContainer = document.getElementById('ticketImageContainer');
        imageContainer.innerHTML = ''; // Clear previous content
        
        if (ticket.image) {
            const link = document.createElement('a');
            link.href = ticket.image;
            link.target = '_blank';
            link.className = 'd-block mt-2';
            link.innerHTML = '<i class="fas fa-image me-2"></i>Bild anzeigen';
            imageContainer.appendChild(link);
        }
    }

    getStatusValue(displayStatus) {
        // Convert display status back to backend value
        for (const [key, value] of Object.entries(this.statusDisplayMap)) {
            if (value === displayStatus) return key;
        }
        return 'open'; // Default to open if not found
    }

    async saveTicket() {
        const ticketId = document.getElementById('ticketId').value;
        const formData = {
            status: document.getElementById('ticketStatus').value,
            assigned_to: document.getElementById('ticketAssignedTo').value,
            resolution_notes: document.getElementById('ticketResolutionNotes').value
        };

        try {
            const response = await fetch(`/course/tickets/${ticketId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            if (data.success) {
                this.ticketModal.hide();
                await this.loadTickets(); // Refresh the tickets list
                this.showAlert('success', 'Ticket erfolgreich aktualisiert');
            } else {
                this.showAlert('danger', data.error || 'Fehler beim Speichern des Tickets');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('danger', 'Ein Fehler ist aufgetreten');
        }
    }

    async deleteTicket() {
        const ticketId = document.getElementById('ticketId').value;
        if (!ticketId) return;

        if (!confirm('Möchten Sie dieses Ticket wirklich löschen?')) {
            return;
        }

        try {
            const response = await fetch(`/course/tickets/${ticketId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            const data = await response.json();
            if (data.success) {
                this.ticketModal.hide();
                await this.loadTickets();
                this.showAlert('success', 'Ticket erfolgreich gelöscht');
            } else {
                this.showAlert('danger', data.error || 'Fehler beim Löschen des Tickets');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('danger', 'Ein Fehler ist aufgetreten');
        }
    }

    async deleteTicketById(ticketId) {
        if (!ticketId) return;
        if (!confirm('Möchten Sie dieses Ticket wirklich löschen?')) {
            return;
        }
        try {
            const response = await fetch(`/course/tickets/${ticketId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });
            const data = await response.json();
            if (data.success) {
                await this.loadTickets();
                this.showAlert('success', 'Ticket erfolgreich gelöscht');
            } else {
                this.showAlert('danger', data.error || 'Fehler beim Löschen des Tickets');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('danger', 'Ein Fehler ist aufgetreten');
        }
    }

    handleSearch(query) {
        this.filterTickets(); // Replace the old search logic with filterTickets
    }

    showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            setTimeout(() => alertDiv.remove(), 5000);
        }
    }
}

// Initialize ticket management when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('ticketsTable')) {
        new TicketManagement();
    }
}); 