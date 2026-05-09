import argostranslate.package
import argostranslate.translate

def setup_argos():
    print("Initializing ArgosTranslate Package Setup...")
    
    # Update package index
    argostranslate.package.update_package_index()
    
    # Available packages
    available_packages = argostranslate.package.get_available_packages()
    
    # Required language pairs
    # hi-en, ta-en, te-en, kn-en, ml-en, mr-en, bn-en, pa-en, gu-en
    # en-hi, en-ta, en-te, en-kn, en-ml, en-mr, en-bn, en-pa, en-gu
    languages = ['hi', 'ta', 'te', 'kn', 'ml', 'mr', 'bn', 'pa', 'gu']
    
    for lang in languages:
        # Install {lang} -> en
        print(f"Installing {lang} -> en...")
        package_to_install = next(
            filter(
                lambda x: x.from_code == lang and x.to_code == 'en',
                available_packages
            )
        )
        argostranslate.package.install_from_path(package_to_install.download())
        
        # Install en -> {lang}
        print(f"Installing en -> {lang}...")
        package_to_install = next(
            filter(
                lambda x: x.from_code == 'en' and x.to_code == lang,
                available_packages
            )
        )
        argostranslate.package.install_from_path(package_to_install.download())

    print("ArgosTranslate Setup Complete!")

if __name__ == "__main__":
    setup_argos()
