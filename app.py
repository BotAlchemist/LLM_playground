import streamlit as st  #Web App
from PIL import Image #Image Processing
import numpy as np #Image Processing
from openai import OpenAI
#import openai
import base64
import json
import os
from urllib.parse import urlparse
from audiorecorder import audiorecorder

st.set_page_config(layout="wide")

#i_key= 'sk-proj-aVAzex4cFCRIU0kIqZWT3BlbkFJF2wZ0WEuG7themYfcubn'
i_key= 'sk-proj-iajReYBKXd12Kw4n2F0xXvwP7fHbEowI2O4fT2EkOZaQE2jydpOsxKR4coOWxgS9D1x9W-7IA6T3BlbkFJlPZ1iv2rmgoezm6-EuX-LDGMa21UoC9tWkZphZpQUBPKFCyn-gZAKuiMF3zF2fsyTPbKPGA60'
i_passcode = st.sidebar.text_input("OpenAI key", type='password')

if len(i_passcode) > 0:
    #insertion_index= 11
    #i_key= i_key[:insertion_index] + i_passcode + i_key[insertion_index:]
    i_key = i_key + i_passcode
    #----------------- Global variables -------------------------
    image_folder_path= 'sample_data/'
    os.environ["OPENAI_API_KEY"]= i_key
    client = OpenAI()
    #------------------------------------------------------------

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def extract_text_from_image(i_user_prompt, image_url ):
        response = client.chat.completions.create(
              model='gpt-4o',
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": i_user_prompt},
                          {
                              "type": "image_url",
                              "image_url": {"url": image_url}
                          }
                      ],
                  }
              ],
              max_tokens=1000,
          )
        return response.choices[0].message.content

    def get_gpt_response(i_user_prompt_final, i_temperature, i_model):
        response= client.chat.completions.create(
              model=i_model,
              messages=[
                  {"role": "user", "content": i_user_prompt_final}
              ],
              temperature=i_temperature
          )
        return response.choices[0].message.content, response.usage.total_tokens


    i_menu= st.sidebar.selectbox("Menu", ['Chat', 'Vision', 'Audio', 'Co-pilot'])
    i_openai_model= st.radio('Choose model: ',['gpt-3.5-turbo', 'gpt-4o'] , horizontal=True)

#------------------------------------- Use GTP chat ---------------------------------------------    
    if i_menu== 'Chat':
        i_chat_prompt= st.text_area(":writing_hand:", placeholder="Type your prompt", height=200, key='chat_key')
        i_temperature = st.slider(":thermometer:", min_value = 0.0, max_value = 2.0, value= 0.3, step=0.1)
        
        got_response= False
        if st.button("Ask") and len(i_chat_prompt)>5:
            st.divider()
            llm_output, llm_tokens= get_gpt_response(i_chat_prompt, i_temperature, i_openai_model)
            got_response= True
        
        if got_response:
            st.write(llm_output)
            st.divider()
            st.metric(label="Tokens", value=llm_tokens)

#-------------------------------------- Use Whisper
    elif i_menu== 'Audio':
        st.title("Record audio")
        audio = audiorecorder("Click to record", "Click to stop recording")
        
        if len(audio) > 0:
            # To play audio in frontend:
            st.audio(audio.export().read())
        
            # To save audio to a file, use pydub export method:
            audio.export("audio.wav", format="wav")
        
            # To get audio properties, use pydub AudioSegment properties:
            st.write(f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds")
        
            client = OpenAI()
        
            audio_file= open("audio.wav", "rb")
            transcription = client.audio.transcriptions.create(
              model="whisper-1",
              file=audio_file
            )
            st.divider()
            st.write(transcription.text)
        
            i_user_prompt= transcription.text
        
            i_chat_prompt= st.text_area(":writing_hand:",value= "You are a helpful assistant. First identify the language in which the speaker is speaking then simply translate the text in English.", placeholder="Type your prompt", height=200, key='chat_key')
            response= client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": i_chat_prompt},
                    {"role": "user", "content": i_user_prompt}
                ]
            )
        
            if st.button("Submit"):
              st.divider()
              st.write(response.choices[0].message.content)
        
              st.divider()
              st.write('Total tokens used: '+ str(response.usage.total_tokens))
        
        # Add a button to delete the audio file
        if st.button("Reset audio file"):
            if os.path.exists("audio.wav"):
                os.remove("audio.wav")
                st.success("Audio is reset.")
            else:
                st.warning("Audio does not exist")
    
    

