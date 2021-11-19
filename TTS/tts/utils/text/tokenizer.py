from typing import Callable, Dict, List, Union

from TTS.tts.utils.text import cleaners
from TTS.tts.utils.text.characters import Graphemes, IPAPhonemes
from TTS.tts.utils.text.phonemizers import DEF_LANG_TO_PHONEMIZER, get_phonemizer_by_name


class TTSTokenizer:
    """🐸TTS tokenizer to convert input characters to token IDs and back.

    Args:
        use_phonemes (bool):
            Whether to use phonemes instead of characters. Defaults to False.

        characters (Characters):
            A Characters object to use for character-to-ID and ID-to-character mappings.

        text_cleaner (callable):
            A function to pre-process the text before tokenization and phonemization. Defaults to None.

        phonemizer (Phonemizer):
            A phonemizer object or a dict that maps language codes to phonemizer objects. Defaults to None.

    """

    def __init__(
        self,
        use_phonemes=False,
        text_cleaner: Callable = None,
        characters: "BaseCharacters" = None,
        phonemizer: Union["Phonemizer", Dict] = None,
        add_blank: bool = False,
        use_eos_bos=False,
    ):
        self.text_cleaner = text_cleaner or (lambda x: x)
        self.use_phonemes = use_phonemes
        self.add_blank = add_blank
        self.use_eos_bos = use_eos_bos
        self.characters = characters
        self.phonemizer = phonemizer

    def encode(self, text: str) -> List[int]:
        """Encodes a string of text as a sequence of IDs."""
        token_ids = []
        for char in text:
            idx = self.characters.char_to_id(char)
            token_ids.append(idx)
        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        """Decodes a sequence of IDs to a string of text."""
        text = ""
        for token_id in token_ids:
            text += self.characters.id_to_char(token_id)
        return text

    def text_to_ids(self, text: str, language: str = None) -> List[int]:
        """Converts a string of text to a sequence of token IDs.

        Args:
            text(str):
                The text to convert to token IDs.

            language(str):
                The language code of the text. Defaults to None.

        1. Text normalizatin
        2. Phonemization (if use_phonemes is True)
        3. Add blank char between characters
        4. Add BOS and EOS characters
        5. Text to token IDs
        """
        # TODO: text cleaner should pick the right routine based on the language
        text = self.text_cleaner(text)
        if self.use_phonemes:
            text = self.phonemizer.phonemize(text, separator="")
        if self.add_blank:
            text = self.intersperse_blank_char(text, True)
        if self.use_eos_bos:
            text = self.pad_with_bos_eos(text)
        return self.encode(text)

    def ids_to_text(self, id_sequence: List[int]) -> str:
        """Converts a sequence of token IDs to a string of text."""
        return self.decode(id_sequence)

    def pad_with_bos_eos(self, char_sequence: List[str]):
        """Pads a sequence with the special BOS and EOS characters."""
        return [self.characters.bos] + list(char_sequence) + [self.characters.eos]

    def intersperse_blank_char(self, char_sequence: List[str], use_blank_char: bool = False):
        char_to_use = self.characters.blank_char if use_blank_char else self.characters.pad
        result = [char_to_use] * (len(char_sequence) * 2 + 1)
        result[1::2] = char_sequence
        return result

    def print_logs(self, level: int = 1):
        indent = "\t" * level
        print(f"{indent}| > add_blank: {self.use_phonemes}")
        print(f"{indent}| > use_eos_bos: {self.use_phonemes}")
        print(f"{indent}| > use_phonemes: {self.use_phonemes}")
        print(f"{indent}| > phonemizer: {self.phonemizer.print_logs(level + 1)}")

    @staticmethod
    def init_from_config(config: "Coqpit"):
        """Init Tokenizer object from the config.

        Args:
            config (Coqpit): Coqpit model config.
        """
        if isinstance(config.text_cleaner, (str, list)):
            text_cleaner = getattr(cleaners, config.text_cleaner)

        if config.use_phonemes:
            characters = IPAPhonemes().init_from_config(config)
            phonemizer_kwargs = {"language": config.phoneme_language}
            phonemizer = get_phonemizer_by_name(DEF_LANG_TO_PHONEMIZER[config.phoneme_language], **phonemizer_kwargs)
        else:
            characters = Graphemes().init_from_config(config)
        return TTSTokenizer(
            config.use_phonemes, text_cleaner, characters, phonemizer, config.add_blank, config.enable_eos_bos_chars
        )