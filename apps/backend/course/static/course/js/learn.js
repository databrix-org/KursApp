document.addEventListener('DOMContentLoaded', function() {
    // Set progress bar width
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const progress = progressFill.getAttribute('data-progress');
        progressFill.style.width = `${progress}%`;
    }
    
    // Get modules data from the template
    const debugDataElement = document.getElementById('debug-data');
    if (!debugDataElement) {
        console.error('Debug data element not found');
        return;
    }
    
    const modulesDataJson = debugDataElement.value;
    
    // Check if the JSON data is valid
    if (!modulesDataJson || modulesDataJson.trim() === '') {
        console.error('Empty JSON data');
        return;
    }
    
    // Log the first few characters for debugging
    console.log('JSON data starts with:', modulesDataJson.substring(0, 50));
    
    // Try to parse the JSON with error handling
    let modulesData;
    try {
        modulesData = JSON.parse(modulesDataJson);
    } catch (error) {
        console.error('JSON parse error:', error);
        console.error('JSON data:', modulesDataJson);
        return;
    }
    
    // Check if modules data has expected structure
    if (!modulesData || !modulesData.modules) {
        console.error('Invalid modules data structure:', modulesData);
        return;
    }
    
    // Function to format ISO 8601 duration string to readable format
    function formatDuration(isoDuration) {
        if (!isoDuration) return '';
        
        // Parse ISO 8601 duration string
        const matches = isoDuration.match(/P(\d+D)?T(\d+H)?(\d+M)?(\d+S)?/);
        if (!matches) return isoDuration;
        
        const days = matches[1] ? parseInt(matches[1].replace('D', '')) : 0;
        const hours = matches[2] ? parseInt(matches[2].replace('H', '')) : 0;
        const minutes = matches[3] ? parseInt(matches[3].replace('M', '')) : 0;
        const seconds = matches[4] ? parseInt(matches[4].replace('S', '')) : 0;
        
        // Format the duration based on its components
        let formattedDuration = '';
        
        if (days > 0) {
            formattedDuration += days + (days === 1 ? ' Tag' : ' Tage');
        }
        
        if (hours > 0) {
            if (formattedDuration) formattedDuration += ' ';
            formattedDuration += hours + (hours === 1 ? ' Std' : ' Std');
        }
        
        if (minutes > 0 || (!days && !hours && !seconds)) {
            if (formattedDuration) formattedDuration += ' ';
            formattedDuration += minutes + (minutes === 1 ? ' Min' : ' Min');
        }
        
        if (seconds > 0 && !days && !hours) {
            if (formattedDuration) formattedDuration += ' ';
            formattedDuration += seconds + (seconds === 1 ? ' Sek' : ' Sek');
        }
        
        return formattedDuration;
    }
    
    // Calculate and display module statistics (duration and completion)
    function updateModuleStatistics() {
        console.log("Module data:", modulesData);
        
        modulesData.modules.forEach((moduleData, index) => {
            console.log(`Processing module ${index}: ${moduleData.title}`);
            
            // Calculate total duration for the module
            let totalDurationMinutes = 0;
            let totalLessons = moduleData.lessons.length;
            let completedLessons = 0;
            let totalExercises = 0;
            let completedExercises = 0;
            
            console.log(`Module ${index} has ${totalLessons} lessons`);
            
            moduleData.lessons.forEach((lesson, lessonIndex) => {
                console.log(`Processing lesson ${lessonIndex}: ${lesson.title}`);
                console.log(`Lesson duration:`, lesson.duration, typeof lesson.duration);
                console.log(`Lesson debug_minutes:`, lesson.debug_minutes);
                console.log(`Lesson type:`, lesson.lesson_type);
                
                // Count exercise lessons
                if (lesson.lesson_type === 'exercise') {
                    totalExercises++;
                    if (lesson.is_completed) {
                        completedExercises++;
                    }
                }
                
                // Add to total duration - use debug_minutes when available
                if (lesson.debug_minutes !== undefined) {
                    // Use the debug_minutes field directly
                    totalDurationMinutes += lesson.debug_minutes;
                    console.log(`Using debug_minutes: ${lesson.debug_minutes} minutes`);
                }
                // Fallback to parsing the duration string
                else if (lesson.duration) {
                    try {
                        // For debugging - output raw duration value
                        let durationParsed = false;
                        
                        // Format like PT30M (30 minutes)
                        const minutesMatch = lesson.duration.match(/PT(\d+)M/);
                        if (minutesMatch && minutesMatch[1]) {
                            const minutes = parseInt(minutesMatch[1]);
                            totalDurationMinutes += minutes;
                            console.log(`Parsed ${lesson.duration} as ${minutes} minutes (simple format)`);
                            durationParsed = true;
                        } 
                        // Format like PT1H30M (1 hour 30 minutes)
                        else {
                            // Full ISO 8601 format handling
                            const fullMatch = lesson.duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
                            if (fullMatch) {
                                const hours = fullMatch[1] ? parseInt(fullMatch[1]) : 0;
                                const minutes = fullMatch[2] ? parseInt(fullMatch[2]) : 0;
                                const seconds = fullMatch[3] ? parseInt(fullMatch[3]) : 0;
                                
                                const totalMinutes = (hours * 60) + minutes + Math.ceil(seconds / 60);
                                totalDurationMinutes += totalMinutes;
                                console.log(`Parsed ${lesson.duration} as ${totalMinutes} minutes (complex format): ${hours}h ${minutes}m ${seconds}s`);
                                durationParsed = true;
                            }
                            // If it's a string representing seconds (fallback)
                            else if (!isNaN(lesson.duration)) {
                                const minutes = Math.ceil(parseInt(lesson.duration) / 60);
                                totalDurationMinutes += minutes;
                                console.log(`Parsed ${lesson.duration} as ${minutes} minutes (seconds format)`);
                                durationParsed = true;
                            }
                        }
                        
                        if (!durationParsed) {
                            console.warn(`Could not parse duration format: ${lesson.duration}`);
                        }
                    } catch (e) {
                        console.error("Error parsing duration:", e, lesson.duration);
                    }
                } else {
                    console.log("No duration value found for this lesson");
                }
                
                // Count completed lessons
                if (lesson.is_completed) {
                    completedLessons++;
                }
            });
            
            console.log(`Module ${index} total duration: ${totalDurationMinutes} minutes`);
            
            // Format the total duration
            let formattedTotalDuration = '';
            const hours = Math.floor(totalDurationMinutes / 60);
            const minutes = totalDurationMinutes % 60;
            
            if (totalDurationMinutes === 0) {
                // If no duration calculated, show at least 10 minutes as fallback
                formattedTotalDuration = '10 Min';
            } else {
                if (hours > 0) {
                    formattedTotalDuration += hours + (hours === 1 ? ' Std' : ' Std');
                }
                
                if (minutes > 0 || (!hours)) {
                    if (formattedTotalDuration) formattedTotalDuration += ' ';
                    formattedTotalDuration += minutes + (minutes === 1 ? ' Min' : ' Min');
                }
            }
            
            console.log(`Module ${index} formatted duration: ${formattedTotalDuration}`);
            
            // Calculate completion percentage
            const completionPercentage = totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;
            
            // Update the module card with duration and completion status
            const durationElement = document.querySelector(`.module-duration[data-module-index="${index}"]`);
            if (durationElement) {
                // Force set duration for testing if still 0
                if (totalDurationMinutes === 0) {
                    // For testing: Each module gets 15 minutes times its index + 15 base minutes
                    const testDuration = 15 + (index * 15);
                    const testHours = Math.floor(testDuration / 60);
                    const testMinutes = testDuration % 60;
                    
                    let testFormattedDuration = '';
                    if (testHours > 0) {
                        testFormattedDuration += testHours + (testHours === 1 ? ' Std' : ' Std');
                    }
                    
                    if (testMinutes > 0 || (!testHours)) {
                        if (testFormattedDuration) testFormattedDuration += ' ';
                        testFormattedDuration += testMinutes + (testMinutes === 1 ? ' Min' : ' Min');
                    }
                    
                    durationElement.innerHTML = `<i class="far fa-clock"></i> ${testFormattedDuration}`;
                    console.log(`Using test duration for module ${index}: ${testFormattedDuration}`);
                } else {
                    durationElement.innerHTML = `<i class="far fa-clock"></i> ${formattedTotalDuration}`;
                }
                console.log(`Updated duration element for module ${index}`);
            } else {
                console.warn(`Duration element not found for module ${index}`);
            }
            

            
            const completionElement = document.querySelector(`.module-completion-status[data-module-index="${index}"]`);
            if (completionElement) {
                // Add CSS class based on completion percentage
                if (completionPercentage === 100) {
                    completionElement.className = 'module-completion-status complete';
                } else if (completionPercentage > 0) {
                    completionElement.className = 'module-completion-status in-progress';
                } else {
                    completionElement.className = 'module-completion-status not-started';
                }
                
                // Base completion status text
                let completionText = `${completedLessons} von ${totalLessons} Lektionen erledigt (${completionPercentage}%)`;
                
                // Add exercise stats if there are any exercises
                if (totalExercises > 0) {
                    const exerciseCompletionPercentage = Math.round((completedExercises / totalExercises) * 100);
                    completionText += `<br><span class="exercise-completion">Übungen: ${completedExercises} von ${totalExercises} erledigt (${exerciseCompletionPercentage}%)</span>`;
                }
                
                completionElement.innerHTML = completionText;
            }
        });
    }
    
    // Call the function to update module statistics
    updateModuleStatistics();
    
    // Modal elements
    const modal = document.getElementById('lessonsModal');
    if (!modal) {
        console.error('Lessons modal element not found');
        return;
    }
    
    const modalTitle = document.getElementById('modalModuleTitle');
    const modalLessonsList = document.getElementById('modalLessonsList');
    const closeBtn = document.querySelector('.modal-close');
    
    if (!modalTitle || !modalLessonsList || !closeBtn) {
        console.error('One or more modal elements not found');
        return;
    }
    
    // Module card click handler
    const moduleCards = document.querySelectorAll('.module-card');
    moduleCards.forEach(card => {
        card.addEventListener('click', function() {
            const moduleIndex = parseInt(this.getAttribute('data-module-index'));
            const moduleData = modulesData.modules[moduleIndex];
            
            // Set modal title with difficulty badge
            modalTitle.textContent = moduleData.title;
            
            // Add difficulty level badge to modal title
            if (moduleData.difficulty_level) {
                // Get difficulty level text and class
                const difficultyLabels = {
                    1: 'Anfänger',
                    2: 'Fortgeschritten',
                    3: 'Experte',
                    4: 'Profi',
                    5: 'Demo'
                };
                const difficultyClass = moduleData.difficulty_level === 1 ? 'bg-success' : 
                                       moduleData.difficulty_level === 2 ? 'bg-primary' :
                                       moduleData.difficulty_level === 3 ? 'bg-warning' : 
                                       moduleData.difficulty_level === 4 ? 'bg-danger' : 
                                       moduleData.difficulty_level === 5 ? 'bg-secondary' : 'bg-secondary';
                
                // Create badge element
                const difficultyBadge = document.createElement('span');
                difficultyBadge.className = `badge ${difficultyClass} ms-2`;
                difficultyBadge.textContent = difficultyLabels[moduleData.difficulty_level] || 'Anfänger';
                
                // Append badge to title
                modalTitle.appendChild(difficultyBadge);
            }
            
            // Clear existing lessons
            modalLessonsList.innerHTML = '';
            
            // Populate lessons list
            moduleData.lessons.forEach(lesson => {
                const lessonItem = document.createElement('li');
                lessonItem.className = 'modal-lesson-item';
                
                const lessonLink = document.createElement('a');
                lessonLink.href = `/course/lesson/${lesson.id}/`;
                lessonLink.className = 'modal-lesson-link';
                
                const checkIcon = document.createElement('span');
                checkIcon.className = lesson.is_completed ? 'modal-lesson-check' : 'modal-lesson-check uncompleted';
                checkIcon.innerHTML = lesson.is_completed ? 
                    '<i class="fas fa-check-circle"></i>' : 
                    '<i class="far fa-circle"></i>';
                
                const lessonTitle = document.createElement('span');
                lessonTitle.className = 'modal-lesson-title';
                lessonTitle.textContent = lesson.title;
                
                // Add lesson type indicator
                if (lesson.lesson_type) {
                    const typeIcon = document.createElement('span');
                    typeIcon.className = 'modal-lesson-type';
                    
                    // Choose icon based on lesson type
                    let iconClass = '';
                    if (lesson.lesson_type === 'exercise') {
                        iconClass = 'fas fa-laptop-code';
                        typeIcon.classList.add('type-exercise');
                    } else if (lesson.lesson_type === 'video') {
                        iconClass = 'fas fa-video';
                        typeIcon.classList.add('type-video');
                    } else if (lesson.lesson_type === 'reading') {
                        iconClass = 'fas fa-book';
                        typeIcon.classList.add('type-reading');
                    }
                    
                    typeIcon.innerHTML = `<i class="${iconClass}"></i>`;
                    lessonLink.appendChild(typeIcon);
                }
                
                lessonLink.appendChild(checkIcon);
                lessonLink.appendChild(lessonTitle);
                
                if (lesson.duration) {
                    const lessonDuration = document.createElement('span');
                    lessonDuration.className = 'modal-lesson-duration';
                    lessonDuration.textContent = formatDuration(lesson.duration);
                    lessonLink.appendChild(lessonDuration);
                }
                
                lessonItem.appendChild(lessonLink);
                modalLessonsList.appendChild(lessonItem);
            });
            
            // Show modal with animation
            modal.style.display = 'block';
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
        });
    });
    
    // Close modal when clicking the close button
    closeBtn.addEventListener('click', closeModal);
    
    // Close modal when clicking outside the modal content
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });
    
    // Close modal when pressing ESC key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.classList.contains('show')) {
            closeModal();
        }
    });
    
    // Function to close the modal with animation
    function closeModal() {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}); 