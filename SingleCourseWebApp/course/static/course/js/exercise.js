/**
 * Toggles the collapse state of a collapsible element
 * @param {HTMLElement} element - The header element that triggers the collapse
 */
function handleCollapse(element) {
    // Toggle the collapsed class on the header
    element.classList.toggle('collapsed');
    
    // Find the content container
    const content = element.nextElementSibling;
    
    // Toggle the show class to trigger animation
    content.classList.toggle('show');
    
    // Update the icon direction
    const icon = element.querySelector('i');
    if (icon) {
        icon.style.transform = content.classList.contains('show') ? 'rotate(0deg)' : 'rotate(180deg)';
    }
}

/**
 * Handle exercise submission
 * @param {number} lessonId - The ID of the lesson being submitted
 * @returns {Promise} - A promise that resolves when the submission is complete
 */
async function handleSubmission(lessonId) {
    // Declare variables outside try block for finally access
    let originalText;
    const submitBtn = document.querySelector('.submit-btn');
    
    try {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Show loading state
        if (submitBtn) {
            originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Wird eingereicht...';
            submitBtn.disabled = true;
        }
        
        // Make submission request
        const response = await fetch(`/course/lesson/${lessonId}/submit-exercise/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update submission history with safe element check
            const userFullNameElement = document.querySelector('.user-fullname');
            const userName = userFullNameElement ? userFullNameElement.textContent : 'Unbekannter Benutzer';
            
            // Show success message
            alert('Übung erfolgreich eingereicht!');
            
            // Update submission history if it exists
            const submissionTable = document.querySelector('.submission-table tbody');
            if (submissionTable) {
                // Clear existing rows
                submissionTable.innerHTML = '';
                
                // Add new submission row
                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td>#${data.submission_id}</td>
                    <td>${data.submitted_at}</td>
                    <td>${userName}</td>
                    <td><span class="text-muted">Ausstehende Überprüfung</span></td>
                    <td><span class="badge bg-secondary">Ausstehend</span></td>
                `;
                submissionTable.appendChild(newRow);
            }
        } else {
            throw new Error(data.error || 'Einreichung fehlgeschlagen');
        }
    } catch (error) {
        alert('Fehler bei der Einreichung der Übung: ' + error.message);
    } finally {
        // Restore button state safely
        if (submitBtn && originalText) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
}

/**
 * Initialize all collapsible elements on the page
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set initial state for all collapsible elements
    const collapsibles = document.querySelectorAll('.collapsible-header');
    
    collapsibles.forEach(header => {
        // Show content by default
        const content = header.nextElementSibling;
        content.classList.add('show');
        
        // Remove any existing onclick attributes
        header.removeAttribute('onclick');
        
        // Add click event listener
        header.addEventListener('click', function() {
            handleCollapse(this);
        });
    });
    
    // Initialize submit button
    const submitBtn = document.querySelector('.submit-btn');
    if (submitBtn) {
        const lessonId = submitBtn.dataset.lessonId;
        submitBtn.addEventListener('click', () => {
            if (confirm('Sind Sie sicher, dass Sie diese Übung einreichen möchten? Diese Aktion kann nicht rückgängig gemacht werden.')) {
                handleSubmission(lessonId);
            }
        });
    }

    // Initialize launch button
    const launchBtn = document.querySelector('.launch-btn');
    if (launchBtn) {
        launchBtn.addEventListener('click', function() {
            const domain = this.dataset.domain;
            const group = this.dataset.group;
            const exerciseName = this.dataset.exerciseName;
            const notebookName = this.dataset.notebookName;
            
            // Detailed validation
            if (!domain) {
                alert('JupyterHub-Domain ist nicht konfiguriert. Bitte kontaktieren Sie Ihren Kursleiter.');
                return;
            }

            if (!group) {
                alert('Sie müssen einer Gruppe angehören, um auf das Labor zugreifen zu können.');
                return;
            }

            if (!exerciseName) {
                alert('Übungsname fehlt. Bitte kontaktieren Sie Ihren Kursleiter.');
                return;
            }

            if (!notebookName) {
                alert('Für diese Übung ist keine Notebook-Datei konfiguriert. Bitte kontaktieren Sie Ihren Kursleiter.');
                return;
            }

            // Encode path components individually to handle spaces and special characters
            const encodedExerciseName = encodeURIComponent(exerciseName);
            const encodedNotebookName = encodeURIComponent(notebookName);
            
            // Construct the path with encoded components
            const notebookPath = `${encodedExerciseName}/${encodedNotebookName}`;
            
            // Construct JupyterHub URL with encoded path
            const jupyterHubUrl = `https://${domain}/jupyterhub/hub/user/${group}/lab/tree/${notebookPath}`;
            
            // Log the final URL for debugging
            console.log('Opening JupyterHub URL:', jupyterHubUrl);
            
            // Open JupyterHub in new tab
            window.open(jupyterHubUrl, '_blank');
        });
    }
}); 