class NotebookViewer {
    constructor() {
        this.markdownConverter = new showdown.Converter();
    }

    render(notebook, container) {
        container.innerHTML = '';
        
        // Add notebook cells
        notebook.cells.forEach((cell, index) => {
            const cellElement = document.createElement('div');
            cellElement.className = 'notebook-cell';
            
            // Add cell number
            const cellNumber = document.createElement('div');
            cellNumber.className = 'cell-number';
            cellNumber.textContent = `[${index + 1}]:`;
            cellElement.appendChild(cellNumber);
            
            // Add cell content
            const cellContent = document.createElement('div');
            cellContent.className = 'cell-content';
            
            if (cell.cell_type === 'markdown') {
                cellContent.innerHTML = this.markdownConverter.makeHtml(cell.source.join(''));
            } else if (cell.cell_type === 'code') {
                const pre = document.createElement('pre');
                const code = document.createElement('code');
                code.className = 'python';
                code.textContent = cell.source.join('');
                pre.appendChild(code);
                cellContent.appendChild(pre);
                
                // Add outputs if any
                if (cell.outputs && cell.outputs.length > 0) {
                    const outputDiv = document.createElement('div');
                    outputDiv.className = 'cell-output';
                    cell.outputs.forEach(output => {
                        if (output.output_type === 'stream') {
                            const pre = document.createElement('pre');
                            pre.textContent = output.text.join('');
                            outputDiv.appendChild(pre);
                        } else if (output.output_type === 'execute_result' || output.output_type === 'display_data') {
                            if (output.data['text/plain']) {
                                const pre = document.createElement('pre');
                                pre.textContent = output.data['text/plain'].join('');
                                outputDiv.appendChild(pre);
                            }
                        }
                    });
                    cellContent.appendChild(outputDiv);
                }
            }
            
            cellElement.appendChild(cellContent);
            container.appendChild(cellElement);
        });
        
        // Highlight code blocks
        if (window.hljs) {
            container.querySelectorAll('pre code').forEach(block => {
                hljs.highlightBlock(block);
            });
        }
    }
}

// Create global instance
window.nbviewer = new NotebookViewer(); 