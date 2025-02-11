document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('lessonSidebar');
    const toggleBtn = document.getElementById('toggleSidebar');
    
    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
    });

    // Add click handlers for module headers
    const moduleHeaders = document.querySelectorAll('.module-header');
    moduleHeaders.forEach(header => {
        header.addEventListener('click', function(e) {
            // Prevent event from bubbling up
            e.stopPropagation();
            const moduleSection = this.parentElement;
            moduleSection.classList.toggle('collapsed');
        });
    });
}); 