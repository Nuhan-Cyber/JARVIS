import translators as ts
import sys

def translate_text_cli():
    """
    A command-line interface for translating text using the 'translators' library.
    """
    print("--- Python Language Translator ---")
    print("Translates text using public translation services. No API key required.")
    print("Type 'exit' at any time to quit the program.\n")

    # A simple list of common language codes for user reference
    print("Common language codes:")
    print("en: English, es: Spanish, fr: French, de: German, hi: Hindi, bn: Bengali, ja: Japanese\n")

    while True:
        try:
            # 1. Get the text to translate from the user
            text_to_translate = input("Enter text to translate: ")
            if text_to_translate.lower() == 'exit':
                print("Exiting translator. Goodbye!")
                break
            if not text_to_translate.strip():
                print("Please enter some text.")
                continue

            # 2. Get the target language from the user
            target_language = input(f"Translate '{text_to_translate[:30]}...' to (e.g., 'es'): ")
            if target_language.lower() == 'exit':
                print("Exiting translator. Goodbye!")
                break
            if not target_language.strip():
                print("Please enter a target language code.")
                continue
            
            print("\nTranslating...")

            # 3. Perform the translation using the Bing Translate service.
            # The library handles the request without a key. Bing is often more stable
            # than the Google endpoint for this library.
            translated_text = ts.translate_text(
                query_text=text_to_translate,
                translator='bing', # Changed from 'google' to 'bing' for better reliability
                to_language=target_language
            )

            # 4. Display the result
            print("-" * 25)
            print(f"Original:    {text_to_translate}")
            print(f"Translated:  {translated_text}")
            print("-" * 25 + "\n")

        except Exception as e:
            # Handle potential errors, like invalid language codes or network issues
            print(f"\n[!] An error occurred: {e}", file=sys.stderr)
            print("[!] Please check your language code and internet connection.\n")


if __name__ == "__main__":
    # Check if the library is installed before running
    try:
        import translators
    except ImportError:
        print("[ERROR] The 'translators' library is not found.", file=sys.stderr)
        print("Please install it first by running this command in your terminal:", file=sys.stderr)
        print("\npip install translators\n", file=sys.stderr)
        sys.exit(1)
    
    translate_text_cli()
