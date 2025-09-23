/**
 * Module Management JavaScript
 * 
 * This module handles all client-side functionality for managing course modules and lessons,
 * including:
 * 
 * 1. Module Management (CRUD operations)
 * 2. Lesson Management (CRUD operations)
 * 3. Content Editors (Quill)
 * 4. Exercise Management
 * 5. UI Utilities
 * 6. Event Handlers
 * 
 * @module manage-modules
 */

// ============================================================================
// Global Variables
// ============================================================================

/** @type {number|null} Current module ID being edited */
let currentModuleId = null;

/** @type {number|null} Current lesson ID being edited */
let currentLessonId = null;

/** @type {Quill|null} Quill editor instance for reading content */
let readingQuill = null;

/** @type {Quill|null} Quill editor instance for traditional exercises */
let traditionalQuill = null;

/** @type {Quill|null} Quill editor instance for programming exercises */
let programmingQuill = null;

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get CSRF token from the page.
 * @returns {string} CSRF token value
 */
function getCsrfToken() {
    // First try to get from cookie
    const csrfCookie = document.cookie
        .split(';')
        .map(cookie => cookie.trim())
        .find(cookie => cookie.startsWith('csrftoken='));
    
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    
    // Then try to get from meta tag
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    console.error('CSRF token not found');
    return '';
}

/**
 * Initialize Quill editors with common configuration.
 */
function initializeQuillEditors() {
    const quillOptions = {
        theme: 'snow',
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'header': 1 }, { 'header': 2 }],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'script': 'sub'}, { 'script': 'super' }],
                [{ 'indent': '-1'}, { 'indent': '+1' }],
                ['link', 'image'],
                ['clean']
            ]
        },
        placeholder: 'Add exercise instructions here...',
        readOnly: false
    };

    // Initialize editors if their elements exist
    const readingEditorEl = document.getElementById('readingEditor');
    const traditionalEditorEl = document.getElementById('traditionalEditor');

    if (readingEditorEl) {
        readingQuill = new Quill('#readingEditor', quillOptions);
    }
    if (traditionalEditorEl) {
        traditionalQuill = new Quill('#traditionalEditor', quillOptions);
    }
}

/**
 * Display a popup notification
 * @param {string} message - Message to display
 * @param {string} type - Type of popup (success, error, warning)
 */
function showToast(message, type = 'success') {
    // Create modal container if it doesn't exist
    let modalContainer = document.getElementById('notificationModal');
    if (!modalContainer) {
        modalContainer = document.createElement('div');
        modalContainer.id = 'notificationModal';
        modalContainer.className = 'modal fade';
        modalContainer.setAttribute('tabindex', '-1');
        modalContainer.setAttribute('aria-hidden', 'true');
        
        modalContainer.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi ${type === 'error' ? 'bi-exclamation-circle-fill text-danger' : 'bi-check-circle-fill text-success'}"></i>
                            ${type === 'error' ? 'Fehler' : 'Erfolg'}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Schließen"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-0">${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Schließen</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modalContainer);
    } else {
        // Update existing modal content
        const title = modalContainer.querySelector('.modal-title');
        const body = modalContainer.querySelector('.modal-body');
        const icon = modalContainer.querySelector('.modal-title i');
        
        if (title) title.innerHTML = `
            <i class="bi ${type === 'error' ? 'bi-exclamation-circle-fill text-danger' : 'bi-check-circle-fill text-success'}"></i>
            ${type === 'error' ? 'Fehler' : 'Erfolg'}
        `;
        if (body) body.innerHTML = `<p class="mb-0">${message}</p>`;
        if (icon) {
            icon.className = `bi ${type === 'error' ? 'bi-exclamation-circle-fill text-danger' : 'bi-check-circle-fill text-success'}`;
        }
    }

    // Show the modal
    const modal = new bootstrap.Modal(modalContainer);
    modal.show();

    // Auto-hide after 3 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            modal.hide();
        }, 3000);
    }
}

// ============================================================================
// Module Management Functions
// ============================================================================

/**
 * Load module data for editing.
 * @param {number} moduleId - ID of the module to load
 * @returns {Promise<void>}
 */
