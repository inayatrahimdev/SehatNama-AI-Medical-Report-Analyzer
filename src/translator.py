from functools import lru_cache


@lru_cache(maxsize=1)
def _load_model():
    try:
        from transformers import MarianMTModel, MarianTokenizer
    except Exception:
        return None, None
    model_name = "Helsinki-NLP/opus-mt-en-ur"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model


def translate_en_to_ur_local(text: str) -> str:
    tokenizer, model = _load_model()
    if tokenizer is None or model is None:
        return text
    tokens = tokenizer([text], return_tensors="pt", truncation=True, padding=True)
    generated = model.generate(**tokens, max_new_tokens=256)
    return tokenizer.decode(generated[0], skip_special_tokens=True)
