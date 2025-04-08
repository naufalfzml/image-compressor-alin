document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('file-upload').addEventListener('change', handleFileSelect);
    document.getElementById('compression-rate').addEventListener('input', handleRateChange);

    let selectedFile = null;
    let compressionRate = null;

    function handleFileSelect(event) {
        selectedFile = event.target.files[0];
        if (selectedFile && compressionRate) {
            compressAndShowImage();
        }
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('before-image').style.backgroundImage = `url(${e.target.result})`;
        }
        reader.readAsDataURL(selectedFile);
    }

    function handleRateChange(event) {
        compressionRate = event.target.value;
        if (selectedFile && compressionRate) {
            compressAndShowImage();
        }
    }

    function compressAndShowImage() {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('rate', compressionRate);

        fetch('/compress', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const imagePath = data.compressed_image_path + '?' + new Date().getTime();
            document.getElementById('after-image').style.backgroundImage = `url(${imagePath})`;
            document.getElementById('compression-time').textContent = data.compression_time.toFixed(2);
            document.getElementById('pixel-difference').textContent = data.pixel_difference.toFixed(2);
            // Menampilkan tombol "Download"
            const downloadButton = document.getElementById('download-button');
            downloadButton.style.display = 'inline-block';
            downloadButton.style.margin = 0;
            // Mengatur event listener untuk tombol "Download"
            document.getElementById('download-button').addEventListener('click', function() {
                downloadImage(imagePath);
            });
        })
        .catch(error => console.error('Error:', error));
    }

    function downloadImage(imagePath) {
        // Membuat elemen <a> untuk memulai unduhan
        const downloadAnchor = document.createElement('a');
        downloadAnchor.href = imagePath;
        downloadAnchor.download = `compressed_photo_${selectedFile.name}`;
        downloadAnchor.click();
    }
});