async function loadModuleData(moduleId) {
    try {
        console.log('Loading module data for ID:', moduleId);
        
        if (!moduleId) {
            console.error('No module ID provided');
            return;
        }
        
        currentModuleId = moduleId;
        
        const response = await fetch(`/course/manage/module/${moduleId}/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received module data:', data);
        
        if (data.success) {
            const module = data.module;
            
            // Show lesson editor section
            const lessonEditor = document.getElementById('lessonEditor');
            if (lessonEditor) {
                lessonEditor.classList.remove('d-none');
            }
            
            // Update lesson list
            const lessonList = document.getElementById('moduleLessonList');
            if (lessonList) {
                lessonList.innerHTML = ''; // Clear existing lessons
                
                if (module.lessons && module.lessons.length > 0) {
                    console.log('Rendering lessons:', module.lessons);
                    module.lessons.forEach(lesson => {
                        const lessonItem = createLessonListItem(lesson);
                        lessonList.appendChild(lessonItem);
                    });
                    
                    // Select first lesson
                    loadLessonContent(module.lessons[0].id);
                } else {
                    console.log('No lessons found');
                    showNoLessonSelected();
                }
            } else {
                console.error('Lesson list container not found');
            }
            
            // Update module title display
            updateModuleTitle(module.title);
            
            // Update quick edit form
            const titleInput = document.getElementById('editModuleTitle');
            const descInput = document.getElementById('editModuleDescription');
            const difficultySelect = document.getElementById('editModuleDifficultyLevel');
            
            if (titleInput) titleInput.value = module.title || '';
            if (descInput) descInput.value = module.description || '';
            if (difficultySelect) difficultySelect.value = module.difficulty_level || 1;
        } else {
            console.error('Failed to load module data:', data.error);
            showToast('Error loading module data', 'error');
        }
    } catch (error) {
        console.error('Error loading module data:', error);
        showToast('Error loading module data: ' + error.message, 'error');
    }
}

/**
 * Save module data to the server.
 * @returns {Promise<void>}
 */
async function saveModule() {
    const titleInput = document.getElementById('editModuleTitle');
    const descInput = document.getElementById('editModuleDescription');
    const difficultySelect = document.getElementById('editModuleDifficultyLevel');
    
    if (!titleInput) return;
    
    const container = document.querySelector('[data-course-id]');
    console.log('Container:', container);
    const courseId = container ? container.dataset.courseId : null;
    console.log('Course ID:', courseId);
    
    if (!courseId) {
        showToast('Fehler: Kurs-ID konnte nicht ermittelt werden', 'error');
        return;
    }
    
    const moduleData = {
        title: titleInput.value,
        description: descInput ? descInput.value : '',
        difficulty_level: difficultySelect ? difficultySelect.value : 1
    };
    
    console.log('Sending module data:', moduleData); // Debug log
    
    const url = currentModuleId ? 
        `/course/manage/module/${currentModuleId}/update/` : 
        `/course/manage/module/create/${courseId}/`;
    
    console.log('Request URL:', url);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(moduleData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Server error:', errorData); // Debug log
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Unknown error'}`);
        }

        const data = await response.json();
        console.log('Response data:', data); // Debug log

        if (data.success) {
            // showToast('Module saved successfully');
            if (!currentModuleId && data.module_id) {
                currentModuleId = data.module_id;
                window.location.reload();
            }
        } else {
            showToast(data.error || 'Error saving module', 'error');
        }
    } catch (error) {
        console.error('Error saving module:', error);
        showToast('Error saving module: ' + error.message, 'error');
    }
}

/**
 * Delete a module and all its lessons.
 * @param {number} moduleId - ID of the module to delete
 * @returns {Promise<void>}
 */
