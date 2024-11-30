document.addEventListener('DOMContentLoaded', function() {
    const API_URL = 'https://invoice-reader-api.onrender.com'; // We'll update this after deployment
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');

    form.onsubmit = async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a file');
            return;
        }
        
        formData.append('file', file);
        
        try {
            loadingDiv.style.display = 'block';
            resultDiv.innerHTML = '';
            
            const response = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                let output = '<h3>Extracted Data:</h3>';
                output += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                resultDiv.innerHTML = output;
            } else {
                resultDiv.innerHTML = `<div class="error">Error: ${data.error || 'Failed to process invoice'}</div>`;
            }
        } catch (error) {
            resultDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        } finally {
            loadingDiv.style.display = 'none';
        }
    };
});
