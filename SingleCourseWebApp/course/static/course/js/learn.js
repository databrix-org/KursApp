document.addEventListener('DOMContentLoaded', function() {
    // Set progress bar width
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const progress = progressFill.getAttribute('data-progress');
        progressFill.style.width = `${progress}%`;
    }
}); 