function deleteModule(moduleId) {
    if (!moduleId || !confirm('Sind Sie sicher, dass Sie dieses Modul und alle zugehörigen Lektionen löschen möchten?')) return;
    
    fetch(`/course/manage/module/${moduleId}/delete/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(async response => {
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const moduleEl = document.querySelector(`.module-card[data-module-id="${moduleId}"]`);
            if (moduleEl) {
                moduleEl.remove();
                // showToast('Module deleted successfully');
            }
        } else {
            showToast(data.error || 'Error deleting module', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting module:', error);
        showToast('Error deleting module: ' + error.message, 'error');
    });
}

/**
 * Update the order of modules in the course.
 * @returns {Promise<void>}
 */
function updateModuleOrder() {
    const moduleOrder = [];
    document.querySelectorAll('#sortableModules .module-card').forEach((el, index) => {
        moduleOrder.push({
            id: el.dataset.moduleId,
            order: index
        });
    });
    
    fetch('/course/manage/update_module_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ modules: moduleOrder })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            // Handle specific error cases
            if (response.status === 403) {
                showToast(data.error || 'Permission denied', 'error');
                // Reload the page to reset the order
                // window.location.reload();
                return;
            }
            throw new Error(data.error || 'Failed to update module order');
        }
        if (!data.success) {
            throw new Error(data.error || 'Failed to update module order');
        }
        // showToast('Module order updated successfully');
    })
    .catch(error => {
        console.error('Error updating module order:', error);
        showToast(error.message || 'Error updating module order', 'error');
        // Reload the page to reset the order
        // window.location.reload();
    });
}

/**
 * Create a new module in the course.
 * @returns {Promise<void>}
 */
async function createNewModule() {
    const container = document.querySelector('[data-course-id]');
    const courseId = container ? container.dataset.courseId : null;
    
    if (!courseId) {
        showToast('Error: Could not determine course ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/course/manage/module/create/${courseId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                title: 'New Module',
                description: '',
                difficulty_level: 1
            })
        });

        const data = await response.json();
        
        if (data.success) {
            // Create new module card
            const moduleCard = createModuleCard({
                id: data.module_id,
                title: 'New Module',
                description: '',
                difficulty_level: 1,
                lessons: { count: 0 }
            });
            
            // Add to modules container
            const modulesContainer = document.getElementById('sortableModules');
            if (modulesContainer) {
                // Remove "no modules" message if it exists
                const emptyMessage = modulesContainer.querySelector('.col-12.text-center');
                if (emptyMessage) {
                    emptyMessage.remove();
                }
                modulesContainer.appendChild(moduleCard);
            }
            
            // Open edit modal with the new module
            currentModuleId = data.module_id;
            loadModuleData(data.module_id);
            
            // Show success message
            // showToast('New module created successfully');
        } else {
            showToast(data.error || 'Error creating module', 'error');
        }
    } catch (error) {
        console.error('Error creating module:', error);
        showToast('Error creating module: ' + error.message, 'error');
    }
}

/**
 * Create a module card element.
 * @param {Object} module - Module data object
 * @param {number} module.id - Module ID
 * @param {string} module.title - Module title
 * @param {string} module.description - Module description
 * @param {Object} module.lessons - Module lessons data
 * @param {number} module.difficulty_level - Module difficulty level
 * @returns {HTMLElement} The created module card element
 */
function createModuleCard(module) {
    const div = document.createElement('div');
    div.className = 'col-md-6 col-lg-4 mb-4 module-card';
    div.dataset.moduleId = module.id;
    
    // Get difficulty level text
    const difficultyLabels = {
        1: 'Anfänger',
        2: 'Fortgeschritten',
        3: 'Experte',
        4: 'Profi',
        5: 'Demo'
    };
    const difficultyText = difficultyLabels[module.difficulty_level] || 'Anfänger';
    const difficultyClass = module.difficulty_level === 1 ? 'bg-success' : 
                           module.difficulty_level === 2 ? 'bg-primary' :
                           module.difficulty_level === 3 ? 'bg-warning' : 
                           module.difficulty_level === 4 ? 'bg-danger' : 'bg-secondary';
    
    div.innerHTML = `
        <div class="card h-100">
            <div class="card-body">
                <div class="d-flex align-items-center mb-3">
                    <div class="drag-handle me-2">
                        <i class="bi bi-grip-vertical"></i>
                    </div>
                    <h5 class="card-title mb-0">${module.title}</h5>
                </div>
                <p class="card-text text-muted">${module.description || 'Keine Beschreibung'}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <span class="badge bg-secondary me-1">${module.lessons.count} Lektionen</span>
                        <span class="badge ${difficultyClass}">${difficultyText}</span>
                    </div>
                    <div class="btn-group">
                        <button type="button" class="btn btn-sm btn-outline-primary edit-module" 
                                data-module-id="${module.id}" data-bs-toggle="modal" 
                                data-bs-target="#editModuleModal">
                            <i class="bi bi-pencil"></i> Bearbeiten
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-danger" 
                                onclick="deleteModule(${module.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return div;
}

// ============================================================================
// Lesson Management Functions
// ============================================================================

/**
 * Create a list item element for a lesson.
 * @param {Object} lesson - Lesson data object
 * @param {number} lesson.id - Lesson ID
 * @param {string} lesson.title - Lesson title
 * @param {string} lesson.lesson_type - Type of lesson
 * @returns {HTMLElement} The created lesson list item element
 */
function createLessonListItem(lesson) {
    const div = document.createElement('div');
    div.className = 'lesson-item d-flex align-items-center p-2 border-bottom';
    div.dataset.lessonId = lesson.id;
    
    div.innerHTML = `
        <div class="drag-handle me-2">
            <i class="bi bi-grip-vertical"></i>
        </div>
        <div class="flex-grow-1" onclick="loadLessonContent(${lesson.id})">
            <div class="lesson-title">${lesson.title}</div>
            <small class="text-muted">${lesson.lesson_type}</small>
        </div>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteLesson(${lesson.id})">
            <i class="bi bi-trash"></i>
        </button>
    `;
    
    return div;
}

/**
 * Load lesson content for editing.
 * @param {number} lessonId - ID of the lesson to load
 * @returns {Promise<void>}
 */
function loadLessonContent(lessonId) {
    if (!lessonId) return;
    
    console.log('Loading lesson content for ID:', lessonId);
    currentLessonId = lessonId;
    
    // Update active state in lesson list
    document.querySelectorAll('.lesson-item').forEach(item => item.classList.remove('active'));
    const activeItem = document.querySelector(`.lesson-item[data-lesson-id="${lessonId}"]`);
    if (activeItem) activeItem.classList.add('active');
    
    fetch(`/course/manage/lesson/${lessonId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const lesson = data.lesson;
                console.log('Received lesson data:', lesson);
                
                const titleInput = document.getElementById('lessonTitle');
                const typeSelect = document.getElementById('lessonType');
                const durationInput = document.getElementById('lessonDuration');
                
                if (titleInput) titleInput.value = lesson.title || '';
                if (typeSelect) typeSelect.value = lesson.lesson_type || 'reading';
                if (durationInput) durationInput.value = lesson.duration || 10;
                
                showLessonTypeContent(lesson.lesson_type);
                
                // Set content based on lesson type
                if (lesson.lesson_type === 'reading' && readingQuill) {
                    console.log('Setting reading content');
                    readingQuill.root.innerHTML = lesson.lesson_content || '';
                } else if (lesson.lesson_type === 'exercise') {
                    const exerciseTypeSelect = document.getElementById('exerciseType');
                    if (exerciseTypeSelect) {
                        exerciseTypeSelect.value = lesson.exercise_type || 'traditional';
                        showExerciseTypeContent(lesson.exercise_type || 'traditional');
                        
                        // Set maximum points and pass points if they exist
                        const maximumPointsInput = document.getElementById('maximumPoints');
                        const passPointsInput = document.getElementById('passPoints');
                        
                        if (maximumPointsInput && lesson.maximum_points !== undefined) {
                            maximumPointsInput.value = lesson.maximum_points;
                        }
                        
                        if (passPointsInput && lesson.pass_points !== undefined) {
                            passPointsInput.value = lesson.pass_points;
                        }
                        
                        if (traditionalQuill) {
                            console.log('Setting exercise content to traditionalQuill');
                            traditionalQuill.root.innerHTML = lesson.lesson_content || '';
                        }
                        
                        // Handle Jupyter specific files
                        if (lesson.exercise_type === 'jupyter') {
                            console.log('Setting up Jupyter files:', lesson); // Debug log
                            const currentJupyterFile = document.getElementById('currentJupyterFile');
                            const currentMaterials = document.getElementById('currentMaterials');
                            const materialsList = document.getElementById('materialsList');

                            // Clear file inputs
                            const jupyterFileInput = document.getElementById('jupyterFile');
                            const materialsInput = document.getElementById('materialFiles');
                            if (jupyterFileInput) jupyterFileInput.value = '';
                            if (materialsInput) materialsInput.value = '';

                            // Display current Jupyter file
                            if (currentJupyterFile) {
                                if (lesson.jupyter_file) {
                                    currentJupyterFile.classList.remove('d-none');
                                    const fileNameSpan = currentJupyterFile.querySelector('.current-file-name');
                                    const fileName = lesson.jupyter_file.split('/').pop();
                                    if (fileNameSpan) {
                                        const fileLink = fileNameSpan.querySelector('a');
                                        if (fileLink) {
                                            fileLink.href = lesson.jupyter_file;
                                            fileLink.textContent = fileName;
                                        }
                                    }
                                } else {
                                    currentJupyterFile.classList.add('d-none');
                                }
                            } else if (currentJupyterFile) {
                                currentJupyterFile.classList.add('d-none');
                            }

                            // Display materials if they exist
                            if (currentMaterials && materialsList && lesson.materials && lesson.materials.length > 0) {
                                currentMaterials.classList.remove('d-none');
                                materialsList.innerHTML = lesson.materials.map(material => `
                                    <li class="d-flex align-items-center mb-1" id="material-${material.id}">
                                        <i class="bi bi-file-earmark me-2"></i>
                                        <span class="text-truncate">
                                            <a href="${material.file_url}" class="text-decoration-none text-dark" download>
                                                ${material.file_name.split('/').pop()}
                                            </a>
                                        </span>
                                        <div class="ms-2">
                                            <button type="button" class="btn btn-link text-danger p-0 ms-2" 
                                                    onclick="deleteMaterial(${material.id}, ${lesson.id})">
                                                <i class="bi bi-x-circle"></i>
                                            </button>
                                        </div>
                                    </li>
                                `).join('');
                            } else if (currentMaterials) {
                                currentMaterials.classList.add('d-none');
                                if (materialsList) materialsList.innerHTML = '';
                            }
                        }
                    }
                } else if (lesson.lesson_type === 'video' && lesson.video_file) {
                    const videoPreview = document.getElementById('videoPreview');
                    if (videoPreview) {
                        videoPreview.src = lesson.video_file;
                        videoPreview.parentElement.classList.remove('d-none');
                    }
                }
                
                const editorEl = document.getElementById('lessonEditor');
                const noLessonEl = document.getElementById('noLessonSelected');
                
                if (editorEl) editorEl.classList.remove('d-none');
                if (noLessonEl) noLessonEl.classList.add('d-none');
            }
        })
        .catch(error => {
            console.error('Error loading lesson:', error);
            showToast('Error loading lesson data', 'error');
        });
}

/**
 * Show content section for selected lesson type.
 * @param {string} type - Type of lesson (reading/video/exercise)
 */
function showLessonTypeContent(type) {
    document.querySelectorAll('.lesson-type-content').forEach(el => el.classList.add('d-none'));
    const contentEl = document.getElementById(`${type}Content`);
    if (contentEl) contentEl.classList.remove('d-none');
    
    if (type === 'exercise') {
        const exerciseTypeSelect = document.getElementById('exerciseType');
        if (exerciseTypeSelect) {
            showExerciseTypeContent(exerciseTypeSelect.value);
        }
    }
}

/**
 * Show content section for selected exercise type.
 * @param {string} type - Type of exercise (traditional/jupyter)
 */
function showExerciseTypeContent(type) {
    document.querySelectorAll('.exercise-type-content').forEach(el => el.classList.add('d-none'));
    const exerciseEl = document.getElementById(`${type}Exercise`);
    
    if (exerciseEl) {
        exerciseEl.classList.remove('d-none');
    }
}

/**
 * Create a new lesson in the current module.
 * @returns {Promise<void>}
 */
function createNewLesson() {
    if (!currentModuleId) {
        showToast('Please save the module first', 'error');
        return;
    }
    
    fetch(`/course/manage/create_lesson/${currentModuleId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const lesson = {
                id: data.lesson_id,
                title: data.lesson_title,
                lesson_type: data.lesson_type
            };
            const lessonList = document.getElementById('moduleLessonList');
            if (lessonList) {
                lessonList.appendChild(createLessonListItem(lesson));
                loadLessonContent(lesson.id);
                // showToast('New lesson created');
            }
        }
    })
    .catch(error => {
        console.error('Error creating lesson:', error);
        showToast('Error creating lesson', 'error');
    });
}

