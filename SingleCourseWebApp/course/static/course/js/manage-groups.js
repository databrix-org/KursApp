document.addEventListener('DOMContentLoaded', function() {
    // Get course ID from data attribute
    const courseId = document.body.dataset.courseId;
    const createGroupBtn = document.getElementById('createGroupBtn');
    const groupsTable = document.getElementById('groupsTable');
    const membersModal = document.getElementById('membersModal');
    const studentSelect = document.getElementById('studentSelect');
    const addStudentBtn = document.getElementById('addStudentBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const membersLoadingSpinner = document.getElementById('membersLoadingSpinner');
    const toast = new bootstrap.Toast(document.getElementById('toastNotification'));
    let currentGroupId = null;

    // Show notification
    function showNotification(title, message, isError = false) {
        const toastEl = document.getElementById('toastNotification');
        const titleEl = document.getElementById('toastTitle');
        const messageEl = document.getElementById('toastMessage');
        
        toastEl.classList.remove('bg-danger', 'text-white');
        if (isError) {
            toastEl.classList.add('bg-danger', 'text-white');
        }
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        toast.show();
    }

    // Toggle loading spinner
    function toggleLoading(show, spinnerEl = loadingSpinner) {
        spinnerEl.classList.toggle('d-none', !show);
    }

    // Only add event listener if button exists and is not disabled
    if (createGroupBtn && !createGroupBtn.disabled) {
        createGroupBtn.addEventListener('click', async () => {
            try {
                toggleLoading(true);
                const response = await fetch(`/course/manage/${courseId}/groups/create/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });
                const data = await response.json();
                if (response.ok) {
                    showNotification('Success', 'New group created successfully');
                    location.reload();
                } else {
                    throw new Error(data.error || 'Failed to create group');
                }
            } catch (error) {
                console.error('Error creating group:', error);
                showNotification('Error', error.message || 'Failed to create group', true);
            } finally {
                toggleLoading(false);
            }
        });
    }

    if (groupsTable) {
        groupsTable.addEventListener('click', async (e) => {
            if (e.target.closest('.delete-group-btn')) {
                const btn = e.target.closest('.delete-group-btn');
                const groupId = btn.dataset.groupId;
                if (confirm('Sind Sie sicher, dass Sie dieses Team löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.')) {
                    try {
                        toggleLoading(true);

                        const response = await fetch(`/course/manage/${courseId}/groups/${groupId}/delete/`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': getCookie('csrftoken'),
                            },
                        });
                        if (response.ok) {
                            btn.closest('tr').remove();
                            showNotification('Success', 'Group deleted successfully');
                        } else {
                            const data = await response.json();
                            throw new Error(data.error || 'Failed to delete group');
                        }
                    } catch (error) {
                        console.error('Error deleting group:', error);
                        showNotification('Error', error.message || 'Failed to delete group', true);
                    } finally {
                        toggleLoading(false);
                    }
                }
            }
        });
    }

    if (membersModal) {
        membersModal.addEventListener('show.bs.modal', async (e) => {
            const button = e.relatedTarget;
            if (!button) return;
            
            currentGroupId = button.dataset.groupId;
            console.log('Modal opened for group:', currentGroupId);
            
            if (studentSelect) studentSelect.value = '';
            if (addStudentBtn) addStudentBtn.disabled = true;
            await loadGroupMembers(currentGroupId);
        });
    }

    if (studentSelect) {
        studentSelect.addEventListener('change', (e) => {
            if (addStudentBtn) addStudentBtn.disabled = !e.target.value;
        });
    }

    if (addStudentBtn) {
        addStudentBtn.addEventListener('click', async () => {
            const studentId = studentSelect.value;
            console.log('Adding student:', studentId, 'to group:', currentGroupId);
            
            if (!studentId || !currentGroupId) {
                console.log('Missing studentId or currentGroupId:', { studentId, currentGroupId });
                return;
            }

            try {
                toggleLoading(true, membersLoadingSpinner);
                const formData = new FormData();
                formData.append('student_id', studentId);
                
                const response = await fetch(`/course/manage/${courseId}/groups/${currentGroupId}/add-member/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData
                });
                
                const data = await response.json();
                if (response.ok) {
                    await loadGroupMembers(currentGroupId);
                    updateMemberCount(currentGroupId, data.member_count);
                    studentSelect.value = '';
                    addStudentBtn.disabled = true;
                    showNotification('Success', 'Member added successfully');
                } else {
                    throw new Error(data.error || 'Failed to add member');
                }
            } catch (error) {
                console.error('Error adding member:', error);
                showNotification('Error', error.message || 'Failed to add member', true);
            } finally {
                toggleLoading(false, membersLoadingSpinner);
            }
        });
    }

    async function loadGroupMembers(groupId) {
        try {
            toggleLoading(true, membersLoadingSpinner);
            const response = await fetch(`/course/api/groups/${groupId}/members/`);
            const members = await response.json();
            const membersList = document.getElementById('membersList');
            
            if (!response.ok) {
                throw new Error('Failed to load members');
            }

            membersList.innerHTML = members.map(member => `
                <div class="list-group-item d-flex justify-content-between align-items-start">
                    <div class="member-info">
                        <div class="member-name">
                            <i class="fas fa-user me-2"></i>${member.full_name}
                        </div>
                        <div class="member-detail">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-envelope me-2"></i>
                                <span>${member.email}</span>
                                <button class="btn btn-sm btn-link ms-2 email-single-member" 
                                        data-email="${member.email}"
                                        title="E-Mail an dieses Mitglied">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                        <div class="member-detail">
                            <i class="fas fa-clock"></i>
                            <span>Zuletzt aktiv: ${member.last_active}</span>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-outline-danger remove-member-btn" 
                            data-student-id="${member.id}">
                        <i class="fas fa-user-minus me-1"></i>Entfernen
                    </button>
                </div>
            `).join('');

            // Add event listeners for remove buttons
            membersList.querySelectorAll('.remove-member-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const studentId = e.target.dataset.studentId;
                    if (confirm('Are you sure you want to remove this member?')) {
                        try {
                            toggleLoading(true, membersLoadingSpinner);
                            const formData = new FormData();
                            formData.append('student_id', studentId);

                            const response = await fetch(`/course/manage/${courseId}/groups/${currentGroupId}/remove-member/`, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken'),
                                },
                                body: formData
                            });
                            const data = await response.json();
                            if (response.ok) {
                                e.target.closest('.list-group-item').remove();
                                updateMemberCount(currentGroupId, data.member_count);
                                showNotification('Success', 'Member removed successfully');
                            } else {
                                throw new Error(data.error || 'Failed to remove member');
                            }
                        } catch (error) {
                            console.error('Error removing member:', error);
                            showNotification('Error', error.message || 'Failed to remove member', true);
                        } finally {
                            toggleLoading(false, membersLoadingSpinner);
                        }
                    }
                });
            });

            // Add event listener for single member email buttons
            membersList.querySelectorAll('.email-single-member').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const email = e.target.closest('.email-single-member').dataset.email;
                    const courseTitle = document.body.dataset.courseTitle || 'Course';
                    const mailtoLink = `mailto:${email}?subject=Course: ${encodeURIComponent(courseTitle)}`;
                    window.location.href = mailtoLink;
                });
            });
        } catch (error) {
            console.error('Error loading members:', error);
            showNotification('Error', 'Failed to load members', true);
        } finally {
            toggleLoading(false, membersLoadingSpinner);
        }
    }

    function updateMemberCount(groupId, count) {
        const row = document.querySelector(`tr[data-group-id="${groupId}"]`);
        if (row) {
            row.querySelector('.member-count').textContent = count;
        }
    }

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

    // Handle workspace viewing
    document.querySelectorAll('.view-workspace-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const domain = this.dataset.domain;
            const group = this.dataset.group;
            const exerciseName = this.dataset.exerciseName;

            if (!domain) {
                showNotification('Error', 'JupyterHub domain not configured', true);
                return;
            }

            if (!group) {
                showNotification('Error', 'Group information missing', true);
                return;
            }

            const jupyterHubUrl = `https://${domain}/jupyterhub/hub/user/${group}/lab`;
            window.open(jupyterHubUrl, '_blank');
        });
    });

    // Direct email functionality with automatic recipient population
    document.querySelectorAll('.email-group-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const groupId = e.target.closest('.email-group-btn').dataset.groupId;
            try {
                toggleLoading(true);
                const response = await fetch(`/course/api/groups/${groupId}/members/`);
                if (!response.ok) {
                    throw new Error('Failed to load member emails');
                }
                const members = await response.json();
                
                // Extract email addresses from the members data
                const emailAddresses = members.map(member => member.email).join(',');
                
                // Create and open mailto link
                const courseTitle = document.body.dataset.courseTitle || 'Course';
                const mailtoLink = `mailto:${emailAddresses}?subject=Course: ${encodeURIComponent(courseTitle)}`;
                window.location.href = mailtoLink;
            } catch (error) {
                console.error('Error loading member emails:', error);
                showNotification('Error', error.message || 'Failed to load member emails', true);
            } finally {
                toggleLoading(false);
            }
        });
    });
}); 