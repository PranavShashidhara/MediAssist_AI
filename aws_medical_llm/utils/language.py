import boto3
import logging

def translate_text(text, source_lang, target_lang):
    """
    Translate text using AWS Translate.
    Assumes internet is available.
    """
    logger = logging.getLogger('medical_app')

    try:
        logger.info(f"Translating text from {source_lang} to {target_lang}")
        translate = boto3.client(service_name='translate', region_name='us-east-1')
        result = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        return result['TranslatedText']
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # Return original text if translation fails