// ============================================================================
// Exercise Management Functions
// ============================================================================

/**
 * Save the current lesson with all its content.
 * @returns {Promise<void>}
 */
function saveLesson() {
    if (!currentLessonId) return;
    
    // Validate all inputs first
    if (!validateFiles()) {
        return; // Don't proceed if validation fails
    }
    
    // Update save button state
    const saveButton = document.querySelector('button[onclick="saveLesson()"]');
    const originalButtonText = saveButton.innerHTML;
    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Speichern...';
    saveButton.disabled = true;

    const formData = new FormData();
    const titleInput = document.getElementById('lessonTitle');
    const typeSelect = document.getElementById('lessonType');
    const durationInput = document.getElementById('lessonDuration');
    
    if (titleInput) formData.append('title', titleInput.value);
    if (typeSelect) formData.append('lesson_type', typeSelect.value);
    if (durationInput) formData.append('duration', durationInput.value);
    
    const lessonType = typeSelect ? typeSelect.value : 'reading';
    console.log('Saving lesson type:', lessonType);
    
    // Get content from the appropriate editor
    if (lessonType === 'reading' && readingQuill) {
        formData.append('content', readingQuill.root.innerHTML);
    } else if (lessonType === 'exercise') {
        const exerciseType = document.getElementById('exerciseType').value;
        formData.append('exercise_type', exerciseType);
        
        // Add maximum points and pass points
        const maximumPoints = document.getElementById('maximumPoints').value;
        const passPoints = document.getElementById('passPoints').value;
        formData.append('maximum_points', maximumPoints);
        formData.append('pass_points', passPoints);
        
        // Use traditionalQuill for all exercise types
        if (traditionalQuill) {
            console.log('Getting exercise content from traditionalQuill');
            formData.append('content', traditionalQuill.root.innerHTML);
        }
        
        // Handle Jupyter specific files
        if (exerciseType === 'jupyter') {
            const jupyterFile = document.getElementById('jupyterFile');
            const materialFiles = document.getElementById('materialFiles');
            
            if (jupyterFile && jupyterFile.files[0]) {
                console.log('Adding Jupyter file:', jupyterFile.files[0].name);
                formData.append('jupyter_file', jupyterFile.files[0]);
            }
            
            if (materialFiles && materialFiles.files.length > 0) {
                console.log('Adding materials:', materialFiles.files.length, 'files');
                // Log each material file being added
                Array.from(materialFiles.files).forEach((file, index) => {
                    console.log(`Adding material file ${index + 1}:`, {
                        name: file.name,
                        size: file.size,
                        type: file.type
                    });
                    formData.append('materials', file);
                });

                // Debug log FormData contents
                console.log('FormData entries:');
                for (let [key, value] of formData.entries()) {
                    if (value instanceof File) {
                        console.log('FormData entry:', key, {
                            name: value.name,
                            size: value.size,
                            type: value.type
                        });
                    } else {
                        console.log('FormData entry:', key, value);
                    }
                }
            }
        }
    } else if (lessonType === 'video') {
        // Handle video file upload
        const videoFile = document.getElementById('videoFile');
        if (videoFile && videoFile.files[0]) {
            console.log('Adding video file:', videoFile.files[0].name);
            formData.append('video_file', videoFile.files[0]);
        }
    }
    
    // Log form data for debugging
    console.log('Sending request to:', `/course/manage/save_lesson/${currentLessonId}/`);
    
    fetch(`/course/manage/save_lesson/${currentLessonId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            showToast('Lesson saved successfully');
            
            // Use loadLessonContent to refresh the page content
            loadLessonContent(currentLessonId);
            
            // Update lesson title in list if changed
            const titleEl = document.querySelector(`.lesson-item[data-lesson-id="${currentLessonId}"] .lesson-title`);
            if (titleEl && titleInput) titleEl.textContent = titleInput.value;
        } else {
            showToast(data.error || 'Error saving lesson', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving lesson:', error);
        showToast('Error saving lesson: ' + error.message, 'error');
    })
    .finally(() => {
        // Reset save button state
        saveButton.innerHTML = originalButtonText;
        saveButton.disabled = false;
    });
}

/**
 * Delete a lesson from the current module.
 * @param {number} lessonId - ID of the lesson to delete
 * @returns {Promise<void>}
 */
function deleteLesson(lessonId) {
    if (!lessonId || !confirm('Sind Sie sicher, dass Sie diese Lektion löschen möchten?')) return;
    
    fetch(`/course/manage/delete_lesson/${lessonId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const lessonEl = document.querySelector(`.lesson-item[data-lesson-id="${lessonId}"]`);
            if (lessonEl) lessonEl.remove();
            
            if (currentLessonId === lessonId) {
                showNoLessonSelected();
            }
            // showToast('Lesson deleted successfully');
        }
    })
    .catch(error => {
        console.error('Error deleting lesson:', error);
        showToast('Error deleting lesson', 'error');
    });
}

