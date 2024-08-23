// Assuming loadSamples is defined in another part of your application
async function loadSamples(jsonFileName) {
    try {
        const response = await fetch(jsonFileName);
        const jsonData = await response.json();
        console.log('Loaded samples from:', jsonFileName, 'with data:', jsonData);
        // Add your audio handling logic here
    } catch (error) {
        console.error('Error loading samples:', error);
    }
}

async function fetchSiteMap() {
    try {
        const response = await fetch('sitemap.json');
        const jsonData = await response.json();
        const container = document.getElementById('sitemap');
        renderSiteMap(jsonData, container);
    } catch (error) {
        console.error('Error fetching sitemap:', error);
    }
}

function renderSiteMap(jsonData, container, parentKey = "") {
    const ul = document.createElement('ul');
    for (const key in jsonData) {
        const li = document.createElement('li');
        li.textContent = key;
        
        if (typeof jsonData[key] === 'object' && Object.keys(jsonData[key]).length > 0) {
            li.addEventListener('click', function(event) {
                event.stopPropagation(); // Prevent triggering clicks on parent elements
                while (li.nextSibling) { // Remove any existing child nodes on new click
                    li.parentNode.removeChild(li.nextSibling);
                }
                renderSiteMap(jsonData[key], li); // Recursive call to handle nested objects
            });
        } else if (typeof jsonData[key] === 'string') { // It's a string path to a JSON file
            li.style.color = 'red'; // Style for keys that represent JSON files
            li.addEventListener('click', async function(event) {
                event.stopPropagation(); // Prevent triggering clicks on parent elements
                await loadFromFilename(jsonData[key]); // Load the sample using the file path
            });
        }
        
        ul.appendChild(li);
    }
    container.appendChild(ul);
}


document.addEventListener('DOMContentLoaded', fetchSiteMap);

// Example usage: load and play a MIDI file
//
document.getElementById('transpose').addEventListener('input', function() {
    transpose = parseInt(this.value, 10);
    // Apply transpose logic to your notes, adjusting their pitch based on transposeValue
});


// JavaScript to handle the button click
document.getElementById('playMidiButton').addEventListener('click', function() {
    playMidiFile('fairyfountain.mid');
});
