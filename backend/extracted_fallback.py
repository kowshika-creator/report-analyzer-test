def run_local_chatbot_fallback(query: str, metrics: list, tone: str = "Empathetic", language: str = "English") -> str:
    """
    Intelligent local rule-based medical fallback chat processor.
    Inspects queries contextually and generates tailored, comforting medical advice
    reflecting the patient's actual SQLite database compared blood metrics,
    dynamically shifting its language and structures based on selected_tone and preferred language.
    """
    q = query.lower()
    raw_tone = (tone or "Empathetic").strip().lower()
    if "clinical" in raw_tone:
        tone_str = "clinical"
    elif "educational" in raw_tone:
        tone_str = "educational"
    elif "family" in raw_tone:
        tone_str = "family"
    else:
        tone_str = "empathetic"
    
    lang = (language or "English").strip().lower()
    
    # Map metrics for quick lookup
    val_map = {m.biomarker_name.lower(): m for m in metrics}
    
    response_text = ""
    
    # 1. Hemoglobin / RBC / Anemia / Fatigue questions
    if any(k in q for k in ["hemoglobin", "anemia", "fatigue", "tired", "weak", "hb", "hgb", "blood", "சோர்வு", "இரத்தம்", "அணு", "थकान", "कमजोरी", "खून", "రక్త", "అలసట", "నీరసం"]):
        if "hemoglobin" in val_map:
            hb = val_map["hemoglobin"]
            if hb.status.lower() == "low":
                if lang == "tamil":
                    if tone_str == "clinical":
                        response_text = (
                            f"• கண்டறியும் குறிகாட்டி: ஹீமோகுளோபின் குறைவு ({hb.value} g/dL). சாதாரண வரம்புகள்: {hb.min_normal} - {hb.max_normal} {hb.unit}.\n"
                            "• நோய்க்கூறியல்: சிவப்பு இரத்த அணுக்களின் குறைபாடு ஆக்ஸிஜன் விநியோகத்தை கட்டுப்படுத்துகிறது.\n"
                            "• பரிந்துரைகள்: இரும்புச்சத்து நிறைந்த உணவுகள் (கீரை, புரதங்கள்). மருத்துவரை அணுகவும்."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"உங்கள் ஹீமோகுளோபின் அளவு {hb.value} g/dL ஆகும், இது சாதாரண வரம்பான {hb.min_normal} - {hb.max_normal} {hb.unit} ஐ விடக் குறைவு. "
                            "உயிரியல் வழிமுறை: ஹீமோகுளோபின் என்பது உங்கள் இரத்த அணுக்களுக்குள் இருக்கும் இரும்புச்சத்து புரதமாகும். "
                            "சிவப்பு இரத்த அணுக்களை உடலின் விநியோக லாரிகளாக நினைத்துப் பாருங்கள். இது நுரையீரலில் இருந்து ஆக்ஸிஜனை உடலின் மற்ற பகுதிகளுக்கு கொண்டு செல்கிறது. "
                            "இது குறைவாக இருக்கும்போது, உங்கள் தசைகளுக்கு ஆக்ஸிஜன் விநியோகம் குறைகிறது, இதனால் சோர்வு ஏற்படுகிறது."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"உங்கள் இரத்த அணுக்களின் ஆற்றல் அளவு {hb.value} g/dL ஆக சற்று குறைவாக உள்ளது (நாம் {hb.min_normal} முதல் {hb.max_normal} வரை பார்க்க விரும்புகிறோம்). "
                            "உங்கள் சிவப்பு இரத்த அணுக்களை காற்று நிரப்பப்பட்ட சிறிய பலூன்களாக நினைத்துப் பாருங்கள். "
                            "இப்போது உங்கள் பலூன்களில் காற்று குறைவாக இருப்பதால், உடல் சோர்வாக உணர்கிறது. கீரை, முட்டைக்கோஸ் சாப்பிடுவது பலூன்களுக்கு சூப்பர் பூஸ்டர் கொடுக்கும்!"
                        )
                    else: # empathetic
                        response_text = (
                            f"உங்கள் ஹீமோகுளோபின் அளவு தற்போது {hb.value} g/dL ஆக உள்ளது, இது சாதாரண வரம்பான ({hb.min_normal} - {hb.max_normal} {hb.unit}) ஐ விடக் குறைவாகும். "
                            "ஹீமோகுளோபின் ஆக்ஸிஜனை உடலுக்குக் கொண்டு செல்வதற்குப் பொறுப்பானது. இது குறைவாக இருக்கும்போது சோர்வு அல்லது பலவீனம் ஏற்படலாம். "
                            "கீரை, பருப்பு வகைகள், இரும்புச்சத்து நிறைந்த உணவுகளை உண்பது நல்லது. மருத்துவரை அணுகி ஆலோசனை பெற பரிந்துரைக்கிறோம்."
                        )
                elif lang == "hindi":
                    if tone_str == "clinical":
                        response_text = (
                            f"• नैदानिक संकेतक: हीमोग्लोबिन कम ({hb.value} g/dL)। सामान्य सीमा: {hb.min_normal} - {hb.max_normal} {hb.unit}।\n"
                            "• रोगजनन: लाल रक्त कोशिकाओं की कमी ऑक्सीजन परिवहन को सीमित करती है।\n"
                            "• सिफारिशें: आयरन युक्त आहार (पालक, प्रोटीन)। चिकित्सक से परामर्श करें।"
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"आपका हीमोग्लोबिन स्तर {hb.value} g/dL है, जो सामान्य सीमा {hb.min_normal} - {hb.max_normal} {hb.unit} से कम है। "
                            "जैविक तंत्र: हीमोग्लोबिन लाल रक्त कोशिकाओं में पाया जाने वाला एक आयरन युक्त प्रोटीन है जो फेफड़ों से शरीर के अन्य भागों में ऑक्सीजन ले जाता है। "
                            "लाल रक्त कोशिकाओं को डिलीवरी ट्रक समझें। हीमोग्लोबिन ऑक्सीजन का वहन करता है। इसके कम होने से अंगों को ऑक्सीजन कम मिलती है, जिससे थकान महसूस होती है।"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"आपकी लाल रक्त कोशिकाओं का ऊर्जा स्तर {hb.value} g/dL थोड़ा कम है (हम इसे {hb.min_normal} और {hb.max_normal} के बीच देखना चाहते हैं)। "
                            "अपनी लाल रक्त कोशिकाओं को हवा से भरे छोटे गुब्बारे समझें। "
                            "अभी आपके गुब्बारे कम हवा ले जा रहे हैं, इसलिए शरीर को थोड़ी थकान महसूस हो रही है। पालक और हरी सब्जियां खाना गुब्बारों को सुपर-बूस्टर देगा!"
                        )
                    else: # empathetic
                        response_text = (
                            f"आपका हीमोग्लोबिन स्तर वर्तमान में {hb.value} g/dL है, जो सामान्य सीमा ({hb.min_normal} - {hb.max_normal} {hb.unit}) से कम है। "
                            "हीमोग्लोबिन पूरे शरीर में ऑक्सीजन ले जाने का काम करता है। इसके कम होने से थकान या कमजोरी महसूस हो सकती है। "
                            "अपने आहार में पालक, दालें और आयरन से भरपूर चीजें शामिल करें। हम डॉक्टर से परामर्श करने की सलाह देते हैं।"
                        )
                elif lang == "telugu":
                    if tone_str == "clinical":
                        response_text = (
                            f"• విశ్లేషణ సూచిక: హిమోగ్లోబిన్ తక్కువ ({hb.value} g/dL). సాధారణ పరిధి: {hb.min_normal} - {hb.max_normal} {hb.unit}.\n"
                            "• పాథోఫిజియాలజీ: ఎర్ర రక్త కణాల కొరత ఆక్సిజన్ రవాణాను పరిమితం చేస్తుంది.\n"
                            "• సిఫార్సులు: ఇనుము అధికంగా ఉండే ఆహారం (పాలకూర, ప్రోటీన్లు). వైద్యుడిని సంప్రదించండి."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"మీ హిమోగ్లోబిన్ స్థాయి {hb.value} g/dL, ఇది సాధారణ పరిధి {hb.min_normal} - {hb.max_normal} {hb.unit} కంటే తక్కువ. "
                            "జీవక్రియ విధానం: హిమోగ్లోబిన్ అనేది ఎర్ర రక్త కణాలలో ఉండే ఇనుముతో కూడిన ప్రోటీన్. "
                            "ఎర్ర రక్త కణాలను శరీర రవాణా ట్రక్కులుగా భావించండి. ఇది ఊపిరితిత్తుల నుండి శరీర భాగాలకు ఆక్సిజన్‌ను మోసుకెళుతుంది. "
                            "ఇది తక్కువగా ఉన్నప్పుడు శరీరానికి ఆక్సిజన్ అందక అలసట కలుగుతుంది."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"మీ ఎర్ర రక్త కణాల శక్తి స్థాయి {hb.value} g/dL కొద్దిగా తక్కువగా ఉంది (మనం దీనిని {hb.min_normal} మరియు {hb.max_normal} మధ్య చూడాలనుకుంటున్నాము). "
                            "మీ ఎర్ర రక్త కణాలను గాలితో కూడిన బుడగలుగా భావించండి. "
                            "ఇప్పుడు బుడగలలో గాలి తక్కువగా ఉండటం వల్ల శరీరం అలసిపోయినట్లు అనిపిస్తుంది. పాలకూర, పప్పులు తినడం వల్ల ఈ బుడగలకు సూపర్ బూస్టర్ లభిస్తుంది!"
                        )
                    else: # empathetic
                        response_text = (
                            f"మీ హిమోగ్లోబిన్ స్థాయి ప్రస్తుతం {hb.value} g/dL గా ఉంది, ఇది సాధారణ పరిధి ({hb.min_normal} - {hb.max_normal} {hb.unit}) కంటే తక్కువ. "
                            "హిమోగ్లోబిన్ ఆక్సిజన్‌ను రవాణా చేయడానికి ఉపయోగపడుతుంది. ఇది తక్కువగా ఉన్నప్పుడు అలసట లేదా నీరసంగా అనిపించడం సహజం. "
                            "పాలకూర, పప్పులు మరియు ఆకుకూరలు ఎక్కువగా తీసుకోండి. వైద్యుడిని సంప్రదించి సలహా తీసుకోండి."
                        )
                else: # English
                    if tone_str == "clinical":
                        response_text = (
                            f"• Diagnostic Indicator: Hemoglobin low ({hb.value} g/dL). Standard limits: {hb.min_normal} - {hb.max_normal} {hb.unit}.\n"
                            "• Pathophysiology: Reduced red blood cell count limits oxygen transport capacities.\n"
                            "• Recommendations: Iron-dense dietary modifications (spinach, proteins). Coordinate serum ferritin panels with provider."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"Your Hemoglobin level is {hb.value} g/dL, which is below the optimal range of {hb.min_normal} - {hb.max_normal} {hb.unit}. "
                            "Biological Mechanism: Hemoglobin is a complex iron-containing protein housed within your red blood cells. "
                            "Think of red blood cells as delivery trucks. Hemoglobin acts as the cargo boxes carrying oxygen from lungs to muscles. "
                            "Low hemoglobin means the delivery trucks are leaving half-empty, leading to tissue lethargy and muscle weakness."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"Your red blood cell energy levels are a bit low at {hb.value} g/dL (we like to see it between {hb.min_normal} and {hb.max_normal}). "
                            "Think of your red blood cells as little balloons carrying bubbles of fresh air. "
                            "Right now, your balloons are carrying fewer bubbles, making your body feel a bit sleepy. "
                            "Eating spinach, leafy greens, or beans gives your balloons a super-booster!"
                        )
                    else: # empathetic
                        response_text = (
                            f"Your Hemoglobin level is currently {hb.value} g/dL, which is below the optimal reference boundary "
                            f"({hb.min_normal} - {hb.max_normal} {hb.unit}). Hemoglobin is responsible for distributing oxygen to your body's cells. "
                            "Being in a lower range can definitely cause feelings of tiredness and fatigue. "
                            "Focusing on iron-rich foods like spinach, lentils, and lean proteins is a comforting way to support your body. We recommend speaking with your doctor!"
                        )
            else:
                if lang == "tamil":
                    response_text = "உங்கள் ஹீமோகுளோபின் அளவுகள் முழுமையாக சாதாரணமாக உள்ளன. ஆரோக்கியமான உணவை உட்கொள்வதை தொடரவும்."
                elif lang == "hindi":
                    response_text = "आपका हीमोग्लोबिन स्तर पूरी तरह से सामान्य है। स्वस्थ और संतुलित आहार जारी रखें।"
                elif lang == "telugu":
                    response_text = "మీ హిమోగ్లోబిన్ స్థాయిలు పూర్తిగా సాధారణంగా ఉన్నాయి. సమతుల్య ఆహారం తీసుకోవడం కొనసాగించండి."
                else:
                    response_text = "Your Hemoglobin levels are completely normal. Continue enjoying a balanced nutrient-dense diet to support your red blood cells."
        else:
            if lang == "tamil":
                response_text = "ஹீமோகுளோபின் ஆக்ஸிஜனை உடலுக்குக் கொண்டு செல்வதற்குப் பொறுப்பானது. இது குறைவாக இருக்கும்போது சோர்வு ஏற்படலாம். இரும்புச்சத்து நிறைந்த உணவுகளை உட்கொள்ளவும்."
            elif lang == "hindi":
                response_text = "हीमोग्लोबिन ऑक्सीजन ले जाने का काम करता है। इसके कम होने से थकान हो सकती है। आयरन से भरपूर भोजन लें।"
            elif lang == "telugu":
                response_text = "హిమోగ్లోబిన్ ఆక్సిజన్‌ను రవాణా చేయడానికి ఉపయోగపడుతుంది. ఇది తక్కువగా ఉన్నప్పుడు అలసట కలుగుతుంది. ఇనుము అధికంగా ఉండే ఆహారం తీసుకోండి."
            else:
                response_text = "Hemoglobin distributes oxygen. Lower limits can trigger fatigue. Try iron-rich leafy foods and align with your doctor for clinical advice."

    # 2. Blood Sugar / Diabetes / Glucose / FBS questions
    elif any(k in q for k in ["sugar", "diabetes", "glucose", "fasting", "fbs", "sugar level", "hba1c", "சர்க்கரை", "நீரிழிவு", "சுகர்", "मधुमेह", "चीनी", "ग्लूकोज", "చక్కెర", "మధుమేహం", "గ్లూకోజ్"]):
        if "fasting" in val_map:
            fasting = val_map["fasting"]
            if fasting.status.lower() == "high":
                hba1c_str = ""
                if "hba1c" in val_map:
                    if lang == "tamil":
                        hba1c_str = f" மற்றும் உங்கள் HbA1c {val_map['hba1c'].value}% ஆகும்"
                    elif lang == "hindi":
                        hba1c_str = f" और आपका HbA1c {val_map['hba1c'].value}% है"
                    elif lang == "telugu":
                        hba1c_str = f" మరియు మీ HbA1c {val_map['hba1c'].value}% ఉంది"
                    else:
                        hba1c_str = f" and your HbA1c is {val_map['hba1c'].value}%"
                
                if lang == "tamil":
                    if tone_str == "clinical":
                        response_text = (
                            f"• கண்டறியும் குறிகாட்டி: உண்ணாவிரத இரத்த சர்க்கரை அதிகம் ({fasting.value} mg/dL){hba1c_str}. சாதாரண வரம்புகள்: {fasting.min_normal} - {fasting.max_normal} {fasting.unit}.\n"
                            "• நோய்க்கூறியல்: இன்சுலின் எதிர்ப்பைக் குறிக்கும் குளுக்கோஸ் அதிகரிப்பு.\n"
                            "• பரிந்துரைகள்: சுத்திகரிக்கப்பட்ட சர்க்கரைகளைக் குறைக்கவும். தினசரி உடற்பயிற்சி மற்றும் வேகமாக நடப்பது நல்லது."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"உங்கள் உண்ணாவிரத இரத்த சர்க்கரை அளவு {fasting.value} mg/dL ஆகும், இது சாதாரண வரம்பான {fasting.min_normal} - {fasting.max_normal} {fasting.unit} ஐ விட அதிகம்{hba1c_str}. "
                            "உயிரியல் வழிமுறை: நாம் உண்ணும் கார்போஹைட்ரேட்டுகள் குளுக்கோஸாக மாறுகின்றன. கணையம் இன்சுலினை வெளியிடுகிறது, இது செல்களின் கதவுகளைத் திறக்கும் சாவியாகும். "
                            "சர்க்கரை அதிகமாக இருக்கும்போது, செல்களின் பூட்டுகள் துருப்பிடித்தது போல் மாறும் (இன்சுலின் எதிர்ப்பு). தினசரி வேகமாக நடப்பது சாவிகள் இல்லாமலேயே கதவுகளைத் திறக்க உதவும்!"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"உங்கள் காலை சர்க்கரை அளவு சற்று அதிகமாக உள்ளது ({fasting.value} mg/dL, இலக்கு {fasting.min_normal} மற்றும் {fasting.max_normal} ஆகும்). "
                            "சர்க்கரையை உடலின் சிறிய ஆற்றல் நாணயங்களாக நினைத்துப் பாருங்கள். தற்போது உங்கள் இரத்தத்தில் ஆற்றல் நாணயங்கள் அதிகமாக உள்ளன. "
                            "இனிப்பு பண்டங்களைக் குறைப்பதும், தினமும் நடப்பதும் இந்த நாணயங்களை சேமிக்க உதவும்!"
                        )
                    else: # empathetic
                        response_text = (
                            f"உங்கள் உண்ணாவிரத இரத்த சர்க்கரை அளவு {fasting.value} mg/dL ஆக உள்ளது, இது சாதாரண வரம்பான ({fasting.min_normal} - {fasting.max_normal} {fasting.unit}) ஐ விட அதிகம்{hba1c_str}. "
                            "உயர்த்தப்பட்ட குளுக்கோஸ் இன்சுலின் எதிர்ப்பைக் குறிக்கலாம். அதிக நார்ச்சத்துள்ள உணவுகளை உட்கொள்வது மற்றும் தினமும் வேகமாக நடப்பது சர்க்கரை அளவை சீராக்க உதவும். மருத்துவரை அணுகவும்."
                        )
                elif lang == "hindi":
                    if tone_str == "clinical":
                        response_text = (
                            f"• नैदानिक संकेतक: खाली पेट रक्त शर्करा अधिक ({fasting.value} mg/dL){hba1c_str}। सामान्य सीमा: {fasting.min_normal} - {fasting.max_normal} {fasting.unit}।\n"
                            "• रोगजनन: इंसुलिन प्रतिरोध के कारण रक्त में ग्लूकोज की अधिकता।\n"
                            "• सिफारिशें: मीठा और प्रसंस्कृत कार्ब्स कम करें। दैनिक सैर करें और डॉक्टर से परामर्श करें।"
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"आपका खाली पेट का शुगर स्तर {fasting.value} mg/dL है, जो सामान्य सीमा {fasting.min_normal} - {fasting.max_normal} {fasting.unit} से अधिक है{hba1c_str}। "
                            "जैविक तंत्र: भोजन से कार्बोहाइड्रेट ग्लूकोज में बदलता है। अग्न्याशय इंसुलिन जारी करता है जो कोशिकाओं के दरवाजों की चाबी है। "
                            "शुगर बढ़ने पर कोशिका के ताले बंद हो जाते हैं (इंसुलिन प्रतिरोध)। ब्रिस्क वॉक करने से कोशिकाओं के द्वार चाबी के बिना भी खुल जाते हैं!"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"सुबह का शुगर स्तर थोड़ा बढ़ा हुआ है ({fasting.value} mg/dL, आदर्श सीमा {fasting.min_normal} और {fasting.max_normal} है)। "
                            "शुगर को शरीर के ऊर्जा के छोटे सिक्के समझें। अभी खून में ऊर्जा के सिक्के ज्यादा तैर रहे हैं। "
                            "मीठा कम खाने और टहलने से शरीर इन सिक्कों को कोशिकाओं में आसानी से जमा कर लेता है!"
                        )
                    else: # empathetic
                        response_text = (
                            f"आपका खाली पेट रक्त शर्करा स्तर {fasting.value} mg/dL है, जो सामान्य सीमा ({fasting.min_normal} - {fasting.max_normal} {fasting.unit}) से अधिक है{hba1c_str}। "
                            "यह इंगित करता है कि कोशिकाएं इंसुलिन का प्रतिरोध कर रही हैं (प्रीडायबिटिक जोखिम)। "
                            "आहार में फाइबर बढ़ाना, मीठा कम करना और दैनिक सैर करना बहुत प्रभावी उपाय हैं। डॉक्टर से परामर्श करें।"
                        )
                elif lang == "telugu":
                    if tone_str == "clinical":
                        response_text = (
                            f"• విశ్లేషణ సూచిక: ఖాళీ కడుపుతో రక్తంలో చక్కెర ఎక్కువ ({fasting.value} mg/dL){hba1c_str}. సాధారణ పరిధి: {fasting.min_normal} - {fasting.max_normal} {fasting.unit}.\n"
                            "• పాథోఫిజియాలజీ: ఇన్సులిన్ నిరోధకత వల్ల రక్తంలో గ్లూకోజ్ పెరగడం.\n"
                            "• సిఫార్సులు: తీపి పదార్థాలు తగ్గించండి. ప్రతిరోజు వ్యాయామం లేదా నడక అలవాటు చేసుకోండి."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"మీ ఖాళీ కడుపుతో చక్కెర స్థాయి {fasting.value} mg/dL గా ఉంది, ఇది సాధారణ పరిధి {fasting.min_normal} - {fasting.max_normal} {fasting.unit} కంటే ఎక్కువ{hba1c_str}. "
                            "జీవక్రియ విధానం: మనం తినే ఆహారం గ్లూకోజ్ గా మారుతుంది. క్లోమం ఇన్సులిన్‌ను విడుదల చేస్తుంది, ఇది కణాల తలుపులు తెరిచే తాళంచెవి. "
                            "చక్కెర పెరిగినప్పుడు కణాల తాళాలు పనిచేయవు (ఇన్సులిన్ నిరోధకత). ప్రతిరోజూ నడవడం వల్ల తాళంచెవి లేకుండానే కణాల తలుపులు తెరుచుకుంటాయి!"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"మీ ఉదయం చక్కెర స్థాయి కొద్దిగా ఎక్కువగా ఉంది ({fasting.value} mg/dL, సాధారణ పరిధి {fasting.min_normal} మరియు {fasting.max_normal}). "
                            "చక్కెరను శరీరంలో ఉండే చిన్న శక్తి నాణేలుగా భావించండి. ఇప్పుడు రక్తంలో ఈ నాణేలు ఎక్కువగా ఉన్నాయి. "
                            "తీపి తగ్గించి, నడక అలవాటు చేసుకోవడం వల్ల ఈ నాణేలను కణాల జేబులలో దాచుకోవచ్చు!"
                        )
                    else: # empathetic
                        response_text = (
                            f"మీ ఖాళీ కడుపుతో రక్తంలో చక్కెర స్థాయి {fasting.value} mg/dL గా ఉంది, ఇది సాధారణ పరిధి ({fasting.min_normal} - {fasting.max_normal} {fasting.unit}) కంటే ఎక్కువ{hba1c_str}. "
                            "ఇది ఇన్సులిన్ నిరోధకతను (ప్రీడయాబెటిక్ ప్రమాదం) సూచిస్తుంది. "
                            "పీచు పదార్థాలు ఎక్కువగా తీసుకోవడం, తీపి తగ్గించడం మరియు రోజువారీ నడక ద్వారా దీనిని నియంత్రించవచ్చు. వైద్యుడిని సంప్రదించండి."
                        )
                else: # English
                    if tone_str == "clinical":
                        response_text = (
                            f"• Diagnostic Indicator: Fasting Blood Sugar high ({fasting.value} mg/dL){hba1c_str}. Standard limits: {fasting.min_normal} - {fasting.max_normal} {fasting.unit}.\n"
                            "• Pathophysiology: Impaired cellular glucose uptake reflecting elevated baseline insulin resistance.\n"
                            "• Recommendations: Restrict processed carbohydrates and refined sugars. Implement post-prandial aerobic steps (20 brisk walk). Consult primary care provider."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"Your Fasting Blood Sugar is currently {fasting.value} mg/dL, which is elevated compared to the optimal range of {fasting.min_normal} - {fasting.max_normal} {fasting.unit}{hba1c_str}. "
                            "Biological Mechanism: When you eat carbs, they break down into glucose. Your pancreas releases insulin, which acts as a molecular key to cell doors. When glucose is high, it is as if the keyholes on cells are clogged (insulin resistance). Walking activates insulin-independent GLUT4 receptors, opening doors without keys!"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"Your morning sugar levels are a bit high at {fasting.value} mg/dL (the target is between {fasting.min_normal} and {fasting.max_normal}). "
                            "Think of sugar as little energy-coins. Right now, there are too many energy-coins floating in your blood. Eating less sweet treats and taking active walks outside helps your body open its pocket-cells and save those energy-coins!"
                        )
                    else: # empathetic
                        response_text = (
                            f"Your Fasting Blood Sugar is currently {fasting.value} mg/dL, which is elevated compared to optimal bounds ({fasting.min_normal} - {fasting.max_normal} {fasting.unit}){hba1c_str}. Elevated fasting glucose suggests that cells might be resisting insulin absorption, representing a prediabetic risk. Shifting towards high-fiber foods, reducing processed sugars, and adding a daily brisk walk does wonders."
                        )
            else:
                if lang == "tamil":
                    response_text = "உங்கள் இரத்த சர்க்கரை அளவு முழுமையாக சாதாரணமாக உள்ளது. ஆரோக்கியமான உணவு முறையை தொடரவும்."
                elif lang == "hindi":
                    response_text = "आपका शुगर स्तर सामान्य है। स्वस्थ आदतों को बनाए रखें।"
                elif lang == "telugu":
                    response_text = "మీ చక్కెర స్థాయి సాధారణంగా ఉంది. ఆరోగ్యకరమైన జీవనశైలిని కొనసాగించండి."
                else:
                    response_text = "Your Fasting Blood Sugar level of {fasting.value} mg/dL is completely normal. Keep up the great health habits!"
        else:
            if lang == "tamil":
                response_text = "உண்ணாவிரத இரத்த சர்க்கரை என்பது காலையில் உணவருந்துவதற்கு முன் அளவிடப்படும் சர்க்கரை ஆகும். இது 100 mg/dL க்குள் இருக்க வேண்டும்."
            elif lang == "hindi":
                response_text = "खाली पेट रक्त शर्करा का स्तर सामान्यतः 100 mg/dL से कम होना चाहिए। संतुलित भोजन लें।"
            elif lang == "telugu":
                response_text = "ఖాళీ కడుపుతో రక్తంలో గ్లూకోజ్ సాధారణంగా 100 mg/dL కంటే తక్కువ ఉండాలి. ఆరోగ్యకరమైన ఆహారం తీసుకోండి."
            else:
                response_text = "Normal fasting blood sugar should be below 100 mg/dL. Soluble fiber diets and daily walks help maintain healthy balances."

    # 3. Cholesterol / Triglycerides / Lipids questions
    elif any(k in q for k in ["cholesterol", "lipid", "triglyceride", "hdl", "ldl", "fat", "கொழுப்பு", "கொலஸ்ட்ரால்", "वसा", "कोलेस्ट्रॉल", "లిపిడ్", "కొలెస్ట్రాల్"]):
        if "total cholesterol" in val_map:
            chol = val_map["total cholesterol"]
            if chol.status.lower() == "high":
                if lang == "tamil":
                    if tone_str == "clinical":
                        response_text = (
                            f"• கண்டறியும் குறிகாட்டி: மொத்த கொழுப்பு அதிகம் ({chol.value} mg/dL). சாதாரண வரம்புகள்: {chol.min_normal} - {hb.max_normal if 'hb' in locals() else 200.0} {chol.unit}.\n"
                            "• நோய்க்கூறியல்: எல்.டி.எல் (LDL) மற்றும் முச்சீரினக் கொழுப்புகள் இரத்த நாளங்களில் படிதல்.\n"
                            "• பரிந்துரைகள்: நார்ச்சத்துள்ள உணவுகள், ஓட்ஸ் மற்றும் தானியங்கள் உட்கொள்ளவும். தாவர எண்ணெய் மற்றும் நல்ல கொழுப்புகளை சேர்க்கவும்."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"உங்கள் மொத்த கொழுப்பு அளவு {chol.value} mg/dL ஆகும், இது சாதாரண வரம்பான {chol.min_normal} - {chol.max_normal} {chol.unit} ஐ விட அதிகம். "
                            "உயிரியல் வழிமுறை: கொழுப்பு என்பது இரத்தத்தில் மிதக்கும் மெழுகு போன்ற கொழுப்புப் பொருளாகும். எல்.டி.எல் (LDL) என்பது வீடுகளுக்கு செங்கற்களைக் கொண்டு செல்லும் லாரிகளைப் போன்றது. "
                            "ஹெச்.டி.எல் (HDL) என்பது தேவையற்ற செங்கற்களை சுத்தம் செய்யும் குப்பை லாரிகளைப் போன்றது. கொழுப்பு அதிகமாகும்போது சுத்தம் செய்யும் லாரிகள் பற்றாக்குறையாகி, இரத்த நாளங்களில் அடைப்பு ஏற்படும்."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"உங்கள் உடலின் கொழுப்புகள் சற்று அதிகமாக உள்ளன ({chol.value} mg/dL, சாதாரண அளவு {chol.min_normal} முதல் {chol.max_normal} வரை). "
                            "கொழுப்பை உடலை உருவாக்கும் சிறிய செங்கற்களாக நினைத்துப் பாருங்கள். இப்போது இரத்த நாளங்களில் கூடுதல் செங்கற்கள் உள்ளன. "
                            "ஓட்ஸ், ஆப்பிள் மற்றும் கொட்டைகள் சாப்பிடுவது சிறிய வெற்றிட கிளீனரைப் போல செயல்பட்டு இரத்த நாளங்களை சுத்தம் செய்யும்!"
                        )
                    else: # empathetic
                        response_text = (
                            f"உங்கள் மொத்த கொழுப்பு அளவு {chol.value} mg/dL ஆக உள்ளது, இது சாதாரண வரம்பான ({chol.min_normal} - {chol.max_normal} {chol.unit}) ஐ விட அதிகம். "
                            "அதிகரித்த கொழுப்பு இரத்த நாளங்களில் படிந்து இதய ஆரோக்கியத்தை பாதிக்கலாம். ஓட்ஸ், நார்ச்சத்துக்கள் மற்றும் ஆரோக்கியமான கொழுப்புகளை உணவில் சேர்க்கவும். மருத்துவர் ஆலோசனை பெறவும்."
                        )
                elif lang == "hindi":
                    if tone_str == "clinical":
                        response_text = (
                            f"• नैदानिक संकेतक: कुल कोलेस्ट्रॉल उच्च ({chol.value} mg/dL)। सामान्य सीमा: {chol.min_normal} - {chol.max_normal} {chol.unit}।\n"
                            "• रोगजनन: एलडीएल (LDL) और ट्राइग्लिसराइड्स का बढ़ा हुआ स्तर हृदय रोगों के खतरे को बढ़ाता है।\n"
                            "• सिफारिशें: घुलनशील फाइबर (ओट्स, बीज) का सेवन बढ़ाएं। हृदय स्वास्थ्य की जांच कराएं।"
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"आपका कुल कोलेस्ट्रॉल {chol.value} mg/dL है, जो सामान्य सीमा ({chol.min_normal} - {chol.max_normal} {chol.unit}) से अधिक है। "
                            "जैविक तंत्र: कोलेस्ट्रॉल एक वसायुक्त पदार्थ है। एलडीएल (LDL) को ईंट (वसा) पहुंचाने वाला डिलीवरी ट्रक समझें। "
                            "एचडीएल (HDL) कचरा उठाने वाला ट्रक है जो अतिरिक्त वसा को लीवर में लाता है। कोलेस्ट्रॉल बढ़ने पर धमनियों में वसा जमा होने लगती है। ओट्स खाने से यह साफ होता है।"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"शरीर में वसा का स्तर थोड़ा बढ़ा हुआ है ({chol.value} mg/dL, सामान्य सीमा {chol.min_normal} से {chol.max_normal} है)। "
                            "कोलेस्ट्रॉल को छोटे ब्लॉक्स समझें। अभी खून में जरूरत से ज्यादा ब्लॉक्स तैर रहे हैं। "
                            "ओट्स और फल खाना एक छोटे वैक्यूम क्लीनर की तरह काम करता है जो इन अतिरिक्त ब्लॉक्स को साफ कर देता है!"
                        )
                    else: # empathetic
                        response_text = (
                            f"आपका कुल कोलेस्ट्रॉल {chol.value} mg/dL है, जो सामान्य सीमा ({chol.min_normal} - {chol.max_normal} {chol.unit}) से अधिक है। "
                            "उच्च कोलेस्ट्रॉल रक्त में वसा की अधिकता को दर्शाता है। हृदय के अनुकूल वसा (नट्स, जैतून का तेल), ओट्स और दैनिक व्यायाम को शामिल करें। डॉक्टर से सलाह लें।"
                        )
                elif lang == "telugu":
                    if tone_str == "clinical":
                        response_text = (
                            f"• విశ్లేషణ సూచిక: మొత్తం కొలెస్ట్రాల్ ఎక్కువ ({chol.value} mg/dL). సాధారణ పరిధి: {chol.min_normal} - {chol.max_normal} {chol.unit}.\n"
                            "• పాథోఫిజియాలజీ: రక్తనాళాలలో ఎల్.డి.ఎల్ (LDL) మరియు కొవ్వులు పేరుకుపోవడం.\n"
                            "• సిఫార్సులు: పీచు పదార్థాలు (ఓట్స్, గింజలు) తీసుకోండి. సమతుల్య ఆహారం పాటించండి."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"మీ మొత్తం కొలెస్ట్రాల్ స్థాయి {chol.value} mg/dL గా ఉంది, ఇది సాధారణ పరిధి ({chol.min_normal} - {chol.max_normal} {chol.unit}) కంటే ఎక్కువ. "
                            "జీవక్రియ విధానం: కొలెస్ట్రాల్ అనేది కొవ్వు పదార్థం. ఎల్.డి.ఎల్ (LDL) కణాలకు కొవ్వును చేర్చే ట్రక్కుల వంటిది. "
                            "హెచ్.డి.ఎల్ (HDL) అదనపు కొవ్వును కాలేయానికి చేర్చే రీసైక్లింగ్ ట్రక్కుల వంటిది. కొలెస్ట్రాల్ పెరిగినప్పుడు రక్తనాళాలలో కొవ్వు పేరుకుపోతుంది."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"మీ శరీరంలో కొవ్వులు కొద్దిగా ఎక్కువగా ఉన్నాయి ({chol.value} mg/dL, సాధారణ పరిధి {chol.min_normal} నుండి {chol.max_normal}). "
                            "కొలెస్ట్రాల్ ను శరీరం నిర్మించే చిన్న ఇటుకలుగా భావించండి. ఇప్పుడు రక్తంలో కొవ్వు ఇటుకలు ఎక్కువగా ఉన్నాయి. "
                            "ఓట్స్, ఆపిల్స్ తినడం వల్ల ఈ అదనపు ఇటుకలను వ్యాక్యూమ్ క్లీనర్ లా శుభ్రం చేయవచ్చు!"
                        )
                    else: # empathetic
                        response_text = (
                            f"మీ మొత్తం కొలెస్ట్రాల్ స్థాయి {chol.value} mg/dL గా ఉంది, ఇది సాధారణ పరిధి ({chol.min_normal} - {chol.max_normal} {chol.unit}) కంటే ఎక్కువ. "
                            "ఇది గుండె జబ్బుల ప్రమాదాన్ని సూచిస్తుంది. ప్రతిరోజూ వ్యాయామం, ఓట్స్, నట్స్ తీసుకోవడం ద్వారా కొలెస్ట్రాల్ ను నియంత్రించవచ్చు. వైద్యుడిని సంప్రదించండి."
                        )
                else: # English
                    if tone_str == "clinical":
                        response_text = (
                            f"• Diagnostic Indicator: Total Cholesterol high ({chol.value} mg/dL). Standard limits: {chol.min_normal} - {chol.max_normal} {chol.unit}.\n"
                            "• Recommendations: Increase dietary soluble fiber (oats, seeds). Replace saturated fats with polyunsaturated omega-3s. Discuss cardiovascular baselines with provider."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"Your Total Cholesterol is currently {chol.value} mg/dL, which is higher than the standard optimal range ({chol.min_normal} - {chol.max_normal} {chol.unit}). "
                            "Biological Mechanism: Cholesterol is waxy fat carried by lipoproteins. LDL delivery trucks bring bricks to build cellular walls, while HDL recycling trucks clear unused bricks. When cholesterol is high, bricks accumulate on arterial walls. Soluble fiber oats bind cholesterol so it can be cleared."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"Your body fats are a bit high at {chol.value} mg/dL (ideal is {chol.min_normal} to {chol.max_normal}). "
                            "Think of cholesterol as tiny building blocks. Right now, there are a few too many blocks in your blood. Eating oatmeal or apples acts like a friendly little vacuum cleaner, cleaning up the extra blocks!"
                        )
                    else: # empathetic
                        response_text = (
                            f"Your Total Cholesterol is currently {chol.value} mg/dL, which is higher than standard optimal limits ({chol.min_normal} - {chol.max_normal} {chol.unit}). Elevated cholesterol suggests higher fat concentration in the bloodstream. Focus on heart-healthy fats, oats, seeds, and aerobic activity."
                        )
            else:
                if lang == "tamil":
                    response_text = "உங்கள் கொழுப்பு அளவுகள் ஆரோக்கியமான வரம்புகளுக்குள் உள்ளன."
                elif lang == "hindi":
                    response_text = "आपका कोलेस्ट्रॉल स्तर पूरी तरह से सामान्य है।"
                elif lang == "telugu":
                    response_text = "మీ కొలెస్ట్రాల్ స్థాయిలు పూర్తిగా సాధారణంగా ఉన్నాయి."
                else:
                    response_text = "Your Total Cholesterol of {chol.value} mg/dL is normal and cardiorobust. Excellent!"
        else:
            if lang == "tamil":
                response_text = "கொழுப்பு என்பது இரத்த நாளங்களில் படியக்கூடிய மெழுகு போன்ற பொருளாகும். ஓட்ஸ் மற்றும் நார்ச்சத்துகள் இதை சீராக்க உதவும்."
            elif lang == "hindi":
                response_text = "कोलेस्ट्रॉल धमनियों में जमा होने वाला वसायुक्त पदार्थ है। स्वस्थ आहार से इसे नियंत्रित रखा जा सकता है।"
            elif lang == "telugu":
                response_text = "కొలెస్ట్రాల్ అనేది రక్తనాళాలలో పేరుకుపోయే కొవ్వు పదార్థం. పీచు ఆహారం ద్వారా దీనిని నియంత్రించవచ్చు."
            else:
                response_text = "Lipid panels track fatty metrics. Soluble fiber diets, seeds, and brisk walking are classic ways to normalize lipid levels."

    # 4. TSH / Thyroid questions
    elif any(k in q for k in ["tsh", "thyroid", "t3", "t4", "hormone", "thyroid gland", "தைராய்டு", "ஹார்மோன்", "थायरॉयड", "हार्मोन", "థైరాయిడ్", "హార్మోన్"]):
        if "tsh" in val_map:
            tsh = val_map["tsh"]
            if tsh.status.lower() == "high":
                if lang == "tamil":
                    if tone_str == "clinical":
                        response_text = (
                            f"• கண்டறியும் குறிகாட்டி: டி.எஸ்.ஹெச் (TSH) அதிகம் ({tsh.value} uIU/mL). சாதாரண வரம்புகள்: {tsh.min_normal} - {tsh.max_normal} {tsh.unit}.\n"
                            "• நோய்க்கூறியல்: தைராய்டு சுரப்பியின் செயலற்ற தன்மை (ஹைப்போதைராய்டிசம்).\n"
                            "• பரிந்துரைகள்: ஹார்மோன் பரிசோதனைகள் (FT3/FT4/TSH) மேற்கொள்ளவும். எண்டோகிரைனாலஜி மருத்துவரை அணுகவும்."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"உங்கள் டி.எஸ்.ஹெச் (TSH) அளவு {tsh.value} uIU/mL ஆகும், இது சாதாரண வரம்பான {tsh.min_normal} - {tsh.max_normal} {tsh.unit} ஐ விட அதிகம். "
                            "உயிரியல் வழிமுறை: தைராய்டு என்பது கழுத்தில் உள்ள வண்ணத்துப்பூச்சி வடிவ சுரப்பியாகும், இது உடலின் வளர்சிதை மாற்றத்தைக் கட்டுப்படுத்தும் அடுப்பாகும். "
                            "மூளையின் பிட்யூட்டரி சுரப்பி தெர்மோஸ்டாட் போன்றது. தைராய்டு சுரப்பி சரியாக செயல்படாதபோது, மூளை அதிக டி.எஸ்.ஹெச் (TSH) ஐ வெளியிட்டு அதை தூண்டுகிறது. அதிக டி.எஸ்.ஹெச் என்பது செயலற்ற தைராய்டைக் குறிக்கிறது."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"உங்கள் உடல் தெர்மோஸ்டாட் உதவியாளர் (TSH) சற்று அதிகமாக உள்ளது ({tsh.value} uIU/mL, சாதாரண அளவு {tsh.min_normal} முதல் {tsh.max_normal} வரை). "
                            "உங்கள் கழுத்தில் ஒரு சிறிய வண்ணத்துப்பூச்சி நண்பர் இருக்கிறார், அவர் உங்களை சுறுசுறுப்பாக வைத்திருப்பார். "
                            "இப்போது உங்கள் வண்ணத்துப்பூச்சி நண்பர் சற்று சோம்பலாக ஓய்வெடுப்பதால், மூளை அவரை எழுப்ப சத்தமாக கத்துகிறது! இதனால்தான் சோர்வு ஏற்படுகிறது."
                        )
                    else: # empathetic
                        response_text = (
                            f"உங்கள் டி.எஸ்.ஹெச் (TSH) அளவு தற்போது {tsh.value} uIU/mL ஆக உள்ளது, இது சாதாரண வரம்பான ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}) ஐ விட அதிகம். "
                            "அதிகரித்த டி.எஸ்.ஹெச் என்பது தைராய்டு சுரப்பியின் செயலற்ற தன்மையைக் குறிக்கலாம் (ஹைப்போதைராய்டிசம்). இது உடல் சோர்வு மற்றும் குளிர்காய்தலை ஏற்படுத்தும். எண்டோகிரைனாலஜி மருத்துவரை அணுகவும்."
                        )
                elif lang == "hindi":
                    if tone_str == "clinical":
                        response_text = (
                            f"• नैदानिक संकेतक: टीएसएच उच्च ({tsh.value} uIU/mL)। सामान्य सीमा: {tsh.min_normal} - {tsh.max_normal} {tsh.unit}।\n"
                            "• रोगजनन: थायरॉयड ग्रंथि की कम सक्रियता (हाइपोथायरायडिज्म) के कारण पिट्यूटरी द्वारा अधिक टीएसएच का स्राव।\n"
                            "• सिफारिशें: एंडोक्राइन विशेषज्ञ से मिलें और FT3/FT4 परीक्षण कराएं।"
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"आपका टीएसएच (TSH) स्तर {tsh.value} uIU/mL है, जो सामान्य सीमा ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}) से अधिक है। "
                            "जैविक तंत्र: थायरॉयड गर्दन में तितली के आकार की ग्रंथि है जो चयापचय को नियंत्रित करती है। "
                            "मस्तिष्क की पिट्यूटरी ग्रंथि थर्मोस्टेट की तरह है। जब थायरॉयड कम काम करता है, तो थर्मोस्टेट अधिक टीएसएच जारी करके थायरॉयड को अधिक काम करने के लिए प्रेरित करता है।"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"आपका शरीर थर्मोस्टेट (TSH) थोड़ा बढ़ा हुआ है ({tsh.value} uIU/mL, सामान्य सीमा {tsh.min_normal} से {tsh.max_normal} है)। "
                            "आपकी गर्दन में एक प्यारी तितली जैसी सहायक ग्रंथि है जो आपको ऊर्जा देती है। "
                            "अभी आपकी तितली सो रही है, इसलिए मस्तिष्क उसे जगाने के लिए जोर से आवाज दे रहा है! तितली सो जाने से आपको नींद आ रही है।"
                        )
                    else: # empathetic
                        response_text = (
                            f"आपका टीएसएच (TSH) स्तर {tsh.value} uIU/mL है, जो सामान्य सीमा ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}) से अधिक है। "
                            "उच्च टीएसएच थायरॉयड ग्रंथि की कम सक्रियता (हाइपोथायरायडिज्म) की ओर इशारा करता है। इससे थकान और सुस्ती महसूस हो सकती है। डॉक्टर से परामर्श करें।"
                        )
                elif lang == "telugu":
                    if tone_str == "clinical":
                        response_text = (
                            f"• విశ్లేషణ సూచిక: టి.ఎస్.హెచ్ (TSH) ఎక్కువ ({tsh.value} uIU/mL). సాధారణ పరిధి: {tsh.min_normal} - {tsh.max_normal} {tsh.unit}.\n"
                            "• పాథోఫిజియాలజీ: థైరాయిడ్ గ్రంధి పనితీరు తగ్గడం (హైపోథైరాయిడిజం).\n"
                            "• సిఫార్సులు: థైరాయిడ్ హార్మోన్ పరీక్షలు (FT3/FT4/TSH) చేయించుకోండి. వైద్యుడిని సంప్రదించండి."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"మీ టి.ఎస్.హెచ్ (TSH) స్థాయి {tsh.value} uIU/mL గా ఉంది, ఇది సాధారణ పరిధి ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}) కంటే ఎక్కువ. "
                            "జీవక్రియ విధానం: థైరాయిడ్ అనేది మెడలో సీతాకోకచిలుక ఆకారంలో ఉండే గ్రంథి. ఇది శరీర జీవక్రియను నియంత్రిస్తుంది. "
                            "మెదడులోని పిట్యూటరీ గ్రంథి థర్మోస్టాట్ లాంటిది. థైరాయిడ్ తక్కువ పనిచేస్తున్నప్పుడు, మెదడు ఎక్కువ TSH విడుదల చేసి దానిని ప్రేరేపిస్తుంది."
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"మీ శరీర థర్మోస్టాట్ (TSH) కొద్దిగా ఎక్కువగా ఉంది ({tsh.value} uIU/mL, సాధారణ పరిధి {tsh.min_normal} నుండి {tsh.max_normal}). "
                            "మీ మెడలో ఒక చిన్న సీతాకోకచిలుక స్నేహితుడు ఉన్నాడు. "
                            "ఇప్పుడు ఆ స్నేహితుడు కొద్దిగా నిద్రపోతుండటంతో, మెదడు థర్మోస్టాట్ గట్టిగా కేకలు వేసి మేల్కొలుపుతోంది! అందుకే మీకు అలసటగా ఉంది."
                        )
                    else: # empathetic
                        response_text = (
                            f"మీ టి.ఎస్.హెచ్ (TSH) స్థాయి {tsh.value} uIU/mL గా ఉంది, ఇది సాధారణ పరిధి ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}) కంటే ఎక్కువ. "
                            "ఇది థైరాయిడ్ గ్రంధి తక్కువ పనితీరును (హైపోథైరాయిడిజం) సూచిస్తుంది. దీనివల్ల బరువు పెరగడం, అలసట కలుగుతాయి. వైద్యుడిని సంప్రదించండి."
                        )
                else: # English
                    if tone_str == "clinical":
                        response_text = (
                            f"• Diagnostic Indicator: TSH high ({tsh.value} uIU/mL). Standard limits: {tsh.min_normal} - {tsh.max_normal} {tsh.unit}.\n"
                            "• Recommendations: Discuss endocrine reviews, FT3/FT4 hormone testing, and therapeutic management with a primary care provider."
                        )
                    elif tone_str == "educational":
                        response_text = (
                            f"Your TSH is currently {tsh.value} uIU/mL, which is above the optimal range ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}). "
                            "Biological Mechanism: The thyroid is a butterfly-shaped neck furnace controlling metabolic speed. The pituitary brain gland acts as the home thermostat. When it senses the furnace isn't releasing enough hormone, it yells louder by releasing more TSH. HIGH TSH indicates an underactive thyroid furnace!"
                        )
                    elif tone_str == "family":
                        response_text = (
                            f"Your body thermostat helper (TSH) is a bit high at {tsh.value} uIU/mL (standard is {tsh.min_normal} to {tsh.max_normal}). "
                            "In your neck, you have a friendly butterfly helper keeping you warm. Right now, your brain thermostat is calling out louder to wake the butterfly up because it is taking a little nap! Sluggish butterfly makes you feel sleepy."
                        )
                    else: # empathetic
                        response_text = (
                            f"Your TSH is currently {tsh.value} uIU/mL, which is above optimal limits ({tsh.min_normal} - {tsh.max_normal} {tsh.unit}). This suggests minor hypothyroid activity slowing metabolism. We recommend showing thyroid metrics to your doctor!"
                        )
            else:
                if lang == "tamil":
                    response_text = "உங்கள் தைராய்டு சுரப்பி சரியாக செயல்படுகிறது. TSH அளவு சாதாரணமாக உள்ளது."
                elif lang == "hindi":
                    response_text = "आपका थायरॉयड स्तर पूरी तरह से सामान्य है।"
                elif lang == "telugu":
                    response_text = "మీ థైరాయిడ్ స్థాయి పూర్తిగా సాధారణంగా ఉంది."
                else:
                    response_text = "Your TSH of {tsh.value} uIU/mL is fully normal, indicating healthy thyroid furnace function."
        else:
            if lang == "tamil":
                response_text = "தைராய்டு ஹார்மோன் உடலின் வளர்சிதை மாற்ற வேகத்தைக் கட்டுப்படுத்துகிறது. டி.எஸ்.ஹெச் (TSH) பரிசோதனை இதய துடிப்பு மற்றும் ஆற்றலை மதிப்பிட உதவும்."
            elif lang == "hindi":
                response_text = "थायरॉयड हार्मोन शारीरिक चयापचय को नियंत्रित करते हैं। उचित जांच के लिए डॉक्टर से मिलें।"
            elif lang == "telugu":
                response_text = "థైరాయిడ్ హార్మోన్లు శారీరక జీవక్రియను నియంత్రిస్తాయి. వైద్య సలహా తీసుకోండి."
            else:
                response_text = "Thyroid hormones guide metabolic speed. Elevated TSH indicates sluggish thyroid responses. Consult with your physician for thyroid hormone checks."

    # 5. Diet / Food / Lifestyle / Wellness recommendations
    elif any(k in q for k in ["diet", "food", "eat", "lifestyle", "exercise", "walk", "உணவு", "பயிற்சி", "நடை", "உண்ண", "आहार", "भोजन", "व्यायाम", "सैर", "ఆహారం", "వ్యాయామం", "నడక"]):
        if lang == "tamil":
            if tone_str == "clinical":
                response_text = (
                    "• உணவு: இரும்புச்சத்து நிறைந்த கீரைகள், புரதங்கள் மற்றும் நார்ச்சத்துக்களை உட்கொள்ளவும். சர்க்கரையைக் குறைக்கவும்.\n"
                    "• உடற்பயிற்சி: தினசரி 20-30 நிமிடங்கள் வேகமாக நடக்கவும். இன்சுலின் எதிர்ப்பு குறையும்.\n"
                    "• மருத்துவர் ஆலோசனை: புதிய உணவு முறைகளைத் தொடங்குவதற்கு முன் மருத்துவரை அணுகவும்."
                )
            elif tone_str == "educational":
                response_text = (
                    "உடலின் ஆரோக்கியத்தை மேம்படுத்த மூன்று முக்கிய தூண்கள்:\n"
                    "1. **பச்சை காய்கறிகள் & புரதங்கள்**: இது ஹீமோகுளோபின் உற்பத்திக்கான இரும்புச்சத்தை வழங்குகிறது.\n"
                    "2. **நல்ல கொழுப்புகள் (Omega-3)**: இரத்த நாளங்களில் உள்ள அடைப்புகளை நீக்க உதவுகிறது.\n"
                    "3. **தினசரி நடைப்பயிற்சி**: இன்சுலின் சாவிகள் இல்லாமலேயே செல்கள் சர்க்கரையை உறிஞ்ச உதவுகிறது."
                )
            elif tone_str == "family":
                response_text = (
                    "உங்கள் உடலை சுறுசுறுப்பாக வைத்திருக்க மூன்று சூப்பர் வழிகள்:\n"
                    "1. **பச்சை காய்கறிகள் சாப்பிடுங்கள்**: இது உடலின் சிறிய பலூன்களுக்கு புதிய காற்று மற்றும் இரும்புச்சத்தை வழங்கும்!\n"
                    "2. **ஓட்ஸ் மற்றும் கொட்டைகள்**: இவை இரத்த நாளங்களை தூய்மையாக வைத்திருக்கும் குட்டி வாக்யூம்கள் ஆகும்!\n"
                    "3. **ஓடி விளையாடுங்கள்**: தினமும் நன்றாக விளையாடுவது உடலை வலிமையாக்கும்!"
                )
            else: # empathetic
                response_text = (
                    "ஆரோக்கியமான உடலைப் பெற மூன்று எளிய பழக்கங்களை மேற்கொள்ளலாம்:\n"
                    "1. **சமச்சீர் உணவு**: கீரைகள், பருப்புகள் மற்றும் நார்ச்சத்துள்ள உணவுகளை சேர்க்கவும்.\n"
                    "2. **இதயத்திற்கு நல்ல கொழுப்புகள்**: தாவர எண்ணெய் மற்றும் கொட்டைகளை உட்கொள்ளவும்.\n"
                    "3. **தினசரி உடற்பயிற்சி**: தினமும் 20-30 நிமிடங்கள் வேகமாக நடப்பது சர்க்கரை அளவை சீராக வைத்திருக்க உதவும். மருத்துவரை அணுகவும்."
                )
        elif lang == "hindi":
            if tone_str == "clinical":
                response_text = (
                    "• आहार: हरी पत्तेदार सब्जियां, प्रोटीन और उच्च फाइबर लें। मीठा कम करें।\n"
                    "• व्यायाम: दैनिक 20-30 मिनट ब्रिस्क वॉक करें।\n"
                    "• समन्वय: नई जीवनशैली से पहले चिकित्सक से परामर्श करें।"
                )
            elif tone_str == "educational":
                response_text = (
                    "शारीरिक स्वास्थ्य को बेहतर बनाने के तीन प्रमुख स्तंभ:\n"
                    "1. **हरी सब्जियां और प्रोटीन**: यह हीमोग्लोबिन के लिए आवश्यक आयरन प्रदान करता है।\n"
                    "2. **ओमेगा-3 वसा**: यह धमनियों में वसा जमा होने से रोकता है।\n"
                    "3. **नियमित व्यायाम**: यह कोशिकाओं को इंसुलिन के बिना भी शुगर सोखने में सक्षम बनाता है।"
                )
            elif tone_str == "family":
                response_text = (
                    "शरीर को मजबूत और स्वस्थ रखने के तीन तरीके:\n"
                    "1. **हरी सब्जियां खाएं**: यह शरीर के छोटे गुब्बारों को सुपर ऊर्जा प्रदान करता है!\n"
                    "2. **ओट्स और ड्राई फ्रूट्स**: ये धमनियों को साफ रखने वाले छोटे क्लीनर हैं!\n"
                    "3. **खूब खेलें और टहलें**: रोजाना एक्टिव रहने से शरीर की कोशिकाएं स्वस्थ रहती हैं!"
                )
            else: # empathetic
                response_text = (
                    "स्वस्थ जीवनशैली के लिए तीन सरल आदतें अपनाएं:\n"
                    "1. **संतुलित आहार**: हरी सब्जियां, दालें और फाइबर युक्त भोजन लें।\n"
                    "2. **हृदय के अनुकूल वसा**: जैतून का तेल और नट्स का उपयोग करें।\n"
                    "3. **दैनिक शारीरिक गतिविधि**: 20-30 मिनट टहलना रक्त शर्करा को नियंत्रित रखता है। डॉक्टर से मिलें।"
                )
        elif lang == "telugu":
            if tone_str == "clinical":
                response_text = (
                    "• ఆహారం: ఆకుకూరలు, ప్రోటీన్లు మరియు పీచు పదార్థాలు తీసుకోండి. తీపి తగ్గించండి.\n"
                    "• వ్యాయామం: ప్రతిరోజు 20-30 నిమిషాలు వేగంగా నడవండి. ఇది ఇన్సులిన్ నిరోధకతను తగ్గిస్తుంది.\n"
                    "• సమన్వయం: కొత్త జీవనశైలి మార్పుల కొరకు మీ వైద్యుడిని సంప్రదించండి."
                )
            elif tone_str == "educational":
                response_text = (
                    "శరీర ఆరోగ్యానికి మూడు ముఖ్యమైన స్తంభాలు:\n"
                    "1. **ఆకుకూరలు & ప్రోటీన్లు**: ఇది హిమోగ్లోబిన్ తయారీకి ఇనుమును అందిస్తుంది.\n"
                    "2. **ఒమేగా-3 కొవ్వులు**: ఇవి రక్తనాళాలలో చెడు కొవ్వును తొలగించడానికి సహాయపడతాయి.\n"
                    "3. **శారీరక శ్రమ**: నడక వల్ల కణాలు గ్లూకోజ్ ను సులభంగా గ్రహిస్తాయి."
                )
            elif tone_str == "family":
                response_text = (
                    "శరీరాన్ని బలంగా ఉంచే మూడు ఉత్తమ మార్గాలు:\n"
                    "1. **ఆకుకూరలు తినండి**: ఇవి శరీరంలోని గాలి బుడగలకు అదనపు బలాన్ని ఇస్తాయి!\n"
                    "2. **ఓట్స్ మరియు బాదం**: ఇవి రక్తనాళాలను శుభ్రం చేసే చిన్న వ్యాక్యూమ్ క్లీనర్లు!\n"
                    "3. **బాగా ఆడుకోండి**: ప్రతిరోజు కాసేపు ఆడుకోవడం వల్ల కణాలు చురుగ్గా ఉంటాయి!"
                )
            else: # empathetic
                response_text = (
                    "ఆరోగ్యంగా ఉండటానికి మూడు సరళమైన మార్గాలు:\n"
                    "1. **సమతుల్య ఆహారం**: ఆకుకూరలు, పప్పులు మరియు పీచు ఎక్కువగా ఉండే ఆహారం తీసుకోండి.\n"
                    "2. **గుండెకు మంచి కొవ్వులు**: నూనెలు మరియు నట్స్ తీసుకోండి.\n"
                    "3. **రోజువారీ నడక**: ప్రతిరోజు 20-30 నిమిషాలు వేగంగా నడవడం ద్వారా చక్కెర స్థాయిలను నియంత్రించవచ్చు. వైద్యుడిని సంప్రదించండి."
                )
        else: # English
            if tone_str == "clinical":
                response_text = (
                    "• Diet: Consume leafy greens, complex proteins, and plant fibers. Restrict processed sugars.\n"
                    "• Cardiovascular: Replace saturated fats with unsaturated omega-3s to clear arterial lipids.\n"
                    "• Exercise: Complete 20-30 minutes of daily physical walks to reduce glycemic insulin resistance.\n"
                    "• Coordination: Review all lifestyle parameters with your licensed provider."
                )
            elif tone_str == "educational":
                response_text = (
                    "To optimize your biochemical baseline pathways, focus on three primary lifestyle pillars:\n"
                    "1. **Leafy Greens & Proteins**: Provides raw iron materials to synthesize hemoglobin balloons and stabilize cellular energy.\n"
                    "2. **Omega-3 Unsaturated Fats**: Acts as arterial recycling units, binding lipid complexes to lower LDL cardiovascular risks.\n"
                    "3. **Physical Activity**: Walking triggers GLUT4 protein receptors, pulling glucose sugar out of the bloodstream independently of insulin.\n"
                    "Coordinate with your physician to discuss therapeutic pathways!"
                )
            elif tone_str == "family":
                response_text = (
                    "Here are three super-boosters to help your body feel strong and happy:\n"
                    "1. **Eat Green Veggies & Fruits**: This is like giving your body high-quality fuels so your balloons can carry lots of fresh air!\n"
                    "2. **Yummy Oatmeal & Nuts**: These act like friendly little vacuums that tidy up extra fats floating in your vessels!\n"
                    "3. **Fun Active Play**: Going outside to play or taking a active walk helps your body save energy easily in its cells!\n"
                    "Always check in with your parents or friendly family doctor before trying new things!"
                )
            else: # empathetic
                response_text = (
                    "To support optimal blood values holistically, we recommend three simple lifestyle habits:\n"
                    "1. **Diverse Whole Foods**: Focus on leafy greens, lean proteins, and complex carbohydrates to support iron and control blood glucose.\n"
                    "2. **Heart-Healthy Fats**: Clears LDL fat deposits by adding omega-3s (like chia seeds and fish) and reducing processed saturated fats.\n"
                    "3. **Daily Physical Activity**: Walking 20-30 minutes daily is highly effective in increasing insulin sensitivity and lowering blood pressure.\n"
                    "Always align any lifestyle adjustments with your doctor first!"
                )

    # 6. Vitamin D / general vitamin questions
    elif any(k in q for k in ["vitamin", "vit d", "deficiency", "வைட்டமின்", "விட்டமின்", "विटामिन", "कमी", "విటమిన్", "లోపం"]):
        if lang == "tamil":
            response_text = "வைட்டமின் டி (Vitamin D) எலும்புகளின் வலிமை மற்றும் நோய் எதிர்ப்பு சக்திக்கு இன்றியமையாதது. இதன் குறைபாடு சோர்வு மற்றும் தசை வலிமையை ஏற்படுத்தலாம். காலையில் மிதமான சூரிய ஒளியில் நிற்பதும், முட்டை மற்றும் பால் பொருட்களை உட்கொள்வதும் நல்லது. எப்போதும் மருத்துவரை அணுகி ஆலோசனை பெறவும்."
        elif lang == "hindi":
            response_text = "विटामिन डी हड्डियों की मजबूती और प्रतिरक्षा प्रणाली के लिए बहुत महत्वपूर्ण है। इसकी कमी से थकान और हड्डियों में दर्द हो सकता है। सुबह की धूप लें और अंडे व दूध का सेवन करें। हमेशा डॉक्टर से सलाह लें।"
        elif lang == "telugu":
            response_text = "విటమిన్ డి ఎముకల బలానికి మరియు రోగనిరోధక శక్తికి చాలా అవసరం. దీని కొరత వల్ల అలసట మరియు కండరాల బలహీనత కలగవచ్చు. ఉదయం పూట ఎండలో నిలబడటం, గుడ్లు మరియు పాలు తీసుకోవడం మంచిది. వైద్యుడిని సంప్రదించండి."
        else:
            response_text = "Vitamin D is essential for maintaining strong bones, muscle function, and a healthy immune system. Early signs of deficiency can include feeling unusually tired, bone discomfort, and muscle weakness. Adding foods like eggs, fortified milks, and catching some safe morning sunshine are excellent ways to boost your levels. Always consult a healthcare provider for personalized diagnostic advice."

    # 7. Acute-phase reactants / general biology questions
    elif any(k in q for k in ["reactant", "acute-phase", "inflammation", "crp", "அழற்சி", "தொற்று", "सूजन", "वाపు"]):
        if lang == "tamil":
            response_text = "அழற்சி புரதங்கள் (CRP போன்றவை) உடலில் ஏதேனும் தொற்று அல்லது காயம் ஏற்படும் போது கல்லீரலால் வெளியிடப்படும் பாதுகாப்பு புரதங்கள் ஆகும். இவை உடலின் வெள்ளை இரத்த அணுக்கள் பாதிப்படைந்த பகுதியைக் கண்டறிந்து குணப்படுத்த உதவுகின்றன. எப்போதும் மருத்துவரை அணுகி ஆலோசனை பெறவும்."
        elif lang == "hindi":
            response_text = "तीव्र-चरण अभिकारक (जैसे सीआरपी) प्रोटीन हैं जो शरीर में सूजन या संक्रमण होने पर लीवर द्वारा जारी किए जाते हैं। ये श्वेत रक्त कोशिकाओं को प्रभावित क्षेत्र को ठीक करने में मदद करते हैं। हमेशा डॉक्टर से सलाह लें।"
        elif lang == "telugu":
            response_text = "శరీరంలో ఇన్ఫ్లమేషన్ (వాపు) లేదా ఇన్ఫెక్షన్ ఉన్నప్పుడు కాలేయం నుండి సిఆర్పి (CRP) వంటి రక్షక ప్రోటీన్లు విడుదలవుతాయి. ఇవి రోగనిరోధక కణాలకు సహాయపడతాయి. వైద్యుడిని సంప్రదించండి."
        else:
            response_text = "Acute-phase reactants are immune-system defense proteins produced by your liver when your body is actively fighting off a bug or healing an injury. C-Reactive Protein (CRP) is a positive acute-phase reactant that increases during active inflammation, helping guide immune cells to the affected area. Always consult a healthcare provider for personalized diagnostic advice."

    # 8. High-stakes emergency triage questions
    elif any(k in q for k in ["chest pain", "heart attack", "emergency", "stroke", "breathing", "severe pain", "die", "வலி", "நெஞ்சு", "நெஞ்சுவலி", "அவசரம்", "दर्द", "छाती", "सांस", "ఆరోగ్య", "నెప్పి", "గుండె", "శ్వాస"]):
        if lang == "tamil":
            response_text = "கடுமையான நெஞ்சுவலி அல்லது மூச்சுத்திணறல் இருந்தால், அது உடனடியாக கவனிக்கப்பட வேண்டிய அவசர நிலையாகும். தயவுசெய்து அவசர உதவி எண்ணை (108 அல்லது 911) தொடர்பு கொள்ளவும். அமைதியாக அமர்ந்து ஓய்வெடுக்கவும், தனியாக பயணம் செய்ய வேண்டாம். எப்போதும் மருத்துவரை அணுகவும்."
        elif lang == "hindi":
            response_text = "यदि आपको सीने में तेज दर्द या सांस लेने में तकलीफ हो रही है, तो यह एक बड़ी आपातकालीन स्थिति है। तुरंत एम्बुलेंस या आपातकालीन सेवाओं (102 या 911) को कॉल करें। शांत बैठें, आराम करें और अकेले यात्रा न करें। डॉक्टर से संपर्क करें।"
        elif lang == "telugu":
            response_text = "మీకు తీవ్రమైన గుండెనొప్పి లేదా శ్వాస తీసుకోవడంలో ఇబ్బంది ఉంటే, ఇది అత్యవసర పరిస్థితి! వెంటనే అంబులెన్స్ లేదా అత్యవసర సేవలను (108 లేదా 911) సంప్రదించండి. ప్రశాంతంగా కూర్చోండి, ఒంటరిగా ప్రయాణించవద్దు. వైద్యుడిని సంప్రదించండి."
        else:
            response_text = "If you are experiencing chest pain, severe shortness of breath, or a sudden emergency, please call your local emergency services (911/112) immediately. Please sit down, rest calmly to reduce physical stress, and do not attempt to travel alone. Your safety is the highest priority. Always consult a healthcare provider for personalized diagnostic advice."

    # 6. Default general clinical assistant response
    else:
        if lang == "tamil":
            if tone_str == "clinical":
                response_text = "வணக்கம்! நான் உங்கள் மருத்துவ உதவியாளர். உங்களது ஹீமோகுளோபின், சர்க்கரை, கொழுப்பு மற்றும் TSH அளவுகளை பகுப்பாய்வு செய்துள்ளேன். எந்த அளவுருவை விவாதிக்க விரும்புகிறீர்கள்?"
            elif tone_str == "educational":
                response_text = "வணக்கம்! நான் உங்கள் அறிவியல் மருத்துவ உதவியாளர். உங்கள் உடலின் உயிரியல் செயல்பாடுகளை ஆராய நான் தயாராக உள்ளேன். எதைப் பற்றி அறிய விரும்புகிறீர்கள்?"
            elif tone_str == "family":
                response_text = "ஹலோ! நான் உங்கள் உடலமைப்பு நண்பன். உங்கள் பலூன்கள், ஆற்றல் நாணயங்கள் பற்றி பேசலாமா? எளிய கதைகளில் விளக்க நான் இங்கு இருக்கிறேன்!"
            else: # empathetic
                response_text = "வணக்கம்! நான் உங்கள் அன்பு மருத்துவ உதவியாளர். உங்கள் இரத்த அறிக்கையின் முடிவுகளை எளிய சொற்களில் விளக்க நான் இங்கு இருக்கிறேன். இன்று எதைப் பற்றி விவாதிக்க விரும்புகிறீர்கள்?"
        elif lang == "hindi":
            if tone_str == "clinical":
                response_text = "नमस्ते! मैं आपका नैदानिक चिकित्सा सहायक हूँ। मैंने आपके हीमोग्लोबिन, शुगर, कोलेस्ट्रॉल और टीएसएच स्तरों की समीक्षा की है। आप किस विषय पर चर्चा करना चाहते हैं?"
            elif tone_str == "educational":
                response_text = "नमस्ते! मैं आपका वैज्ञानिक चिकित्सा सहायक हूँ। आइए आपके बायोमार्कर के पीछे की जीव विज्ञान को समझें। आप क्या जानना चाहते हैं?"
            elif tone_str == "family":
                response_text = "नमस्ते! मैं आपका मित्रवत शरीर सहायक हूँ। आपके शरीर के मित्रों (जैसे गुब्बारे और ऊर्जा के सिक्कों) के बारे में कोई भी प्रश्न पूछें!"
            else: # empathetic
                response_text = "नमस्ते! मैं आपका सहानुभूतिपूर्ण चिकित्सा सहायक हूँ। मैं आपकी रिपोर्ट के परिणामों को सरल शब्दों में समझाने के लिए यहाँ हूँ। आज आप किस विषय में बात करना चाहेंगे?"
        elif lang == "telugu":
            if tone_str == "clinical":
                response_text = "నమస్కారం! నేను మీ క్లినికల్ మెడికల్ సహాయకుడిని. మీ హిమోగ్లోబిన్, గ్లూకోజ్, కొలెస్ట్రాల్ మరియు TSH స్థాయిలను సమీక్షించాను. వేటి గురించి చర్చించాలనుకుంటున్నారు?"
            elif tone_str == "educational":
                response_text = "నమస్కారం! నేను మీ జీవశాస్త్ర సహాయకుడిని. మీ బయోమార్కర్ల వెనుక ఉన్న విజ్ఞానాన్ని వివరిస్తాను. వేటి గురించి తెలుసుకోవాలనుకుంటున్నారు?"
            elif tone_str == "family":
                response_text = "హలో! నేను మీ శరీర సహాయకుడిని. మీ గాలి బుడగలు, శక్తి నాణేల గురించి కథలలో వివరిస్తాను! దేని గురించి మాట్లాడదాం?"
            else: # empathetic
 