// ============================================================================
// Event Handlers and Initialization
// ============================================================================

/**
 * Initialize the page when the DOM is fully loaded.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeQuillEditors();
    initializeEventListeners();
    initializeSortable();
    initializeCollapseHandlers();

    // Disable editing if course is published
    if (window.courseIsPublished) {
        // Disable add module button
        const addModuleBtn = document.querySelector('[data-bs-target="#editModuleModal"]');
        if (addModuleBtn) {
            addModuleBtn.disabled = true;
            addModuleBtn.style.pointerEvents = 'none';
            addModuleBtn.style.opacity = 0.5;
        }
        // Disable all edit/delete buttons
        document.querySelectorAll('.edit-module, .btn-outline-danger').forEach(btn => {
            btn.disabled = true;
            btn.style.pointerEvents = 'none';
            btn.style.opacity = 0.5;
        });
        // Hide drag handles
        document.querySelectorAll('.drag-handle').forEach(handle => {
            handle.style.display = 'none';
        });
        // Prevent drag-and-drop
        if (window.Sortable && document.getElementById('sortableModules')) {
            const sortable = window.Sortable.get(document.getElementById('sortableModules'));
            if (sortable) sortable.option('disabled', true);
        }
    }
    // For debugging
    console.log('Remove file event listener registered');
});

/**
 * Initialize collapse handlers for module info section.
 */