#------------------------------------- Use GTP vision ---------------------------------------------
    elif i_menu== 'Vision':   
        i_input_type= st.selectbox('Choose task:', ["Open camera", "Upload image"])

        if i_input_type == "Open camera":
            i_prompt_template= st.selectbox("Choose prompt", ["Answer","Label", "None"])
            if i_prompt_template == "Answer":
                i_mcq_type= st.radio("Choose MCQ type", ["Single", "Multiple"], horizontal=True)

                i_user_prompt= '''Extract all text from the images. The image contains text in the form of multiple choice questions.
                Ignore any watermarks. Format the output in the form of multiple choice questions.
                provide suitable line breaks with numbering if any.'''

                if i_mcq_type == "Single":
                    i_user_prompt+= "\n Each question can have only one answer."
                elif i_mcq_type == "Multiple":
                    i_user_prompt+= "\n Each question can have multiple answers."

            elif i_prompt_template == "None":
                i_user_prompt= st.text_area("Type your prompt", "")

            elif i_prompt_template == "Label":
                i_user_prompt= '''You are provided with a image of product with its labels and ingredients list.
                Your goal is to extract all texts from labels, ingredients or nutrition facts..
               
                If the image doesnot contain any labels or ingredients, provide a response: "Image does not contain necessary details".
                '''

            image_local = st.camera_input("Take a picture")
            if image_local and len(i_user_prompt)>5:
                with open(os.path.join(image_folder_path,"test.jpg"),"wb") as f:
                    f.write(image_local.getbuffer())

                image_local_temp = os.path.join(image_folder_path,"test.jpg")
                image_url = f"data:image/jpeg;base64,{encode_image(image_local_temp)}"

                #st.write(i_user_prompt)
                ocr_string = extract_text_from_image(i_user_prompt, image_url )
                st.write(ocr_string)

                if i_prompt_template == "Answer":
                    i_user_prompt_final= '''Provide the correct answern for below multiple choice question.
                      First answer what the correct answern is and then explain why you chose this in 2 to 3 lines. \n''' + ocr_string
                    st.divider()
                    llm_output, llm_tokens= get_gpt_response(i_user_prompt_final, 0.2, i_openai_model)
                    st.write(llm_output)
                    st.metric(label="Tokens", value=llm_tokens)

                elif i_prompt_template == "Label":
                    i_user_prompt_final=''' You are an expert nutritionist.
                    Carefully analyze  all the labels and ingredients.
                    Provide the list of ingredients along with a line of what the ingredient is.
                    Provide a brief summary of the extracted label information, highlighting the key details.
                    Focus more on the additives, preservatives, artificial colors or flavors or any harmful substances present.
                    ''' + ocr_string

                    st.divider()
                    llm_output, llm_tokens= get_gpt_response(i_user_prompt_final, 0.3)
                    st.write(llm_output)
                    st.metric(label="Tokens", value=llm_tokens)

                    




else:
    st.info("Please enter your passcode.")
    
    # st.code("sk-proj-7uK5yZ4zEeXyPbrMPJf3sdOrpVHgyEsAHGig94MGVzW1AxdRXF")
    # st.code("sk-proj-nugHpvIH1whBPpcEVLnktMHfQTNh7n2muDQRrM5wd6DTNsYlJz")
    # st.code("sk-proj-aVA9zex4cECRIU1kIqZWT3BlbkFJF2wZ0WEuG7tpemSfxubn")
    # st.code("sk-proj-c4uc7o2F5VGsSYgc1PfUgDtAE6KNC8iMrJRZKVz32Kh0N1Olb3")
    # st.code("sk-proj-ITf7c0lWVCeNi2DPU3YWobQTAn6evVQlnN9Z7f8pDquTQuVhv")
    # st.code("sk-proj-nugHpvIH1whBPpcEVLnktMHfQTNh7n2muDQRrM5wd6DTNsYlJj")
    # st.code("sk-proj-5lNHypFjNexYEkqjNawyXRl0dlR8FNiVjd6GxoLyAtan5ZtXx")
    # st.code("sk-proj-S4svUFupfUHlH5XRU6nbCuwKuS5E8fhka8Ub3EfkpW7d5QZn")
    # st.code("sk-proj-7uK5yZ4zEeXyPbrMPJf3sdOrpVHgyEsAHGig94MGVzW1Axdr")
    # st.code("sk-proj-aVA7zex4cFCRIU0kIqZWT3BlbkFJF2wZ0WEuG7thenYfcubn")
    # st.code("sk-proj-FIfvIkWdKghp9qaCR7XlLU9EoMu6iYjoSeDVtL3BRtO7pUbo")
