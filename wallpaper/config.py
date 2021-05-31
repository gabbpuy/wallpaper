# -*- coding: utf-8 -*-
import dataclasses
import json
from typing import Dict, Optional, List, IO


class DataclassJSON_Encoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class DataclassIO:
    def dumps(self) -> str:
        return json.dumps(self, cls=DataclassJSON_Encoder)

    def dump(self, fp: IO):
        json.dump(self, fp, cls=DataclassJSON_Encoder)

    def loads(self, json_blob: str):
        self.update(json.loads(json_blob))

    def load(self, fp: IO):
        self.update(json.load(fp))

    def update(self, structure: dict):
        self.__dict__.update(structure)


@dataclasses.dataclass
class MonitorConfig(DataclassIO):
    blending: bool = True
    blend_ratio: float = 0.4
    crop: bool = False
    fill: bool = False
    # collage, strip, spiral
    fill_mode: str = 'spiral'
    gradient: bool = False
    pre_rotate: bool = False
    reset_collage_folder: bool = True
    single_folder_mode: bool = False
    shadow_mode: bool = False
    spanning: bool = False
    stack_mode: bool = False
    stop_threshold: int = 32
    directories: List[str] = dataclasses.field(default_factory=list)
    desktop_filters: List[str] = dataclasses.field(default_factory=list)
    image_filters: List[str] = dataclasses.field(default_factory=list)
    background_filters: List[str] = dataclasses.field(default_factory=list)


class WallpaperConfig:
    def __init__(self):
        self.global_config: Optional[MonitorConfig] = MonitorConfig()
        self.monitors: Dict[str] = {}

    def load(self, fp: IO):
        structure = json.load(fp)
        self.global_config.update(structure['global_config'])
        for k, v in structure.get('monitors', {}).items():
            monitor = MonitorConfig()
            monitor.update(self.global_config.__dict__)
            monitor.update(v)
            self.monitors[k] = monitor

    def dump(self, fp: IO):
        json.dump(self.__dict__, fp, cls=DataclassJSON_Encoder, indent=4)