function initializeCollapseHandlers() {
    const moduleInfoCollapse = document.getElementById('moduleInfoCollapse');
    if (moduleInfoCollapse) {
        moduleInfoCollapse.addEventListener('show.bs.collapse', function() {
            const header = this.previousElementSibling;
            const icon = header.querySelector('.transition-icon');
            if (icon) {
                icon.style.transform = 'rotate(0deg)';
            }
        });

        moduleInfoCollapse.addEventListener('hide.bs.collapse', function() {
            const header = this.previousElementSibling;
            const icon = header.querySelector('.transition-icon');
            if (icon) {
                icon.style.transform = 'rotate(180deg)';
            }
        });

        // Make the entire header clickable
        const sectionHeader = document.querySelector('.section-header');
        if (sectionHeader) {
            sectionHeader.addEventListener('click', function(e) {
                // Prevent click event from reaching the collapse toggle
                e.stopPropagation();
                const collapseElement = document.getElementById('moduleInfoCollapse');
                const bsCollapse = new bootstrap.Collapse(collapseElement, {
                    toggle: true
                });
            });
        }
    }

    // Add handler for Add Module button
    const addModuleBtn = document.querySelector('[data-bs-target="#editModuleModal"]');
    if (addModuleBtn) {
        addModuleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            createNewModule();
        });
    }
}

/**
 * Initialize sortable for lessons.
 */
function initializeSortable() {
    const lessonList = document.getElementById('moduleLessonList');
    const moduleList = document.getElementById('sortableModules');
    
    if (lessonList) {
        new Sortable(lessonList, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: updateLessonOrder
        });
    }
    
    if (moduleList) {
        new Sortable(moduleList, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: updateModuleOrder
        });
    }
}

/**
 * Initialize event listeners.
 */
function initializeEventListeners() {
    // Lesson type change handler
    const lessonTypeSelect = document.getElementById('lessonType');
    lessonTypeSelect?.addEventListener('change', () => showLessonTypeContent(lessonTypeSelect.value));
    
    // Exercise type change handler
    const exerciseTypeSelect = document.getElementById('exerciseType');
    exerciseTypeSelect?.addEventListener('change', () => {
        const selectedType = exerciseTypeSelect.value;
        showExerciseTypeContent(selectedType);
    });
    
    // Points fields event handlers
    const maximumPointsInput = document.getElementById('maximumPoints');
    const passPointsInput = document.getElementById('passPoints');
    
    // Handle change events
    maximumPointsInput?.addEventListener('change', () => {
        // Ensure maximum points is at least equal to pass points
        if (passPointsInput && parseInt(maximumPointsInput.value) < parseInt(passPointsInput.value)) {
            passPointsInput.value = maximumPointsInput.value;
        }
    });
    
    passPointsInput?.addEventListener('change', () => {
        // Ensure pass points doesn't exceed maximum points
        if (maximumPointsInput && parseInt(passPointsInput.value) > parseInt(maximumPointsInput.value)) {
            passPointsInput.value = maximumPointsInput.value;
        }
    });
    
    // Also handle input events for real-time validation
    maximumPointsInput?.addEventListener('input', () => {
        if (maximumPointsInput.value && parseInt(maximumPointsInput.value) < 1) {
            maximumPointsInput.value = 1;
        }
    });
    
    passPointsInput?.addEventListener('input', () => {
        if (passPointsInput.value && parseInt(passPointsInput.value) < 0) {
            passPointsInput.value = 0;
        }
        
        if (maximumPointsInput && passPointsInput.value && 
            parseInt(passPointsInput.value) > parseInt(maximumPointsInput.value)) {
            passPointsInput.value = maximumPointsInput.value;
        }
    });
    
    // Video file upload handler
    const videoFile = document.getElementById('videoFile');
    videoFile?.addEventListener('change', handleVideoFileUpload);
    
    // Add lesson button handler
    document.getElementById('addLessonBtn')?.addEventListener('click', createNewLesson);
    
    // Modal reset handler
    document.getElementById('editModuleModal')?.addEventListener('hidden.bs.modal', resetModalState);
    
    // File validation handlers
    const jupyterFile = document.getElementById('jupyterFile');
    const materialFiles = document.getElementById('materialFiles');
    jupyterFile?.addEventListener('change', validateFiles);
    materialFiles?.addEventListener('change', validateFiles);

    // Add modal show event handler
    const editModuleModal = document.getElementById('editModuleModal');
    if (editModuleModal) {
        editModuleModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            if (button && button.dataset.moduleId) {
                currentModuleId = button.dataset.moduleId;
                loadModuleData(currentModuleId);
            } else {
                // Handle new module case
                resetModalState();
            }
        });
    }
}

