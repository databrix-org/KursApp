function initSubmissionsTable() {
    const table = $('#submissionsTable');
    
    // Check if DataTable already exists
    if ($.fn.dataTable.isDataTable(table)) {
        return;
    }

    // Initialize DataTable
    table.DataTable({
        order: [[2, 'desc']],
        pageLength: 25, // Show 25 entries per page
        language: {
            search: "Suche in Abgaben:",
            lengthMenu: "_MENU_ Einträge pro Seite",
            info: "Zeige _START_ bis _END_ von _TOTAL_ Einträgen",
            infoEmpty: "Keine Einträge verfügbar",
            infoFiltered: "(gefiltert aus _MAX_ Einträgen)",
            zeroRecords: "Keine passenden Einträge gefunden",
            paginate: {
                first: "Erste",
                last: "Letzte",
                next: "Nächste",
                previous: "Vorherige"
            }
        },
        ajax: {
            url: window.location.href,
            dataSrc: function(json) {
                if (!json.success) {
                    // Handle error cases
                    if (json.error) {
                        showError(json.error);
                    }
                    return [];
                }
                return json.submissions || [];
            },
            error: function(xhr, error, thrown) {
                if (xhr.status === 403) {
                    // Handle permission denied
                    showError('Sie haben keine Berechtigung, diese Abgaben einzusehen.');
                    // Redirect to home page after a delay
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 3000);
                } else {
                    showError('Beim Laden der Abgaben ist ein Fehler aufgetreten.');
                }
            }
        },
        columns: [
            { 
                data: 'group',
                title: 'Gruppe'
            },
            {
                data: 'submitted_at',
                title: 'Eingereicht am'
            },
            {
                data: 'score',
                title: 'Bewertung',
                render: function(data, type, row) {
                    return data !== null ? data : 'Ausstehend';
                }
            },
            /*
            {
                data: 'passed',
                title: 'Status',
                render: function(data, type, row) {
                    if (row.score === null) return 'Pending';
                    return data ? 'Passed' : 'Failed';
                }
            },
            */
            {
                data: 'files',
                title: 'Dateien',
                render: function(data, type, row) {
                    if (!data || !data.length) return 'Keine Dateien';
                    return data.map(file => 
                        `<a href="${file.url}" target="_blank">${file.name}</a>`
                    ).join('<br>');
                }
            },
            {
                data: 'id',
                title: 'Aktionen',
                render: function(data, type, row) {
                    return `<a href="/course/submissions/${data}/grade/" class="btn btn-primary btn-sm">Bewerten</a>`;
                }
            }
        ],
        columnDefs: [
            { orderable: false, targets: [0, 3] }
        ]
    });
    
    // Handle submission filtering
    document.getElementById('submissionFilter')?.addEventListener('change', function() {
        const filterValue = this.value;
        table.DataTable().column(2).search( // Score column index
            filterValue === 'pending' ? '^Pending$' :
            filterValue === 'graded' ? '^[0-9]' : '',
            true, // Use regex
            false // Exact match for 'Pending'
        ).draw();
    });
}

function initGradingView() {
    // Add declarations inside the function
    let currentFileType = null;
    let editor = null;
    let referenceNotebook = null;
    
    // Initialize ACE editor
    if (!window.editor) {
        window.editor = ace.edit("editor");
        window.editor.setTheme("ace/theme/monokai");
        window.editor.session.setMode("ace/mode/python");
        window.editor.setReadOnly(true);
    }

    // Initialize file upload handling
    const referenceUpload = document.getElementById('referenceUpload');
    if (referenceUpload) {
        referenceUpload.addEventListener('change', handleReferenceUpload);
    }

    // Initialize back button
    const backButton = document.getElementById('backToFiles');
    if (backButton) {
        backButton.addEventListener('click', showFileList);
    }

    // Show file list by default
    showFileList();
}

function handleReferenceUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        if (file.name.endsWith('.ipynb')) {
            displayNotebook(e.target.result, 'referenceViewer');
        } else {
            displayPythonFile(e.target.result, 'referenceViewer');
        }
    };
    reader.readAsText(file);
}

function loadSubmissionFile(element) {
    currentFile = element;
    currentFileType = element.dataset.fileType;
    const fileUrl = element.dataset.fileUrl;

    fetch(fileUrl)
        .then(response => response.text())
        .then(content => {
            if (currentFileType.includes('.ipynb')) {
                displayNotebook(content, 'submissionViewer');
                hideFileList();
            } else {
                displayPythonFile(content, 'submissionViewer');
                hideFileList();
            }
        })
        .catch(error => console.error('Error loading file:', error));
}

function displayNotebook(content, containerId) {
    const container = document.getElementById(containerId);
    
    // Create notebook viewer element if it doesn't exist
    let viewer = container.querySelector('.notebook-viewer');
    if (!viewer) {
        viewer = document.createElement('div');
        viewer.className = 'notebook-viewer';
        container.appendChild(viewer);
    }

    // Clear previous content and show viewer
    viewer.innerHTML = '';
    viewer.style.display = 'block';
    
    // Use nbviewer to render the notebook
    const notebook = JSON.parse(content);
    viewer.render(notebook, viewer);
}

function displayPythonFile(content, containerId) {
    const container = document.getElementById(containerId);
    
    if (containerId === 'submissionViewer') {
        // Ensure editor container is visible
        const editorContainer = container.querySelector('.editor-container');
        if (editorContainer) {
            editorContainer.style.display = 'block';
        }
        editor.setValue(content);
        editor.clearSelection();
    } else {
        // Create code container if it doesn't exist
        let codeContainer = container.querySelector('pre code');
        if (!codeContainer) {
            codeContainer = document.createElement('code');
            const pre = document.createElement('pre');
            pre.appendChild(codeContainer);
            container.appendChild(pre);
        }
        codeContainer.innerHTML = escapeHtml(content);
        hljs.highlightElement(codeContainer);
    }
    
    // Hide other viewers
    const notebookViewer = container.querySelector('.notebook-viewer');
    if (notebookViewer) {
        notebookViewer.style.display = 'none';
    }
}

function hideFileList() {
    const fileList = document.getElementById('submissionFileList');
    const backButton = document.getElementById('backToFiles');
    if (fileList) fileList.style.display = 'none';
    if (backButton) backButton.style.display = 'block';
}

function showFileList() {
    const fileList = document.getElementById('submissionFileList');
    const backButton = document.getElementById('backToFiles');
    if (fileList) fileList.style.display = 'block';
    if (backButton) backButton.style.display = 'none';
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.role = 'alert';
    errorDiv.textContent = message;
    
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initSubmissionsTable();
    
    // Only initialize grading view if on grading page
    if (document.getElementById('gradingForm')) {
        initGradingView();
    }
}); 