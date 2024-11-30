from pydantic import BaseModel, field_validator, model_validator, Field
from typing import List, Union
import json
import logging

logging.basicConfig(level=logging.INFO, filename="models.log", filemode="a", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PressAction(BaseModel):
    press: str


class ComboAction(BaseModel):
    hold: list[str] = Field(..., title="The list of keys to be held down while the seqyence of 'press' is executed", min_length=0)
    press: list[str] = Field(..., title="The list of keys to be pressed", min_length=1)


class WordAction(BaseModel):
    word: str


class DelayAction(BaseModel):
    delay: str


class EventData(BaseModel):
    keys: List[Union[PressAction, ComboAction, WordAction, DelayAction]] = Field(..., title="The list of actions to be performed", min_length=1)

 
class TTSData(BaseModel):
    message: str = Field(..., title="The message to be converted to speech")
    volume: float = Field(..., title="The volume of the audio TTS to be played", ge=0.0, le=1.0)

    @field_validator("volume")
    def convert_volume_to_float(cls, value):
        if isinstance(value, str):  
            try:
                return float(value)  
            except ValueError:
                raise ValueError(f"Invalid volume value: {value}. It must be a number.")
        return value  


class WsEvent(BaseModel):
    event: str
    data: Union[EventData, TTSData]

    @model_validator(mode="before")
    def process_combo_actions(cls, values):
        if values.get('event') == "tts":
            ttsdata = TTSData.model_validate(values['data'])
            if not isinstance(ttsdata, TTSData):
                raise ValueError("Invalid data format for 'tts' event. Expected TTSData.")
            return values
        
        keys = values.get('data', {}).get('keys', [])
        for i, key in enumerate(keys):
            if "combo" in key:
                try:
                    combo = key["combo"]
                    keys[i] = ComboAction(hold=combo["hold"], press=combo["press"])
                except KeyError as e:
                    raise ValueError(f"Invalid combo format: {key}. Missing key: {e}")

        values['data']['keys'] = keys
        return values

    @model_validator(mode="before")
    def check_event_value(cls, values):
        allowed_events = ["keypress", "tts"]
        event = values.get("event")
        if event not in allowed_events:
            raise ValueError(f"Invalid event: {event}. Allowed events are {allowed_events}")
        return values
