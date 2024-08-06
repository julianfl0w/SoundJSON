const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const samples = {};

const qwerty_c_major_dict = {
    "a": 60,  // C
    "s": 62,  // D
    "d": 64,  // E
    "f": 65,  // F
    "g": 67,  // G
    "h": 69,  // A
    "j": 71,  // B
    "k": 72,  // C
    "l": 74,  // D
    "q": 59,  // B flat
    "w": 61,  // C sharp/D flat
    "e": 63,  // D sharp/E flat
    "r": 64,  // E sharp/F
    "t": 66,  // F sharp/G flat
    "y": 68,  // G sharp/A flat
    "u": 70,  // A sharp/B flat
}

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

async function loadSamples(jsonData) {
    const regions = jsonData["sfz_test/Harp.sfz"].regions;

    for (const region of regions) {
        if (region.audioFormat === "wav") {
            const audioData = base64ToArrayBuffer(region.audioData);

            const audioBuffer = await audioContext.decodeAudioData(audioData);
            samples[region.pitch_keycenter] = {
                buffer: audioBuffer,
                gain: region.gain * 0.3 // Default to 1 if gain is not specified
            };
        } else {
            console.error(`Unsupported audio format: ${region.audioFormat}`);
        }
    }
}

function base64ToArrayBuffer(base64) {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

function enableKeyboardControl() {
    window.addEventListener('keydown', (event) => {
        const key = event.key;
        if (key >= 'a' && key <= 'z') {
            const pitch = key.charCodeAt(0) - 97 + 30; // Mapping 'a' to 30, 'b' to 31, etc.
            playSample(pitch);
        }
    });
}

function playSample(pitch) {
    const sample = samples[pitch];
    if (sample) {
        const sampleSource = audioContext.createBufferSource();
        sampleSource.buffer = sample.buffer;

        const gainNode = audioContext.createGain();
        gainNode.gain.value = sample.gain; // Set gain based on the gain value in the region

        sampleSource.connect(gainNode).connect(audioContext.destination);
        sampleSource.start();
    }
}
