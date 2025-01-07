from flask import Flask, render_template, request, jsonify
from gtts import gTTS
import openai
import os
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from PIL import Image
import pytesseract
from pydub import AudioSegment
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)

# Configure your OpenAI API key (make sure not to expose your real key publicly)
openai.api_key = 'openai key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    # Get conversion type and user input from the form
    conversion_type = request.form.get('conversion_type')
    user_input = request.form.get('input_text')

    try:
        outputs = []

        # Text to Text conversion (generating multiple responses)
        if conversion_type == 'text-to-text':
            for _ in range(3):  
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_input}],
                    max_tokens=500
                )
                outputs.append(response['choices'][0]['message']['content'])

        # Text to Image conversion (generating image based on text input)
        elif conversion_type == 'text-to-image':
            for _ in range(3):  
                response = openai.Image.create(
                    prompt=user_input,
                    n=1,  
                    size="512x512"
                )
                outputs.append(response['data'][0]['url'])

        # Text to Audio (convert input text to speech and generate MP3)
        elif conversion_type == 'text-to-audio':
            try:
                explanation = user_input
                for i in range(3):  # Generate multiple audio files
                    audio_file = f"static/generated_audio_{i}.mp3"
                    tts = gTTS(text=explanation, lang='en')
                    tts.save(audio_file)
                    outputs.append(f"/{audio_file}")  # Include the audio path
            except Exception as e:
                return jsonify({'error': f'An error occurred during text-to-audio conversion: {str(e)}'})

        # Text to Speech conversion (Generate text and convert to speech)
        elif conversion_type == 'text-to-speech':
            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_input}]
            )
            generated_text = gpt_response['choices'][0]['message']['content']

            # Generate the audio
            tts = gTTS(generated_text, lang='en')
            audio_path = 'static/generated_audio.mp3'
            tts.save(audio_path)

            # Only return the audio path, removing the text
            outputs.append({'audio_path': f"/{audio_path}"})


        # Text to Code conversion (Generate code for the input)
        elif conversion_type == 'text-to-code':
            for _ in range(3):  
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": f"Generate code for: {user_input}"}],
                    max_tokens=300
                )
                outputs.append(response['choices'][0]['message']['content'])

        # Speech to Text (Convert audio to text)
        # Change 'speech-to-text' to 'audio-to-text'
        elif conversion_type == 'audio-to-text':
            file = request.files.get('input_file')
            if not file:
                return jsonify({'error': 'No file uploaded.'})
            
            input_file_path = os.path.join("uploads", file.filename)
            file.save(input_file_path)
            logging.debug(f"Received audio file at: {input_file_path}")

            # Convert MP3 to WAV if necessary
            if input_file_path.lower().endswith(".mp3"):
                wav_audio_path = input_file_path.replace(".mp3", ".wav")
                try:
                    sound = AudioSegment.from_mp3(input_file_path)
                    sound.export(wav_audio_path, format="wav")
                    logging.debug(f"Converted MP3 to WAV at: {wav_audio_path}")
                except Exception as e:
                    logging.error(f"Error converting MP3 to WAV: {e}")
                    return jsonify({'error': f"Error converting MP3 to WAV: {e}"})
            else:
                wav_audio_path = input_file_path

            # Recognize Speech
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_audio_path) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    outputs.append(text)
                except sr.UnknownValueError:
                    return jsonify({'error': 'Google Speech Recognition could not understand the audio.'})
                except sr.RequestError as e:
                    return jsonify({'error': f"Error with the speech recognition service: {e}"})



                
                
                
                
                
                
                

        # Image to Text (Extract text from an image)
        elif conversion_type == 'image-to-text':
            if 'input_file' not in request.files:
                return jsonify({'error': 'No image file uploaded.'})

            image_file = request.files['input_file']
            image_path = os.path.join("uploads", image_file.filename)
            image_file.save(image_path)
            logging.info(f"Uploaded image saved at: {image_path}")

            try:
                img = Image.open(image_path)
                text = pytesseract.image_to_string(img)
                if text:
                    outputs.append(text)
                else:
                    outputs.append("No text found in the image.")
            except Exception as e:
                logging.error(f"Error processing image: {str(e)}")
                return jsonify({'error': f'An error occurred during image-to-text conversion: {str(e)}'})





        # Image to Image (Generate a modified version of an image based on input)
        elif conversion_type == 'image-to-image':
            input_image_path = request.form.get('input_file_path')
            logging.debug(f"Received file path: {input_image_path}")
            if not input_image_path:
                return jsonify({'error': 'No image path provided.'})

            if not os.path.exists(input_image_path):
                return jsonify({'error': 'File not found at the provided path.'})

            try:
                # Use OpenAI Image generation (or an alternative service for image manipulation)
                response = openai.Image.create(
                    prompt="Generate an image based on: " + user_input,
                    n=1,
                    size="512x512"
                )
                image_url = response['data'][0]['url']
                outputs.append(image_url)
            except Exception as e:
                logging.error(f"Error processing image-to-image conversion: {str(e)}")
                return jsonify({'error': f'An error occurred during image-to-image conversion: {str(e)}'})


        else:
            outputs = ["Feature not implemented yet"] * 3

        return jsonify(outputs=outputs)

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
