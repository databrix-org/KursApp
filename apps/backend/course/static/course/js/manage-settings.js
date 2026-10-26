document.addEventListener('DOMContentLoaded', function() {
    const settingsForm = document.getElementById('courseSettingsForm');
    const addCustomImageBtn = document.getElementById('addCustomImageBtn');
    const addCustomDomainBtn = document.getElementById('addCustomDomainBtn');
    const saveCustomImage = document.getElementById('saveCustomImage');
    const saveCustomDomain = document.getElementById('saveCustomDomain');
    const jupyterImageSelect = document.getElementById('jupyterImage');
    const domainNameSelect = document.getElementById('domainName');
    
    // Get course_id from URL path
    const urlPath = window.location.pathname;
    const courseIdMatch = urlPath.match(/\/manage\/(\d+)\//);
    const courseId = courseIdMatch ? courseIdMatch[1] : null;
    
    // Get CSRF token from cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Initialize Bootstrap modals
    const imageModal = new bootstrap.Modal(document.getElementById('addImageModal'));
    const domainModal = new bootstrap.Modal(document.getElementById('addDomainModal'));
    
    // Add custom image button click handler
    if (addCustomImageBtn) {
        addCustomImageBtn.addEventListener('click', function() {
            document.getElementById('customImageName').value = '';
            document.getElementById('customImageName').classList.remove('is-invalid');
            imageModal.show();
        });
    }
    
    // Add custom domain button click handler
    if (addCustomDomainBtn) {
        addCustomDomainBtn.addEventListener('click', function() {
            document.getElementById('customDomainName').value = '';
            document.getElementById('customDomainName').classList.remove('is-invalid');
            domainModal.show();
        });
    }
    
    // Save custom image click handler
    if (saveCustomImage) {
        saveCustomImage.addEventListener('click', function() {
            const customImageName = document.getElementById('customImageName').value.trim();
            
            if (!isValidDockerImage(customImageName)) {
                document.getElementById('customImageName').classList.add('is-invalid');
                return;
            }
            
            // Send the new image to the server
            const formData = new FormData();
            formData.append('image_name', customImageName);
            
            fetch(`/course/manage/${courseId}/add-image/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Add the new option to the dropdown
                    const option = document.createElement('option');
                    option.value = customImageName;
                    option.text = customImageName;
                    option.selected = true;
                    jupyterImageSelect.appendChild(option);
                    
                    // Close the modal
                    imageModal.hide();
                    
                    // Show success message
                    showAlert('success', 'JupyterLab Image erfolgreich hinzugefügt');
                } else {
                    // Show error message
                    showAlert('danger', data.error || 'Fehler beim Hinzufügen des JupyterLab Images');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'Ein Fehler ist aufgetreten');
            });
        });
    }
    
    // Save custom domain click handler
    if (saveCustomDomain) {
        saveCustomDomain.addEventListener('click', function() {
            const customDomainName = document.getElementById('customDomainName').value.trim();
            
            if (!isValidDomain(customDomainName)) {
                document.getElementById('customDomainName').classList.add('is-invalid');
                return;
            }
            
            // Send the new domain to the server
            const formData = new FormData();
            formData.append('domain_name', customDomainName);
            
            fetch(`/course/manage/${courseId}/add-domain/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Add the new option to the dropdown
                    const option = document.createElement('option');
                    option.value = customDomainName;
                    option.text = customDomainName;
                    option.selected = true;
                    domainNameSelect.appendChild(option);
                    
                    // Close the modal
                    domainModal.hide();
                    
                    // Show success message
                    showAlert('success', 'Domain erfolgreich hinzugefügt');
                } else {
                    // Show error message
                    showAlert('danger', data.error || 'Fehler beim Hinzufügen der Domain');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'Ein Fehler ist aufgetreten');
            });
        });
    }
    
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            // Convert checkbox value to boolean
            formData.set('is_published', formData.get('is_published') === 'on');
            
            // Get selected values
            const jupyterImage = jupyterImageSelect.value;
            const domainName = domainNameSelect.value;
            
            // Validate image name if provided
            if (jupyterImage && !isValidDockerImage(jupyterImage)) {
                alert('Bitte geben Sie einen gültigen Docker-Image-Namen ein (z.B. jupyter/datascience-notebook:latest)');
                return;
            }

            // Validate domain name if provided
            if (domainName && !isValidDomain(domainName)) {
                alert('Bitte geben Sie einen gültigen Domainnamen ein (z.B. jupyter.example.com)');
                return;
            }
            
            fetch(window.location.pathname + '?action=update_settings', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    showAlert('success', 'Einstellungen erfolgreich aktualisiert');
                } else {
                    // Show error message
                    showAlert('danger', data.error || 'Fehler beim Aktualisieren der Einstellungen');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Show error message
                showAlert('danger', 'Ein Fehler ist aufgetreten');
            });
        });
    }
    
    // Handle publish toggle confirmation
    const publishToggle = document.getElementById('isPublished');
    if (publishToggle) {
        let originalState = publishToggle.checked;
        
        publishToggle.addEventListener('change', function(e) {
            if (this.checked && !originalState) {
                // User is trying to publish the course
                if (!confirm('Nach der Veröffentlichung können Kursinhalte nicht mehr geändert werden. Sie dürfen auch kein Team löschen oder neues Team erstellen.\n\nAußerdem ist das Unpublishen des Kurses wärend der Veranstaltung nicht zu empfehlen, da die bearbeiteten Aufgaben von den Studierenden zurückgesetzt werden können.\n\nMöchten Sie den Kurs wirklich veröffentlichen?')) {
                    this.checked = originalState;
                    return;
                }
            } else if (!this.checked && originalState) {
                // User is trying to unpublish the course
                if (!confirm('Sind Sie sicher, dass Sie diesen Kurs nicht mehr veröffentlichen möchten? \n\nStudierende werden dann keinen Zugriff mehr darauf haben. \n\nNach Änderungen an den Modulen werden die bearbeiteten Aufgaben von den Studierenden zurückgesetzt.')) {
                    this.checked = originalState;
                    return;
                }
            }
            originalState = this.checked;
        });
    }
    
    // Function to show alert
    function showAlert(type, message) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        settingsForm.insertAdjacentElement('beforebegin', alert);
        
        // Auto dismiss after 3 seconds
        setTimeout(() => {
            alert.remove();
        }, 3000);
    }
    
    // Function to validate Docker image name
    function isValidDockerImage(imageName) {
        // Basic Docker image name validation
        // Format: [registry/]name[:tag]
        const regex = /^([a-z0-9]+(?:[._-][a-z0-9]+)*\/)?([a-z0-9]+(?:[._-][a-z0-9]+)*)(:[a-z0-9]+(?:[._-][a-z0-9]+)*)?$/;
        return regex.test(imageName);
    }

    // Function to validate domain name
    function isValidDomain(domain) {
        // Basic domain name validation
        // Format: subdomain.domain.tld
        const regex = /^[a-zA-Z0-9][a-zA-Z0-9-_.]+[a-zA-Z0-9]$/;
        return regex.test(domain) && domain.includes('.');
    }
}); 