import gradio as gr
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODES = {

    "Technical Explainer": {

        "system_prompt":
        "Explain clearly for beginners.",

        "few_shot_examples": [
            {
                "user": "What is API?",
                "assistant": "API allows software communication."
            }
        ],

        "output_format": "text"
    },

    "Debate Coach": {

        "system_prompt":
        "Show both sides equally and fairly.",

        "few_shot_examples": [],

        "output_format": "text"
    },

    "Code Reviewer": {

        "system_prompt":
        """
Return ONLY JSON.

Format:
{
"issues":"",
"suggestions":"",
"severity":""
}
""",

        "few_shot_examples": [],

        "output_format": "json"
    },

    "Creative Writer": {

        "system_prompt":
        "Write vivid and creative responses.",

        "few_shot_examples": [],

        "output_format": "text"
    }

}


def inject_examples(mode):

    examples = []

    for ex in mode["few_shot_examples"]:

        examples.append(
            {
                "role": "user",
                "content": ex["user"]
            }
        )

        examples.append(
            {
                "role": "assistant",
                "content": ex["assistant"]
            }
        )

    return examples


def format_json(text):

    try:

        data = json.loads(text)

        return f"""
### Issues
{data.get("issues")}

### Suggestions
{data.get("suggestions")}

### Severity
{data.get("severity")}
"""

    except:

        return text


def stream_chat(user_input, history, selected_mode, temperature):

    mode = MODES[selected_mode]

    messages = [

        {
            "role": "system",
            "content": mode["system_prompt"]
        }

    ]

    messages.extend(
        inject_examples(mode)
    )

    if history:

        for msg in history:

            if (
                isinstance(msg, dict)
                and
                "role" in msg
                and
                "content" in msg
            ):

                messages.append(
                    {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                )

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    stream = client.chat.completions.create(

        messages=messages,

        model="llama-3.3-70b-versatile",

        temperature=temperature,

        stream=True
    )

    reply = ""

    for chunk in stream:

        delta = (
            chunk
            .choices[0]
            .delta
            .content
        )

        if delta:

            reply += delta

            yield reply

    if mode["output_format"] == "json":

        yield format_json(reply)


def update_prompt(selected):

    return MODES[selected][
        "system_prompt"
    ]


with gr.Blocks() as app:

    gr.Markdown(
        "# PromptForge"
    )

    mode = gr.Dropdown(

        choices=list(MODES.keys()),

        value="Technical Explainer",

        label="Mode"
    )

    temperature = gr.Slider(

        minimum=0,

        maximum=1.5,

        value=0.7,

        label="Temperature"
    )

    prompt = gr.Markdown()

    mode.change(

        update_prompt,

        inputs=mode,

        outputs=prompt
    )

    update_prompt(
        "Technical Explainer"
    )

    gr.ChatInterface(

        fn=stream_chat,

        additional_inputs=[

            mode,

            temperature

        ]
    )

app.launch(
    share=True
)