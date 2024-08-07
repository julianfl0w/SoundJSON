# SoundPickle
A Python Format for Audio Samples

The SoundPickle (.sp) format was created for the Jero sampling synthesizer. The idea is to create a modern, Pickle-serialized standard that is easier to use in Python than SF2 and SFZ. 

You can easily convert SF2 and SFZ to SP. 

The webpage example held in this repository can be accessed at https://julianloiacono.com/SoundJSON 


# Usage  
```bash
# First you install directly from the production branch
pip install git+https://github.com/julianfl0w/SoundJSON
# then you can use the CLI to convert a whole directory:  
soundjson .
```

# SoundJSON

SoundJSON is a JSON format designed to store and organize audio samples like SF2 or SFZ. This format facilitates the detailed configuration and easy retrieval of sample data for use in audio applications.

## Fields

### `displayName`
- **Description**: The display name of the instrument.

### `key2samples`
- **Description**: A list of lists mapping keys to their respective samples.
- **Fields**:
  - `sampleNo`: The sample number.
  - `pitchBend`: The pitch bend value.
  - `keyTrigger`: The key that triggers the sample.
  - `targetKeyCenter`: The target key center for the sample.

### `samples`
- **Description**: An array of sample objects containing detailed information about each sample.
- **Fields**:
  - `volume`: Volume level.
  - `hivel`: High velocity limit.
  - `lovel`: Low velocity limit.
  - `pitch_keycenter`: Pitch key center.
  - `hikey`: High key limit.
  - `lokey`: Low key limit.
  - `sample`: The sample file name.
  - `ampeg_dynamic`: Dynamic amplitude envelope.
  - `ampeg_release`: Release time for the amplitude envelope.
  - `ampeg_attack`: Attack time for the amplitude envelope.
  - `sampleFilename`: The full path to the sample file.
  - `gain`: Gain value.
  - `sampleNo`: The sample number.
  - `lengthSamples`: The length of the sample in samples.
  - `sampleRate`: The sample rate of the audio.
  - `audioFormat`: The format of the audio file.
  - `audioData`: The audio data encoded in base64.

### `path`
- **Description**: An array representing the path to the sample files.

### `success`
- **Description**: A boolean indicating if the sample loading was successful.

### `samplesLoadPoint`
- **Description**: The base path where the sample files are located.

### `globalDict`
- **Description**: Contains global settings for the sound, such as volume and envelope parameters.
- **Fields**:
  - `volume`: Volume level.
  - `ampeg_dynamic`: Dynamic amplitude envelope.
  - `ampeg_release`: Release time for the amplitude envelope.
  - `ampeg_attack`: Attack time for the amplitude envelope.

### `masterDict`
- **Description**: Contains master-level settings for the sound. 

### `groupDict`
- **Description**: Contains group-level settings for the sound.
