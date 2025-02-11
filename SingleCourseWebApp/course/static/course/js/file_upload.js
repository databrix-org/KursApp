class FileUploadHandler {
    constructor(formElement, progressBarElement) {
        this.form = formElement;
        this.progressBar = progressBarElement;
        this.uploadId = null;
        this.progressCheckInterval = null;
        this.setupFormSubmit();
        this.setupFileValidation();
    }

    setupFormSubmit() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadId = Date.now().toString();
            this.startUpload();
        });
    }

    setupFileValidation() {
        const fileInputs = this.form.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                const maxSize = 1024 * 1024 * 1024; // 1GB
                
                files.forEach(file => {
                    if (file.size > maxSize) {
                        alert(`File ${file.name} is too large. Maximum size is 1GB.`);
                        e.target.value = '';
                    }
                });
            });
        });
    }

    startUpload() {
        // Show progress bar
        this.progressBar.style.width = '0%';
        this.progressBar.textContent = '0%';
        this.progressBar.parentElement.style.display = 'block';

        // Start progress checking
        this.progressCheckInterval = setInterval(() => {
            this.checkProgress();
        }, 1000);

        // Submit the form
        const formData = new FormData(this.form);
        formData.append('upload_id', this.uploadId);

        fetch(this.form.action, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(this.progressCheckInterval);
            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                alert('Upload failed: ' + data.error);
            }
        })
        .catch(error => {
            clearInterval(this.progressCheckInterval);
            alert('Upload failed: ' + error);
        });
    }

    checkProgress() {
        fetch(`/course/check-upload-progress/?upload_id=${this.uploadId}`)
            .then(response => response.json())
            .then(data => {
                if (data.progress !== undefined) {
                    const progress = Math.round(data.progress);
                    this.progressBar.style.width = `${progress}%`;
                    this.progressBar.textContent = `${progress}%`;
                }
            })
            .catch(error => {
                console.error('Error checking progress:', error);
            });
    }
}

// Initialize the handler when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form[enctype="multipart/form-data"]');
    const progressBar = document.querySelector('.progress-bar');
    
    if (form && progressBar) {
        new FileUploadHandler(form, progressBar);
    }
}); 