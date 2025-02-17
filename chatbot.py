#!/usr/bin/env -S uvx marimo@0.11.2 edit --sandbox
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "requests==2.32.3",
# ]
# ///

import marimo

__generated_with = "0.11.5"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import requests, uuid, json
    return json, mo, requests, uuid


@app.cell
def _(mo):
    mo.md(
        f"""
        # Kashmiri Language Chatbot Demo

        _A Demo chatbot that can converse in the [Kashmiri language](https://en.wikipedia.org/wiki/Kashmiri_language)._

        {mo.image(str(mo.notebook_location() / 'public' / 'kashmiri.png'), width=200)}

        ## Problem

        LLM's like ChatGPT lack support for Kashmiri language, so native speakers of the language are unable to get the benefits of these modern tools.

        ## Insight

        By combining a translator service with a chatbot api, we can create our own kashmiri speaking chatbot.

        Recently Microsoft translator has added support for the language, see [the announcement page](https://news.microsoft.com/en-in/microsoft-translator-expands-to-20-indian-languages-empowering-linguistic-diversity/).

        It can be tried at [Bing translator](https://www.bing.com/translator?to=ks&setlang=en), they also have an API serivce available at Azure Cloud for this.

        ## Solution

        {mo.mermaid(
            """
            sequenceDiagram
                participant User
                participant Azure Translator
                participant OpenAI ChatAPI

                Note over User: Input in Kashmiri
                User->>Azure Translator: Send Kashmiri text (from Perso-Arabic/Roman script)
                Azure Translator->>OpenAI ChatAPI: Translated English text
                OpenAI ChatAPI->>Azure Translator: English response
                Azure Translator->>User: Kashmiri translation and transliteration (to Roman script)
            Note over User: Shows translated Kashmiri text with transliteration
            """
        )
        }
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Application
        Enter the credentials for Azure Translator and OpenAI Chat API, and start chatting with the chatbot in Kashmiri language.

        _Note you can write in both Perso-Arabic and Roman(english alphabets) script._
        """
    )
    return


@app.cell
def _(mo):
    azure_translator_api_region = mo.ui.text(label="Region")
    azure_translator_api_endpoint = mo.ui.text(label="Endpoint", value="https://api.cognitive.microsofttranslator.com")
    azure_translator_api_key = mo.ui.text(label="API Key", kind="password")
    openai_api_key = mo.ui.text(label="API Key", kind="password")
    mo.hstack([
        mo.vstack([
            mo.md("### [Azure Translator API](https://learn.microsoft.com/en-us/azure/ai-services/translator/)"),
            azure_translator_api_region,
            azure_translator_api_endpoint,
            azure_translator_api_key,
        ]),
        mo.vstack([
            mo.md("### [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat)"),
            openai_api_key
        ])
    ], justify="start")
    return (
        azure_translator_api_endpoint,
        azure_translator_api_key,
        azure_translator_api_region,
        openai_api_key,
    )


@app.cell
def _(requests, typing, uuid):
    def translator(api_key: str, api_region: str, api_endpoint: str, sourceLanguage: str, destinationLanguage: str, messages: typing.List[str]) -> object:
        path = '/translate'
        constructed_url = api_endpoint + path

        params = {
            'api-version': '3.0',
            'from': sourceLanguage,
            'to': [destinationLanguage],
        }

        if sourceLanguage == "ks":
            params['fromScript'] = 'Latn'

        if destinationLanguage == "ks":
            params['toScript'] = 'Latn'

        headers = {
            'Ocp-Apim-Subscription-Key': api_key,
            'Ocp-Apim-Subscription-Region': api_region,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{'text': message} for message in messages]

        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        if request.status_code != 200:
            raise Exception("Request failed with status code: ", request.status_code)
        response = request.json()
        return response
    def translate_kashmiri_to_english(key: str, location: str, endpoint: str, msgs: typing.List[str]) -> object:
        return translator(key, location, endpoint, "ks", "en", msgs)
    def translate_english_to_kashmiri(key: str, location: str, endpoint: str, msgs: typing.List[str]) -> object:
        return translator(key, location, endpoint, "en", "ks", msgs)
    return (
        translate_english_to_kashmiri,
        translate_kashmiri_to_english,
        translator,
    )


@app.cell
def _(
    azure_translator_api_endpoint,
    azure_translator_api_key,
    azure_translator_api_region,
    mo,
    openai_api_key,
    requests,
    translate_english_to_kashmiri,
    translate_kashmiri_to_english,
):
    mo.stop(
        not (
            azure_translator_api_key.value and 
            azure_translator_api_region.value and 
            azure_translator_api_endpoint.value and 
            openai_api_key.value
        ),
        mo.md("""
        **Please enter the required credentials to see the chatbot**

        _Note: You can get translator credentials by registering translator service at Azure, for OpenAI create an api key for completions at OpenAI platform._

        _Your credentials won't be stored or shared with anyone, they are only used in memory to run the chatbot._

        You can also contact me at [asrar.nahvi@gmail.com](mailto:asrar.nahvi@gmail.com) for temporary credentials in case you want to test out the chatbot.

        _To see app code click on the three dot horizontal menu on the top right corner of the app._

        Code is hosted on GitHub at https://github.com/aszenz/kashmiri-chatbot
        """)
    )
    def kashir_gpt(msgs: list, config) -> object:
        texts = [msg.content for msg in msgs]
        english_prompt_msgs = translate_kashmiri_to_english(azure_translator_api_key.value, azure_translator_api_region.value, azure_translator_api_endpoint.value, texts)
        english_text = [translated_text['translations'][0]['text'] for translated_text in english_prompt_msgs]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key.value}"
        }

         # Format messages as a list of message objects
        formatted_messages = [
            {"role": "system", "content": "You are a helpful assistant. Respond concisely."}
        ]
        # Add each user message as a separate message object
        for text in english_text:
            formatted_messages.append({"role": "user", "content": text})

        payload = {
            "model": 'gpt-4o-mini',
            "messages": formatted_messages,
            "temperature": 0.7,
            "max_tokens": 300
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            final_translation = translate_english_to_kashmiri(azure_translator_api_key.value, azure_translator_api_region.value, azure_translator_api_endpoint.value, [ai_response])
            return mo.vstack([
                mo.accordion({
                    "See in English": mo.vstack([
                        mo.md('_User prompt:_'),
                        mo.md(f"**{english_text.pop()}**"),
                        mo.md('_AI response:_'),
                        mo.md(ai_response)
                    ])
                }),
                final_translation[0]['translations'][0]['text'],
                final_translation[0]['translations'][0]['transliteration']['text']
            ])
        else:
            raise Exception("Could not process the request", response)


    mo.ui.chat(
        kashir_gpt,
        show_configuration_controls = True,
        prompts = [
            'kutbe khatunech dastane',
            'خُتبہ خاتونٕچ داستانہٕ',
            'keshiri binz abaedi kyah chi',
            'keshiri heynd mukhtelif alaqe kyah chi',
            '20 ہِمہِ صٔدی منٛز کُس اوس کٔشیٖرِ ہُنٛد حُکُمران',
            'کشمیٖری زبانہِ ہُنٛد تٲریٖخ کیٛاہ چھُ'
        ]
    )
    return (kashir_gpt,)


if __name__ == "__main__":
    app.run()
