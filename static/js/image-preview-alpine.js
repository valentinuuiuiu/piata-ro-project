

document.addEventListener('alpine:init', () => {
  Alpine.data('imagePreview', () => ({
    previewFile(event, previewId) {
      const input = event.target;
      const preview = document.getElementById(previewId);
      
      if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
          preview.src = e.target.result;
          preview.classList.remove('hidden');
        }
        reader.readAsDataURL(input.files[0]);
      }
    }
  }));
});

