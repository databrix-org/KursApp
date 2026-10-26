let currentFileType = null;
let currentFile = null;
let referenceContent = null;
let markdownConverter;

// Initialize markdown converter
document.addEventListener('DOMContentLoaded', function() {
    // Try to initialize markdown converter
    if (typeof showdown === 'object' && typeof showdown.Converter === 'function') {
        markdownConverter = new showdown.Converter();
    }

    // Initialize reference solution if available
    if (initialReferenceSolution) {
        referenceContent = JSON.stringify(initialReferenceSolution);
    }
});

function initGradingForm(submissionId, returnUrl) {
    // Only initialize editor if the element exists
    const editorElement = document.getElementById('editor');
    if (editorElement && !window.editor) {
        window.editor = ace.edit("editor");
        window.editor.setTheme("ace/theme/github");
        window.editor.session.setMode("ace/mode/python");
        window.editor.setReadOnly(true);
        window.editor.setOptions({
            fontSize: "14px",
            showPrintMargin: false,
            showGutter: true,
            highlightActiveLine: false,
            wrap: true
        });
    }

    // Add event listener to enforce maximum points
    const scoreInput = document.getElementById('score');
    if (scoreInput) {
        scoreInput.addEventListener('input', function() {
            const maxPoints = parseFloat(this.getAttribute('max'));
            const currentValue = parseFloat(this.value);
            
            if (!isNaN(currentValue) && currentValue > maxPoints) {
                this.value = maxPoints;
            }
        });
    }

    // Initialize file upload handling
    const referenceUpload = document.getElementById('referenceUpload');
    if (referenceUpload) {
        referenceUpload.addEventListener('change', handleReferenceUpload);
    }

    // Hide back button as we won't need it
    const backButton = document.getElementById('backToFiles');
    if (backButton) {
        backButton.style.display = 'none';
    }

    // Initialize grading form
    const form = document.getElementById('gradingForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitGrade(submissionId, returnUrl);
        });
    }

    // Automatically select the first Jupyter notebook and show diff if reference exists
    const fileItems = document.querySelectorAll('.file-item');
    const notebookFile = Array.from(fileItems).find(item => 
        item.dataset.fileType.includes('.ipynb')
    );

    if (notebookFile) {
        loadSubmissionFile(notebookFile);
    }

    // Hide the file list as we don't need it
    hideFileList();

    // Add event listener for points inputs
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('points-input')) {
            updateTotalPoints();
        }
    });
}

function handleReferenceUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.ipynb')) {
        alert('Please upload a Jupyter notebook file (.ipynb)');
        event.target.value = '';
        return;
    }

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Get exercise ID from the URL or data attribute
    const exerciseId = document.querySelector('[data-exercise-id]').dataset.exerciseId;

    // Send file to server
    fetch(`/course/exercise/${exerciseId}/upload-reference/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update reference content
            referenceContent = data.reference_solution;
            
            // Update UI to show reference solution is available
            const referenceInfo = document.querySelector('.reference-solution-info');
            if (referenceInfo) {
                referenceInfo.innerHTML = '<span class="badge bg-info">Referenzlösung verfügbar</span>';
            }
            
            // Update button text
            const uploadButton = document.querySelector('.reference-upload button');
            if (uploadButton) {
                uploadButton.innerHTML = '<i class="fas fa-sync"></i> Referenzlösung ändern';
            }
            
            // Reload current file with new reference
            if (currentFile) {
                loadSubmissionFile(currentFile);
            }
        } else {
            alert('Error uploading reference solution: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error uploading reference solution');
    });

    // Clear the file input
    event.target.value = '';
}

function loadSubmissionFile(element) {
    currentFile = element;
    currentFileType = element.dataset.fileType;
    const fileUrl = element.dataset.fileUrl;

    // Update active state
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('active');
    });
    element.classList.add('active');

    fetch(fileUrl)
        .then(response => response.text())
        .then(content => {
            if (currentFileType.includes('.ipynb')) {
                if (referenceContent) {
                    displayNotebookDiff(referenceContent, content);
                } else {
                    displayNotebook(content);
                }
                hideFileList();
            } else {
                displayPythonFile(content);
                hideFileList();
            }
        })
        .catch(error => {
            console.error('Error loading file:', error);
            alert('Error loading submission file');
        });
}

function displayNotebook(content) {
    const viewer = document.querySelector('.notebook-viewer');
    const editorContainer = document.querySelector('.editor-container');
    
    if (editorContainer) {
        editorContainer.style.display = 'none';
    }
    
    if (viewer) {
        viewer.style.display = 'block';
        
        try {
            const notebook = JSON.parse(content);
            nbviewer.render(notebook, viewer);
        } catch (error) {
            console.error('Error parsing notebook:', error);
            viewer.innerHTML = '<div class="alert alert-danger">Error loading notebook</div>';
        }
    }
}

function displayNotebookDiff(referenceContent, submissionContent) {
    const viewer = document.querySelector('.notebook-viewer');
    const editorContainer = document.querySelector('.editor-container');
    
    if (editorContainer) {
        editorContainer.style.display = 'none';
    }
    
    if (viewer) {
        viewer.style.display = 'block';
        
        try {
            const reference = JSON.parse(referenceContent);
            const submission = JSON.parse(submissionContent);
            
            // Clear outputs from both notebooks
            clearNotebookOutputs(reference);
            clearNotebookOutputs(submission);
            
            // Compare notebooks and create diff view
            const diffHtml = generateNotebookDiff(reference, submission);
            viewer.innerHTML = diffHtml;
            
            // Apply syntax highlighting to code cells
            if (window.hljs) {
                viewer.querySelectorAll('pre code').forEach(block => {
                    hljs.highlightBlock(block);
                });
            }
        } catch (error) {
            console.error('Error creating notebook diff:', error);
            viewer.innerHTML = '<div class="alert alert-danger">Error comparing notebooks</div>';
        }
    }
}

function clearNotebookOutputs(notebook) {
    if (notebook.cells) {
        notebook.cells.forEach(cell => {
            if (cell.cell_type === 'code') {
                cell.outputs = [];
                cell.execution_count = null;
            }
        });
    }
}

function generateNotebookDiff(reference, submission) {
    let diffHtml = '<div class="notebook-diff">';
    
    // Header with total points only
    diffHtml += `
        <div class="comparison-header">
            <div class="comparison-title">Referenzlösung</div>
            <div class="comparison-title">Studentenlösung</div>
        </div>
    `;
    
    const refCells = reference.cells || [];
    const subCells = submission.cells || [];
    const maxCells = Math.max(refCells.length, subCells.length);
    
    for (let i = 0; i < maxCells; i++) {
        const refCell = refCells[i];
        const subCell = subCells[i];
        
        if (!refCell) {
            // Added cell in student submission
            diffHtml += `<div class="cell-comparison">
                <div></div>
                ${generateCellHtml(subCell, 'added')}
            </div>`;
        } else if (!subCell) {
            // Cell only in reference
            diffHtml += `<div class="cell-comparison">
                ${generateCellHtml(refCell, 'removed')}
                <div></div>
            </div>`;
        } else {
            const refContent = getCellContent(refCell);
            const subContent = getCellContent(subCell);
            
            if (refContent === subContent) {
                // Identical cells
                diffHtml += `<div class="cell-single">
                    ${generateCellHtml(refCell, 'unchanged')}
                </div>`;
            } else {
                // Different cells
                diffHtml += `<div class="cell-comparison">
                    ${generateCellHtml(refCell, 'removed')}
                    ${generateCellHtml(subCell, 'added')}
                </div>`;
            }
        }
    }
    
    diffHtml += '</div>';
    return diffHtml;
}

function getCellContent(cell) {
    if (cell.cell_type === 'code') {
        return cell.source.join('');
    } else {
        return cell.source.join('');
    }
}

function generateCellHtml(cell, status) {
    const cellClass = `diff-${status}`;
    let html = `<div class="notebook-cell ${cellClass}">`;
    
    // Add cell content without the cell type indicator
    if (cell.cell_type === 'code') {
        html += '<div class="cell-content"><pre><code class="python">';
        html += escapeHtml(cell.source.join(''));
        html += '</code></pre>';
        
        // Add outputs if they exist
        if (cell.outputs && cell.outputs.length > 0) {
            html += '<div class="cell-outputs">';
            cell.outputs.forEach(output => {
                if (output.output_type === 'stream') {
                    html += `<pre class="output-stream">${escapeHtml(output.text.join(''))}</pre>`;
                } else if (output.output_type === 'execute_result' || output.output_type === 'display_data') {
                    if (output.data['text/plain']) {
                        html += `<pre class="output-result">${escapeHtml(output.data['text/plain'].join(''))}</pre>`;
                    }
                }
            });
            html += '</div>';
        }
        
        html += '</div>';
    } else {
        // Markdown or raw cell
        html += '<div class="cell-content">';
        try {
            const markdownText = cell.source.join('');
            if (markdownConverter) {
                html += markdownConverter.makeHtml(markdownText);
            } else {
                html += `<pre>${escapeHtml(markdownText)}</pre>`;
            }
        } catch (error) {
            console.error('Error rendering markdown:', error);
            html += `<pre>${escapeHtml(cell.source.join(''))}</pre>`;
        }
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

function displayPythonFile(content) {
    const viewer = document.querySelector('.notebook-viewer');
    viewer.style.display = 'none';
    editor.container.style.display = 'block';
    
    editor.setValue(content);
    editor.clearSelection();
    editor.scrollToLine(0);
}

// Modify hideFileList to permanently hide the file list
function hideFileList() {
    const fileList = document.getElementById('submissionFileList');
    const backButton = document.getElementById('backToFiles');
    if (fileList) fileList.style.display = 'none';
    if (backButton) backButton.style.display = 'none';
}

function submitGrade(submissionId, returnUrl) {
    const score = document.getElementById('score').value;
    const feedback = document.getElementById('feedback').value;
    const maxPoints = parseFloat(document.getElementById('score').getAttribute('max'));

    // Validate score
    if (score === '' || isNaN(score)) {
        alert('Please enter a valid score');
        return;
    }
    
    // Enforce maximum points
    let finalScore = parseFloat(score);
    if (finalScore > maxPoints) {
        alert(`Die maximale Punktzahl für diese Übung ist ${maxPoints}. Ihr eingegebener Wert wurde angepasst.`);
        finalScore = maxPoints;
        document.getElementById('score').value = maxPoints;
    }

    fetch(`/course/submissions/${submissionId}/grade/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            score: finalScore,
            feedback: feedback
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Network response was not ok');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            window.location.href = returnUrl;
        } else {
            alert('Error saving grade: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving grade: ' + error.message);
    });
}

// Helper function to get CSRF token
function getCsrfToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenElement ? tokenElement.value : '';
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function updateTotalPoints() {
    const inputs = document.querySelectorAll('.points-input');
    const total = Array.from(inputs)
        .map(input => parseFloat(input.value) || 0)
        .reduce((sum, current) => sum + current, 0);
    
    document.getElementById('totalPoints').textContent = total.toFixed(1);
    document.getElementById('score').value = total.toFixed(1);
} 