# ViMax-inspired pipeline for AiForge
# Adapted from https://github.com/HKUDS/ViMax (MIT License)
# Key changes: langchain → direct HTTP to sensenova, file storage → DB, generators → oiioii

from .extractor import CharacterExtractor, StoryboardExtractor
from .decomposer import VisualDecomposer