/**
 * Update the updateLessonOrder function to handle the case when spinner functions aren't needed
 */
function updateLessonOrder() {
    const lessonList = document.getElementById('moduleLessonList');
    const lessons = Array.from(lessonList.children);
    const moduleId = currentModuleId;
    
    const orderData = lessons.map((lesson, index) => ({
        lesson_id: lesson.dataset.lessonId,
        order: index
    }));

    fetch(`/course/api/modules/${moduleId}/lessons/reorder/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ lessons: orderData })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update lesson order');
        }
        return response.json();
    })
    .then(data => {
        // showToast('Lesson order updated successfully');
    })
    .catch(error => {
        console.error('Error updating lesson order:', error);
        showToast('Failed to update lesson order', 'error');
    });
}

/**
 * Show the no lesson selected state.
 */
function showNoLessonSelected() {
    currentLessonId = null;
    const editorEl = document.getElementById('lessonEditor');
    const noLessonEl = document.getElementById('noLessonSelected');
    
    if (editorEl) editorEl.classList.add('d-none');
    if (noLessonEl) noLessonEl.classList.remove('d-none');
}

/**
 * Cancel lesson editing and reset to current state.
 */
function cancelLessonEdit() {
    if (currentLessonId) {
        loadLessonContent(currentLessonId);
    } else {
        showNoLessonSelected();
    }
}

/**
 * Update the module title display.
 * @param {string} title - New title to display
 */
function updateModuleTitle(title) {
    const displayTitle = document.getElementById('displayModuleTitle');
    if (displayTitle) {
        displayTitle.textContent = title || 'New Module';
    }
}

/**
 * Quick save module information.
 * @returns {Promise<void>}
 */
async function saveModuleQuick() {
    const titleInput = document.getElementById('editModuleTitle');
    const descInput = document.getElementById('editModuleDescription');
    const difficultySelect = document.getElementById('editModuleDifficultyLevel');
    
    if (!titleInput) return;
    
    const moduleData = {
        title: titleInput.value,
        description: descInput ? descInput.value : '',
        difficulty_level: difficultySelect ? difficultySelect.value : 1
    };
    
    try {
        const url = currentModuleId ? 
            `/course/manage/module/${currentModuleId}/update/` : 
            `/course/manage/module/create/${courseId}/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(moduleData)
        });

        const data = await response.json();
        
        if (data.success) {
            updateModuleTitle(moduleData.title);
            // showToast('Module saved successfully');
            
            // Collapse the quick edit form
            const quickEdit = document.getElementById('moduleQuickEdit');
            if (quickEdit) {
                bootstrap.Collapse.getInstance(quickEdit).hide();
            }
            
            if (!currentModuleId && data.module_id) {
                currentModuleId = data.module_id;
            }
        } else {
            showToast(data.error || 'Error saving module', 'error');
        }
    } catch (error) {
        console.error('Error saving module:', error);
        showToast('Error saving module: ' + error.message, 'error');
    }
}

/**
 * Cancel module quick edit and reset form.
 */
