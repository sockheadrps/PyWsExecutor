from pydantic import BaseModel, field_validator, model_validator, Field
from typing import List, Union
import pprint


class TTSData(BaseModel):
    message: str
    volume: float

    @field_validator("volume")
    def convert_volume_to_float(cls, value):
        if isinstance(value, str):  
            try:
                return float(value)  
            except ValueError:
                raise ValueError(f"Invalid volume value: {value}. It must be a number.")
        return value  


class Screenshot(BaseModel):
    pin: str = Field(default="1234")

class PressAction(BaseModel):
    press: str


class ComboAction(BaseModel):
    hold: list[str]  
    press: list[str] 


class WordAction(BaseModel):
    word: str


class DelayAction(BaseModel):
    delay: str


class ActionList(BaseModel):
    keys: List[Union[PressAction, ComboAction, WordAction, DelayAction]]


class EventData(BaseModel):
    keys: List[Union[PressAction, ComboAction, WordAction, DelayAction]]


class WsEvent(BaseModel):
    event: str
    data: Union[EventData, TTSData, Screenshot]

    @model_validator(mode="before")
    def process_combo_actions(cls, values):
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
        allowed_events = ["keypress", "tts", "screenshot"]
        event = values.get("event")
        if event not in allowed_events:
            raise ValueError(f"Invalid event: {event}. Allowed events are {allowed_events}")
        return values


if __name__ == "__main__":
    pprint.pprint(WsEvent.model_json_schema())