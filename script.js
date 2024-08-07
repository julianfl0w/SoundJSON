const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const samples = [];
var key2samples = [];

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
    ";": 76,  // E
    "'": 77,  // F
    "q": 59,  // B flat
    "w": 61,  // C sharp/D flat
    "e": 63,  // D sharp/E flat
    "r": 64,  // E sharp/F
    "t": 66,  // F sharp/G flat
    "y": 68,  // G sharp/A flat
    "u": 70,  // A sharp/B flat
};

async function loadSamples(jsonData) {
    for (let key in jsonData) {
        const sfzData = jsonData[key];
        const samplesList = sfzData.samples;
        key2samples = sfzData.key2samples;

        // Load each sample into the samples object
        for (let i = 0; i < samplesList.length; i++) {
            const sampleData = samplesList[i];
            const audioData = base64ToArrayBuffer(sampleData.audioData);
            const audioBuffer = await audioContext.decodeAudioData(audioData);
            samples.push({
                buffer: audioBuffer,
                gain: sampleData.gain * 0.3,
                sampleFilename: sampleData.sampleFilename
            });
        }
        console.log('Samples loaded:', samples);
        console.log('Key to samples mapping:', key2samples);
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
        const pitch = qwerty_c_major_dict[key];
        if (pitch === undefined) {
            return;
        }
        playSample(pitch);
    });

    document.querySelectorAll('.key').forEach(key => {
        key.addEventListener('click', () => {
            const pitch = parseInt(key.getAttribute('data-note'));
            playSample(pitch);
        });
    });
}

function playSample(pitch) {
    const regionsList = key2samples[pitch];
    if (regionsList === undefined) {
        console.error(`No samples found for pitch: ${pitch}`);
        return;
    }
    regionsList.forEach(region => {
        const sampleNo = region.sampleNo;  // Using sampleNo as the index
        if (sampleNo === undefined || !samples[sampleNo]) {
            console.error(`No sample found for region: ${JSON.stringify(region)}`);
            return;
        }
        const sampleSource = audioContext.createBufferSource();
        const referredSample = samples[sampleNo];
        sampleSource.buffer = referredSample.buffer;

        const gainNode = audioContext.createGain();
        gainNode.gain.value = referredSample.gain; // Set gain based on the gain value in the region

        sampleSource.connect(gainNode).connect(audioContext.destination);
        sampleSource.playbackRate.value = region.pitchBend || 1;

        sampleSource.start();
    });
}

// Load the JSON file and initialize the samples
fetch('SoloSteel1_4.json')
    .then(response => response.json())
    .then(data => {
        loadSamples(data).then(() => enableKeyboardControl());
    })
    .catch(error => console.error('Error loading JSON file:', error));
