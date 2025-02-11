document.addEventListener('DOMContentLoaded', function() {
    const lessonId = document.getElementById('lesson-id').value;
    const lessonContainer = document.querySelector('.lesson-detail-container');
    const sidebar = document.getElementById('lessonSidebar');
    
    // Initial check
    if (sidebar.classList.contains('collapsed')) {
        lessonContainer.classList.add('sidebar-collapsed');
    }
    
    // Watch for sidebar toggle
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.classList.contains('collapsed')) {
                lessonContainer.classList.add('sidebar-collapsed');
            } else {
                lessonContainer.classList.remove('sidebar-collapsed');
            }
        });
    });
    
    observer.observe(sidebar, { attributes: true });
    
    // Update the completion button handler
    const completeButton = document.getElementById('completeButton');
    if (completeButton) {
        if (completeButton.hasAttribute('completed')) {
            completeButton.textContent = 'Abgeschlossen';
        } else {
            completeButton.textContent = 'Lektion abschließen';
        }
        
        completeButton.addEventListener('click', async function() {
            try {
                const response = await fetch(`/course/lesson/${lessonId}/complete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    const data = await response.json();
                    completeButton.disabled = data.is_completed;
                    completeButton.textContent = data.is_completed ? 'Abgeschlossen' : 'Lektion abschließen';
                    
                    // Only navigate if we're marking as complete and there's a next lesson
                    if (data.next_lesson_id) {
                        window.location.href = `/course/lesson/${data.next_lesson_id}/`;
                    }
                }
            } catch (error) {
                console.error('Error toggling lesson completion:', error);
            }
        });
    }
});

// Helper function to get CSRF token
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