function cancelModuleQuickEdit() {
    const titleInput = document.getElementById('editModuleTitle');
    const descInput = document.getElementById('editModuleDescription');
    const difficultySelect = document.getElementById('editModuleDifficultyLevel');
    
    // Reset inputs to current values
    if (currentModuleId) {
        fetch(`/course/manage/module/${currentModuleId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (titleInput) titleInput.value = data.module.title || '';
                    if (descInput) descInput.value = data.module.description || '';
                    if (difficultySelect) difficultySelect.value = data.module.difficulty_level || 1;
                }
            })
            .catch(error => console.error('Error resetting module info:', error));
    } else {
        // For new modules, clear the inputs
        if (titleInput) titleInput.value = '';
        if (descInput) descInput.value = '';
        if (difficultySelect) difficultySelect.value = 1;
    }
    
    // Collapse the quick edit form
    const quickEdit = document.getElementById('moduleQuickEdit');
    if (quickEdit) {
        bootstrap.Collapse.getInstance(quickEdit).hide();
    }
}

/**
 * Reset modal state when closing.
 */
function resetModalState() {
    currentModuleId = null;
    currentLessonId = null;
    
    // Reset title display and form
    updateModuleTitle('');
    const titleInput = document.getElementById('editModuleTitle');
    const descInput = document.getElementById('editModuleDescription');
    if (titleInput) titleInput.value = '';
    if (descInput) descInput.value = '';
    
    // Collapse quick edit if open
    const quickEdit = document.getElementById('moduleQuickEdit');
    if (quickEdit && bootstrap.Collapse.getInstance(quickEdit)) {
        bootstrap.Collapse.getInstance(quickEdit).hide();
    }
    
    const lessonList = document.getElementById('moduleLessonList');
    if (lessonList) lessonList.innerHTML = '';
    
    showNoLessonSelected();
}

/**
 * Add a function to validate file types
 */
function validateFiles() {
    const jupyterFile = document.getElementById('jupyterFile');
    const materialFiles = document.getElementById('materialFiles');
    let isValid = true;
    
    // Validate points for exercises
    const lessonType = document.getElementById('lessonType')?.value;
    if (lessonType === 'exercise') {
        const maximumPointsInput = document.getElementById('maximumPoints');
        const passPointsInput = document.getElementById('passPoints');
        
        if (maximumPointsInput && passPointsInput) {
            const maxPoints = parseInt(maximumPointsInput.value);
            const passPoints = parseInt(passPointsInput.value);
            
            if (maxPoints < 1) {
                showToast('Maximale Punkte müssen mindestens 1 sein', 'error');
                maximumPointsInput.value = 1;
                isValid = false;
            }
            
            if (passPoints < 0) {
                showToast('Mindestpunktzahl darf nicht negativ sein', 'error');
                passPointsInput.value = 0;
                isValid = false;
            }
            
            if (passPoints > maxPoints) {
                showToast('Mindestpunktzahl darf nicht größer als maximale Punkte sein', 'error');
                passPointsInput.value = maxPoints;
                isValid = false;
            }
        }
    }
    
    if (jupyterFile && jupyterFile.files[0]) {
        const file = jupyterFile.files[0];
        if (!file.name.endsWith('.ipynb')) {
            showToast('Bitte wählen Sie eine gültige Jupyter Notebook-Datei (.ipynb)', 'error');
            jupyterFile.value = '';
            isValid = false;
        }
    }
    
    if (materialFiles && materialFiles.files.length > 0) {
        const allowedExtensions = ['.py', '.csv', '.json', '.txt', '.dat', '.npy', '.h5', '.pkl'];
        Array.from(materialFiles.files).forEach(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(ext)) {
                showToast(`Dateityp nicht erlaubt: ${file.name}`, 'error');
                materialFiles.value = '';
                isValid = false;
            }
        });
    }
    
    //const videoFile = document.getElementById('videoFile');
    //if (videoFile && videoFile.files[0]) {
    //    const file = videoFile.files[0];
    //    if (!file.type.startsWith('media/')) {
    //        showToast('Bitte wählen Sie eine gültige Videodatei aus (mp4, mov, avi, wmv, mpeg, mp3, m4a, wav, ogg, webm)', 'error');
    //        videoFile.value = '';
    //        isValid = false;
    //    }
    //}
    
    return isValid;
}

/**
 * Delete Jupyter notebook file from an exercise
 * @param {number} lessonId - ID of the lesson containing the exercise
 * @returns {Promise<void>}
 */
async function deleteJupyterFile(lessonId) {
    if (!confirm('Sind Sie sicher, dass Sie diese Datei löschen möchten?')) {
        return;
    }

    try {
        const response = await fetch(`/course/lesson/${lessonId}/delete-jupyter-file/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete file');
        }

        if (data.success) {
            // Update UI to reflect deleted file
            const fileInfo = document.querySelector('#currentJupyterFile');
            if (fileInfo) {
                fileInfo.querySelector('.current-file-name a').textContent = '';
                fileInfo.classList.add('d-none');
            }
            showToast('File deleted successfully');
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showToast(error.message, 'error');
    }
}

/**
 * Handle video file upload.
 * @param {Event} event - The event object
 */
function handleVideoFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const url = URL.createObjectURL(file);
        const preview = document.getElementById('videoPreview');
        if (preview) {
            preview.src = url;
            preview.parentElement.classList.remove('d-none');
        }
    }
}

/**
 * Delete material from an exercise
 * @param {number} materialId - ID of the material to delete
 * @param {number} lessonId - ID of the lesson containing the material
 * @returns {Promise<void>}
 */
async function deleteMaterial(materialId, lessonId) {
    if (!confirm('Sind Sie sicher, dass Sie dieses Material löschen möchten?')) {
        return;
    }

    try {
        const response = await fetch(`/course/lesson/${lessonId}/delete-material/${materialId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete material');
        }

        if (data.success) {
            // Remove the material item from the list
            const materialItem = document.querySelector(`#material-${materialId}`);
            if (materialItem) {
                materialItem.remove();
            }
            
            // Hide the materials section if no materials left
            const materialsList = document.getElementById('materialsList');
            if (materialsList && materialsList.children.length === 0) {
                document.getElementById('currentMaterials').classList.add('d-none');
            }
            
            showToast('Material deleted successfully');
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error deleting material:', error);
        showToast(error.message, 'error');
    }
}

// Add event listener for delete button
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('.jupyter-remove-file')?.addEventListener('click', function(e) {
        e.preventDefault();
        const lessonId = currentLessonId;
        if (lessonId) {
            deleteJupyterFile(lessonId);
        } else {
            console.error('No lesson ID found');
            showToast('Error: Could not determine lesson ID', 'error');
        }
    });
}); 