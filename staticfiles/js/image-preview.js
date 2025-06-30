document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('id_images');
    const previewGrid = document.getElementById('image-preview-grid');
    const maxFileSize = 5 * 1024 * 1024; // 5MB
    const maxFiles = 10;
    let currentFiles = [];

    function createPreviewElement(file, index) {
        const reader = new FileReader();
        const preview = document.createElement('div');
        preview.className = 'relative aspect-square group';
        
        reader.onload = function(e) {
            preview.innerHTML = `
                <img src="${e.target.result}" 
                     class="w-full h-full object-cover rounded-lg border border-gray-200"
                     alt="Preview">
                <div class="absolute inset-0 bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                    <button type="button" data-index="${index}" class="remove-image text-white hover:text-red-500 transition-colors">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
                ${index === 0 ? '<div class="absolute top-2 left-2 bg-primary text-white px-2 py-1 rounded-md text-xs">Principal</div>' : ''}
            `;
        }
        
        reader.readAsDataURL(file);
        return preview;
    }

    function updatePreviews() {
        previewGrid.innerHTML = '';
        currentFiles.forEach((file, index) => {
            const preview = createPreviewElement(file, index);
            previewGrid.appendChild(preview);
        });
    }

    function handleFileSelect(event) {
        const files = Array.from(event.target.files);
        
        // Validate file count
        if (currentFiles.length + files.length > maxFiles) {
            alert(`Poți încărca maximum ${maxFiles} imagini.`);
            return;
        }
        
        // Validate file types and sizes
        const validFiles = files.filter(file => {
            if (!file.type.startsWith('image/')) {
                alert(`${file.name} nu este o imagine validă.`);
                return false;
            }
            if (file.size > maxFileSize) {
                alert(`${file.name} este prea mare. Dimensiunea maximă este 5MB.`);
                return false;
            }
            return true;
        });
        
        currentFiles = [...currentFiles, ...validFiles];
        updatePreviews();
        
        // Update the input's files
        const dataTransfer = new DataTransfer();
        currentFiles.forEach(file => dataTransfer.items.add(file));
        imageInput.files = dataTransfer.files;
    }

    // Handle drag and drop
    const dropZone = imageInput.closest('label');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('border-primary');
    }

    function unhighlight(e) {
        dropZone.classList.remove('border-primary');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFileSelect({target: {files}});
    }

    // Handle file input change
    imageInput.addEventListener('change', handleFileSelect);

    // Handle image removal
    previewGrid.addEventListener('click', function(e) {
        const removeButton = e.target.closest('.remove-image');
        if (!removeButton) return;
        
        const index = parseInt(removeButton.dataset.index);
        currentFiles.splice(index, 1);
        updatePreviews();
        
        // Update the input's files
        const dataTransfer = new DataTransfer();
        currentFiles.forEach(file => dataTransfer.items.add(file));
        imageInput.files = dataTransfer.files;
    });
});
