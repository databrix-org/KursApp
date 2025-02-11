document.addEventListener('DOMContentLoaded', function() {
    const settingsForm = document.getElementById('courseSettingsForm');
    
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            // Convert checkbox value to boolean
            formData.set('is_published', formData.get('is_published') === 'on');
            
            // Get JupyterLab image name and domain name
            const jupyterImage = document.getElementById('jupyterImage');
            const domainName = document.getElementById('domainName');
            
            // Validate image name if provided
            if (jupyterImage.value.trim() && !isValidDockerImage(jupyterImage.value.trim())) {
                alert('Bitte geben Sie einen gültigen Docker-Image-Namen ein (z.B. jupyter/datascience-notebook:latest)');
                return;
            }

            // Validate domain name if provided
            if (domainName.value.trim() && !isValidDomain(domainName.value.trim())) {
                alert('Bitte geben Sie einen gültigen Domainnamen ein (z.B. jupyter.example.com)');
                return;
            }
            
            fetch(window.location.pathname + '?action=update_settings', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-success alert-dismissible fade show mt-3';
                    alert.innerHTML = `
                        Settings updated successfully
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    settingsForm.insertAdjacentElement('beforebegin', alert);
                    
                    // Update image info if provided
                    if (data.jupyterlab_image) {
                        const imageInfo = document.querySelector('.text-success');
                        if (imageInfo) {
                            imageInfo.innerHTML = `
                                <i class="bi bi-check-circle"></i>
                                Current image: ${data.jupyterlab_image.name}
                            `;
                        }
                    }

                    // Update domain info if provided
                    if (data.domain_name) {
                        const domainInfo = document.querySelectorAll('.text-success')[1];
                        if (domainInfo) {
                            domainInfo.innerHTML = `
                                <i class="bi bi-check-circle"></i>
                                Current domain: ${data.domain_name}
                            `;
                        }
                    }
                    
                    // Auto dismiss after 3 seconds
                    setTimeout(() => {
                        alert.remove();
                    }, 3000);
                } else {
                    // Show error message
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-danger alert-dismissible fade show mt-3';
                    alert.innerHTML = `
                        ${data.error || 'Failed to update settings'}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    settingsForm.insertAdjacentElement('beforebegin', alert);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Show error message
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show mt-3';
                alert.innerHTML = `
                    An error occurred while updating settings
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                settingsForm.insertAdjacentElement('beforebegin', alert);
            });
        });
    }
    
    // Handle publish toggle confirmation
    const publishToggle = document.getElementById('isPublished');
    if (publishToggle) {
        let originalState = publishToggle.checked;
        
        publishToggle.addEventListener('change', function(e) {
            if (!this.checked && originalState) {
                if (!confirm('Sind Sie sicher, dass Sie diesen Kurs nicht mehr veröffentlichen möchten? Studierende werden dann keinen Zugriff mehr darauf haben.')) {
                    this.checked = originalState;
                    return;
                }
            }
            originalState = this.checked;
        });
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