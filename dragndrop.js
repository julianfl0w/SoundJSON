
document.getElementById('dropArea').addEventListener('dragover', (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
});

document.getElementById('dropArea').addEventListener('drop', async (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    const reader = new FileReader();

    reader.onload = async (e) => {
        const jsonData = JSON.parse(e.target.result);
        await loadSamples(jsonData);
        enableKeyboardControl();
        alert('Samples loaded successfully!');
    };

    reader.readAsText(file);
});
