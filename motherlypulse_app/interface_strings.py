"""
MotherlyPulse Multilingual Interface Strings
Provides UI prompts, button texts, help messages, and confirmations in English, Yoruba, and Nigerian Pidgin.

Safety invariant:
- Flag `allow_unreviewed_translations: bool = False` by default.
- If `allow_unreviewed_translations` is False, any string for a language whose
  linguistic review status is not finalized ('in progress' or 'not reviewed')
  falls back to English, preventing unreviewed translation from being presented
  without explicit administrative opt-in.
"""

from typing import Dict, Any, Optional

# Review statuses for interface strings:
# English: canonical baseline
# Yoruba: in progress (preliminary translation, pending formal clinical-linguist sign-off)
# Nigerian Pidgin: in progress (preliminary translation, pending formal clinical-linguist sign-off)
STRING_REVIEW_STATUS = {
    "English": "reviewed",
    "Yoruba": "in progress",
    "Nigerian Pidgin": "in progress"
}

STRINGS: Dict[str, Dict[str, str]] = {
    "welcome": {
        "English": (
            "Welcome to MotherlyPulse. I provide maternal and infant health guidance for mothers "
            "and caregivers in Ondo State. In any medical emergency, please call 112 immediately or visit the nearest hospital."
        ),
        "Yoruba": (
            "E kaabo si MotherlyPulse. Mo wa nibi lati ran awon iya ati alaboyun lowo pelu imo ilera ni Ipinle Ondo. "
            "Ti pajawiri ba wa, pe 112 lẹsẹkẹsẹ tabi ki o lo si ile iwosan to sunmo julo."
        ),
        "Nigerian Pidgin": (
            "Welcome to MotherlyPulse. I dey here to help mama, belle women, and pikins with correct health advice for Ondo State. "
            "If any emergency happen, call 112 quick-quick or go the nearest hospital."
        )
    },
    "language_select_prompt": {
        "English": (
            "🌍 Please select your preferred language:\n"
            "1. English\n"
            "2. Yoruba (Èdè Yorùbá)\n"
            "3. Nigerian Pidgin (Naijá Pidgin)\n\n"
            "Reply with 1, 2, or 3, or tap a button below."
        ),
        "Yoruba": (
            "🌍 E jọwọ yan ede ti ẹ fẹ lo:\n"
            "1. English (Gẹẹsi)\n"
            "2. Yoruba (Èdè Yorùbá)\n"
            "3. Nigerian Pidgin (Naijá Pidgin)\n\n"
            "Ẹ dahun pẹlu okan, eeji, tabi meta."
        ),
        "Nigerian Pidgin": (
            "🌍 Abeg select the language wey you wan use:\n"
            "1. English\n"
            "2. Yoruba\n"
            "3. Nigerian Pidgin\n\n"
            "Reply with 1, 2, or 3, or tap the button."
        )
    },
    "consent_prompt": {
        "English": (
            "Before we begin, do you agree to use MotherlyPulse for health information? "
            "MotherlyPulse does not replace a doctor. Type /agree to continue or /stop to decline."
        ),
        "Yoruba": (
            "Ki a to bere, se o gba lati lo MotherlyPulse fun imo ilera? "
            "MotherlyPulse ki i se dokita. Te /mogba lati tesiwaju tabi /duro ti o ko ba fe."
        ),
        "Nigerian Pidgin": (
            "Before we start, you agree make we use MotherlyPulse give you health info? "
            "MotherlyPulse no be medical doctor. Type /agree make we continue or /stop if you no wan."
        )
    },
    "consent_notice_text": {
        "English": (
            "📋 **MOTHERLYPULSE CONSENT NOTICE**\n\n"
            "MotherlyPulse provides maternal and infant health support, routine clinic & medication reminders, "
            "and health facility lookups for mothers and caregivers in Ondo State.\n\n"
            "**Key Principles:**\n"
            "• MotherlyPulse does not replace a medical doctor, midwife, or clinic examination.\n"
            "• In an emergency, always call 112 immediately or proceed to the nearest emergency facility.\n"
            "• We collect basic non-sensitive milestone information (such as preferred alias, pregnancy delivery date, or infant birth date) strictly to deliver timely health reminders.\n"
            "• Your data is kept secure and will not be shared with unauthorized third parties.\n"
            "• You may delete your account and personal data anytime using /delete.\n\n"
            "Do you agree to proceed?\n"
            "• Reply **agree** (or /agree) to give consent\n"
            "• Reply **decline** (or /stop) to decline"
        ),
        "Yoruba": (
            "📋 **IKEDE IFOHUNSOKAN MOTHERLYPULSE**\n\n"
            "MotherlyPulse n pese iranlọwọ ilera fun awọn aboyun ati awọn iya ọmọ ni Ipinle Ondo, "
            "pẹlu awọn iranti abẹwo ile-iwosan, oogun, ati wiwa ile-iṣẹ ilera.\n\n"
            "**Awọn Eto Pataki:**\n"
            "• MotherlyPulse ki i ṣe dokita tabi agbẹbi, ko si rọpo ayẹwo ile-iwosan.\n"
            "• Ti pajawiri ba wa, pe 112 lẹsẹkẹsẹ tabi ki ẹ lọ si ile-iwosan to sunmọ.\n"
            "• A n gba orukọ inagijẹ ati ọjọ ibimọ lati le ran yin leti abẹwo ati ajesara.\n"
            "• Aabo wa fun gbogbo alaye yin, a ko si ni pin pẹlu ẹnikẹni.\n"
            "• Ẹ le pa gbogbo alaye yin rẹ nigbakugba pẹlu /delete.\n\n"
            "Ṣe ẹ gba lati tẹsiwaju?\n"
            "• Dahun **mo gba** (tabi /agree) lati gba wọle\n"
            "• Dahun **mi o gba** (tabi /stop) ti ẹ kò ba fẹ"
        ),
        "Nigerian Pidgin": (
            "📋 **MOTHERLYPULSE AGREE NOTICE**\n\n"
            "MotherlyPulse dey give mama, belle women, and pikins correct health info, clinic & medicine reminders, "
            "and hospital lookup for Ondo State.\n\n"
            "**Important Things to Note:**\n"
            "• MotherlyPulse no be medical doctor or nurse, e no replace doctor checkup.\n"
            "• If na emergency, call 112 quick-quick or go hospital immediately.\n"
            "• We dey collect your alias name and baby date to help set correct clinic and vaccine reminder.\n"
            "• We keep your data safe and we no go share am give anybody.\n"
            "• You fit clear all your data anytime with /delete.\n\n"
            "You agree make we start?\n"
            "• Type **agree** (or /agree) to accept\n"
            "• Type **decline** (or /stop) if you no agree"
        )
    },
    "consent_declined": {
        "English": (
            "You have declined consent. Respecting your privacy, no personal information has been collected or saved.\n\n"
            "If you change your mind later, simply type /start to begin anytime.\n\n"
            "⚠️ In any medical emergency, please dial national emergency services on 112 immediately."
        ),
        "Yoruba": (
            "Ẹ ti kọ ifọhunsọkan. Nitori aṣiri yin, a ko gba tabi fi alaye kankan pamọ.\n\n"
            "Ti ẹ ba fẹ tẹsiwaju nigbamii, ẹ tẹ /beere nigbakugba.\n\n"
            "⚠️ Ti pajawiri ba wa, ẹ pe 112 lẹsẹkẹsẹ."
        ),
        "Nigerian Pidgin": (
            "You decline to agree. We respect your choice, so we no collect or save any of your info at all.\n\n"
            "If you change your mind later, just type /start make you begin again.\n\n"
            "⚠️ If emergency happen, call 112 right now."
        )
    },
    "consent_confirmed": {
        "English": "Thank you. Your consent has been recorded. How can I help you today?",
        "Yoruba": "E se pupo. A ti gba ifohunsokan re wole. Bawo ni mo se le ran o lowo loni?",
        "Nigerian Pidgin": "Thank you well well. We don record your agree. How I fit help you today?"
    },
    "alias_request": {
        "English": (
            "What name or alias should I call you? (e.g. Mama Tolu, Funke, Sister Mary)\n"
            "You can use any preferred nickname."
        ),
        "Yoruba": (
            "Orukọ inagijẹ wo ni ki n máa pè yín? (fun apẹẹrẹ: Mama Tolu, Funke)\n"
            "Ẹ le lo orukọ eyikeyi ti ẹ fẹ."
        ),
        "Nigerian Pidgin": (
            "Which name or alias you wan make I dey call you? (like Mama Tolu, Funke, Sister Mary)\n"
            "You fit use any nickname wey sweet you."
        )
    },
    "group_request": {
        "English": (
            "Please select your user group:\n"
            "1. Pregnant woman (Expecting a baby)\n"
            "2. Mother or caregiver of an infant / young child\n\n"
            "Reply with 1 or 2, or type 'pregnant' / 'mother'."
        ),
        "Yoruba": (
            "E jọwọ yan ẹka ti ẹ wa:\n"
            "1. Alaboyun (Ẹ n reti ọmọ)\n"
            "2. Iya tabi alabojuto ọmọ ọwọ\n\n"
            "Ẹ dahun pẹlu okan tabi eeji."
        ),
        "Nigerian Pidgin": (
            "Abeg choose which group you dey:\n"
            "1. Belle woman (Expecting baby)\n"
            "2. Mama or caregiver wey get infant/pikin\n\n"
            "Reply with 1 or 2, or type 'pregnant' / 'mother'."
        )
    },
    "edd_request": {
        "English": (
            "What is your Expected Delivery Date (EDD)?\n"
            "Please enter it as YYYY-MM-DD or DD/MM/YYYY (e.g. 2026-12-15 or 15/12/2026)."
        ),
        "Yoruba": (
            "Ọjọ wo ni a n reti ibimọ ọmọ yin (EDD)?\n"
            "Ẹ jọwọ tẹ ẹ bi YYYY-MM-DD tabi DD/MM/YYYY (fun apẹẹrẹ: 2026-12-15 tabi 15/12/2026)."
        ),
        "Nigerian Pidgin": (
            "Which date doctor tell you say you go born (Expected Delivery Date)?\n"
            "Abeg type am as YYYY-MM-DD or DD/MM/YYYY (example: 2026-12-15 or 15/12/2026)."
        )
    },
    "dob_request": {
        "English": (
            "What is your baby's Date of Birth (DOB)?\n"
            "Please enter it as YYYY-MM-DD or DD/MM/YYYY (e.g. 2026-06-01 or 01/06/2026)."
        ),
        "Yoruba": (
            "Ọjọ wo ni a bi ọmọ yin (DOB)?\n"
            "Ẹ jọwọ tẹ ẹ bi YYYY-MM-DD tabi DD/MM/YYYY (fun apẹẹrẹ: 2026-06-01 tabi 01/06/2026)."
        ),
        "Nigerian Pidgin": (
            "When your baby born (Date of Birth)?\n"
            "Abeg type am as YYYY-MM-DD or DD/MM/YYYY (example: 2026-06-01 or 01/06/2026)."
        )
    },
    "date_error_format": {
        "English": "Invalid date format. Please enter as YYYY-MM-DD or DD/MM/YYYY (e.g. 2026-12-15 or 15/12/2026).",
        "Yoruba": "Ọna ti ẹ kọ ọjọ yii ko tọna. Ẹ jọwọ kọ ọ bi YYYY-MM-DD tabi DD/MM/YYYY (fun apẹẹrẹ: 2026-12-15).",
        "Nigerian Pidgin": "The date format no correct. Abeg enter am as YYYY-MM-DD or DD/MM/YYYY (like 2026-12-15)."
    },
    "date_error_edd_past": {
        "English": "The expected delivery date cannot be in the past. Please enter your upcoming delivery date.",
        "Yoruba": "Ọjọ ibimọ ti a n reti ko le jẹ ọjọ ti o ti kọja. Ẹ jọwọ kọ ọjọ ti o n bọ.",
        "Nigerian Pidgin": "Delivery date no fit don pass already. Abeg enter the correct date wey dey come."
    },
    "edd_past_check_prompt": {
        "English": (
            "Has your baby already been born?\n\n"
            "• Reply **yes** if your baby has arrived (to record baby's birth date and routine vaccinations).\n"
            "• Reply **no** if you are still expecting.\n\n"
            "⚠️ *Clinical note:* If you are past your expected delivery date and still pregnant, we recommend contacting your doctor, midwife, or primary health clinic promptly for examination and monitoring. In an emergency, dial 112 immediately."
        ),
        "Yoruba": (
            "Ṣe a ti bi ọmọ naa?\n\n"
            "• Dahun **beeni** ti a ba ti bi ọmọ (lati kọ ọjọ ibimọ ati bẹrẹ eto ajesara).\n"
            "• Dahun **rara** ti ẹ ba ṣi wa ninu oyun.\n\n"
            "⚠️ *Akiyesi Ilera:* Ti ọjọ ibimọ ba ti kọja ti ẹ si ṣi wa ninu oyun, a gba yin nimọran lati lọ si ile-iwosan tabi kan si dokita/agbẹbi yin lẹsẹkẹsẹ fun ayẹwo to peye. Ti pajawiri ba wa, pe 112 lẹsẹkẹsẹ."
        ),
        "Nigerian Pidgin": (
            "You don born the baby already?\n\n"
            "• Type **yes** if baby don arrive (make we fit record birth date and arrange vaccine reminders).\n"
            "• Type **no** if you still dey expect.\n\n"
            "⚠️ *Health advice:* If your delivery date don pass and you never born, abeg go clinic or see your doctor/midwife quick-quick make dem examine you well. For any emergency, call 112 immediately."
        )
    },
    "edd_post_term_retained_notice": {
        "English": (
            "🎉 **Registration Complete!**\n\n"
            "Welcome to MotherlyPulse, {alias}! Your pregnancy profile has been recorded with Expected Delivery Date {milestone_date}.\n\n"
            "⚠️ **Important Clinical Recommendation:** Because your expected delivery date has passed, please contact your antenatal clinic, doctor, or midwife promptly for a clinical examination and monitoring. "
            "If you experience any severe symptoms, bleeding, severe headache, or reduced baby movements, call **112** or proceed to the nearest emergency maternal facility immediately."
        ),
        "Yoruba": (
            "🎉 **Iforukọsilẹ Pari Ni Aṣeyọri!**\n\n"
            "Ẹ kaabọ si MotherlyPulse, {alias}! A ti fi profaili oyun yin pamọ pẹlu ọjọ ibimọ {milestone_date}.\n\n"
            "⚠️ **Imọran Ilera Pataki:** Nitoripe ọjọ ibimọ ti ẹ n reti ti kọja, ẹ jọwọ kan si ile-iwosan tabi dokita/agbẹbi yin lẹsẹkẹsẹ fun ayẹwo ati abojuto to peye. "
            "Ti eewu ba wa bi ẹjẹ tabi orififo lile, pe **112** lẹsẹkẹsẹ."
        ),
        "Nigerian Pidgin": (
            "🎉 **Registration Don Complete!**\n\n"
            "Welcome to MotherlyPulse, {alias}! We don save your belle profile with delivery date {milestone_date}.\n\n"
            "⚠️ **Important Health Advice:** As your delivery date don pass, abeg go clinic or see your doctor/midwife quick-quick make dem check you well. "
            "If any danger sign happen like heavy bleeding, call **112** immediately."
        )
    },
    "date_error_edd_future": {
        "English": "The expected delivery date is too far in the future (gestation is up to 42 weeks). Please check and re-enter.",
        "Yoruba": "Ọjọ ibimọ yii jinna ju (oyun kii koja ọsẹ 42). Ẹ jọwọ ṣayẹwo ki ẹ si tẹ ẹ lẹẹkansi.",
        "Nigerian Pidgin": "The delivery date far too much (belle no dey pass 42 weeks). Abeg check and type am again."
    },
    "date_error_dob_future": {
        "English": "Baby's birth date cannot be in the future. Please enter your baby's actual date of birth.",
        "Yoruba": "Ọjọ ibimọ ọmọ ko le jẹ ọjọ iwaju. Ẹ jọwọ kọ ọjọ gangan ti a bi ọmọ.",
        "Nigerian Pidgin": "Baby birth date no fit dey the future. Abeg enter the actual date wey baby born."
    },
    "date_error_dob_old": {
        "English": "MotherlyPulse focuses on pregnancy and infants up to one year after birth. Please enter an infant birth date within the past year.",
        "Yoruba": "MotherlyPulse wa fun oyun ati itọju ọmọ wẹwẹ titi di ọdun kan. Ẹ jọwọ kọ ọjọ ibimọ ọmọ to wa laarin ọdun kan.",
        "Nigerian Pidgin": "MotherlyPulse dey focus on belle and small pikin wey no pass one year. Abeg enter birth date within the past year."
    },
    "registration_complete": {
        "English": (
            "🎉 **Registration Complete!**\n\n"
            "Welcome to MotherlyPulse, {alias}! Your profile has been saved.\n"
            "• Category: {group_desc}\n"
            "• Milestone Date: {milestone_date}\n"
            "• Language: {language}\n\n"
            "You can now manage reminders, find clinics in Ondo State, or view your profile below."
        ),
        "Yoruba": (
            "🎉 **Iforukọsilẹ Pari Ni Aṣeyọri!**\n\n"
            "Ẹ kaabọ si MotherlyPulse, {alias}! A ti fi profaili yin pamọ.\n"
            "• Ẹka: {group_desc}\n"
            "• Ọjọ Pataki: {milestone_date}\n"
            "• Ede: {language}\n\n"
            "Ẹ le ṣeto awọn iranti, wa ile-iwosan ni Ipinle Ondo, tabi wo profaili yin lati akojọ aṣayan yii."
        ),
        "Nigerian Pidgin": (
            "🎉 **Registration Don Complete!**\n\n"
            "Welcome to MotherlyPulse, {alias}! We don save your profile well.\n"
            "• Group: {group_desc}\n"
            "• Date: {milestone_date}\n"
            "• Language: {language}\n\n"
            "You fit manage your clinic reminders, find hospital for Ondo State, or check your profile now."
        )
    },
    "language_updated": {
        "English": "Language updated to English.",
        "Yoruba": "A ti yipada si Ede Yoruba.",
        "Nigerian Pidgin": "Language don change to Nigerian Pidgin."
    },
    "help_text": {
        "English": (
            "🏥 **MotherlyPulse Help & Command Reference:**\n\n"
            "/start - Start registration or display Main Menu\n"
            "/language - Change preferred language (English, Yoruba, Pidgin)\n"
            "/profile - View your registered maternal/infant profile\n"
            "/remind - View or manage appointment, medication & vaccine reminders\n"
            "/clinic - Find nearest health facility or immunization centre (Ondo State)\n"
            "/delete - Erase your profile, reminders, and personal records\n"
            "/help - Display this instructions menu\n\n"
            "⚠️ **Emergency:** If you or your baby experience danger signs, dial **112** immediately."
        ),
        "Yoruba": (
            "🏥 **Itọsọna Ati Awọn Ilana MotherlyPulse:**\n\n"
            "/start - Bẹrẹ iforukọsilẹ tabi ṣii Akojọ Aṣayan\n"
            "/language - Yi ede pada (English, Yoruba, Pidgin)\n"
            "/profile - Wo profaili aboyun tabi iya ọmọ rẹ\n"
            "/remind - Wo tabi ṣeto awọn iranti abẹwo, oogun, ati ajesara\n"
            "/clinic - Wa ile-iwosan tabi ile-iṣẹ ajesara to sunmọ (Ipinle Ondo)\n"
            "/delete - Pa profaili, iranti, ati gbogbo alaye rẹ rẹ patapata\n"
            "/help - Wo itọsọna yii lẹẹkansi\n\n"
            "⚠️ **Pajawiri:** Ti eewu ba wa, ẹ pe **112** lẹsẹkẹsẹ."
        ),
        "Nigerian Pidgin": (
            "🏥 **MotherlyPulse Help & Commands:**\n\n"
            "/start - Start registration or open Main Menu\n"
            "/language - Change your language (English, Yoruba, Pidgin)\n"
            "/profile - Check your profile info\n"
            "/remind - Check or set clinic, medicine and vaccine reminders\n"
            "/clinic - Find clinic or immunization post near you (Ondo State)\n"
            "/delete - Delete your profile and all your reminders\n"
            "/help - See this guide\n\n"
            "⚠️ **Emergency:** If any serious danger sign happen, call **112** right now."
        )
    },
    "emergency_banner": {
        "English": "EMERGENCY ALERT: This appears to be a medical emergency. Please call 112 immediately or proceed to the nearest emergency health facility.",
        "Yoruba": "IKILO PAJAWIRI: Eyi dabi pajawiri ilera. E pe 112 lesekese tabi ki e lo si ile iwosan pajawiri to sunmo julo.",
        "Nigerian Pidgin": "EMERGENCY WARNING: This one be serious medical emergency. Call 112 immediately or run go the nearest emergency hospital."
    },
    "holding_message": {
        "English": (
            "ℹ️ **Notice:** The conversational health assistant is currently in preparation (awaiting AI model integration).\n\n"
            "While our health chat is being connected, you can use MotherlyPulse to:\n"
            "• Track clinic appointments (/remind)\n"
            "• Schedule your personal medication reminders\n"
            "• View infant vaccination schedules\n"
            "• Find verified health facilities in Ondo State (/clinic)\n\n"
            "⚠️ **IN AN EMERGENCY:** If you or your baby experience any severe symptoms, bleeding, convulsions, or high fever, please call **112** immediately or go to the nearest hospital."
        ),
        "Yoruba": (
            "ℹ️ **Akiyesi:** Iranlọwọ ibaraẹnisọrọ ilera ti MotherlyPulse wa ni imurasilẹ lọwọlọwọ (a n duro de iṣọpọ awoṣe AI).\n\n"
            "Lakoko ti a n sopọ eto ibaraẹnisọrọ yii, ẹ le lo MotherlyPulse fun:\n"
            "• Ṣiṣeto awọn iranti abẹwo ile-iwosan (/remind)\n"
            "• Ṣiṣeto awọn iranti oogun ti dokita kọ fun yin\n"
            "• Wiwo akoko ajesara awọn ọmọ wẹwẹ\n"
            "• Wiwa awọn ile-iwosan to fidi mule ni Ipinle Ondo (/clinic)\n\n"
            "⚠️ **TI PAJAWIRI BA WA:** Ti ẹ ba ni awọn aami eewu to le koko, ẹ pe **112** lẹsẹkẹsẹ tabi ki ẹ lọ si ile-iwosan to sunmọ."
        ),
        "Nigerian Pidgin": (
            "ℹ️ **Notice:** Health chat assistant dey under preparation now (we dey wait for AI model integration).\n\n"
            "As we dey arrange the chat model, you fit use MotherlyPulse do:\n"
            "• Clinic appointment reminders (/remind)\n"
            "• Set reminder for medicine wey doctor give you\n"
            "• Check infant vaccination timetable\n"
            "• Find verified clinics for Ondo State (/clinic)\n\n"
            "⚠️ **FOR EMERGENCY:** If you or your pikin get severe sickness, bleeding, or convulsion, call **112** right now or go straight to hospital."
        )
    },
    "data_deleted": {
        "English": "All your stored profile details and reminders have been permanently deleted.",
        "Yoruba": "A ti pa gbogbo alaye ati iranti re re patapata.",
        "Nigerian Pidgin": "We don clear all your stored profile and reminders completely."
    },
    "delete_confirm_prompt": {
        "English": (
            "⚠️ **ACCOUNT DELETION CONFIRMATION**\n\n"
            "Are you sure you want to permanently delete your MotherlyPulse account?\n"
            "This will erase:\n"
            "• Your registered profile and milestone dates\n"
            "• All scheduled clinic, medication, and vaccination reminders\n"
            "• All session and registration records\n\n"
            "This action cannot be undone.\n"
            "Reply **confirm** to permanently delete, or **cancel** to keep your account."
        ),
        "Yoruba": (
            "⚠️ **IFIDIMULE IPARẸ AKAUNTI**\n\n"
            "Ṣe o da yin loju pe ẹ fẹ pa akaunti MotherlyPulse yin rẹ patapata?\n"
            "Eyi yoo pa:\n"
            "• Profaili ati ọjọ ibimọ yin\n"
            "• Gbogbo awọn iranti abẹwo ile-iwosan, oogun, ati ajesara\n"
            "• Gbogbo akọsilẹ iforukọsilẹ yin\n\n"
            "A ko le da eyi pada mọ.\n"
            "Dahun **fowosi** lati pa a rẹ, tabi **fagile** lati da duro."
        ),
        "Nigerian Pidgin": (
            "⚠️ **CONFIRM TO DELETE YOUR ACCOUNT**\n\n"
            "You sure say you wan permanently delete your MotherlyPulse account?\n"
            "This go clear:\n"
            "• Your profile and baby milestone dates\n"
            "• All your clinic, medicine, and vaccine reminders\n"
            "• All your account information\n\n"
            "Once deleted, e no go fit come back.\n"
            "Reply **confirm** make we delete am, or **cancel** to keep your account."
        )
    },
    "delete_cancelled": {
        "English": "Account deletion cancelled. Your profile and reminders remain active.",
        "Yoruba": "A ti fagilee iparẹ akaunti. Profaili ati awọn iranti yin ṣi wa.",
        "Nigerian Pidgin": "Account deletion don cancel. Your profile and reminders still active well."
    },
    "location_prompt": {
        "English": "Please share your location or send your coordinates (latitude, longitude) to locate your nearest clinic in Ondo State.",
        "Yoruba": "E jowo fi ibi ti o wa ranse tabi e fi nomba latitude ati longitude ranse lati wa ile iwosan to sunmo yin ni Ipinle Ondo.",
        "Nigerian Pidgin": "Abeg send your location or latitude and longitude make we find the clinic wey near you pass for Ondo State."
    }
}


def get_interface_string(
    key: str,
    language: str = "English",
    allow_unreviewed_translations: bool = False
) -> str:
    """
    Retrieves an interface string for the given language.
    If allow_unreviewed_translations is False and the language's status is not 'reviewed',
    falls back safely to English.
    """
    key_dict = STRINGS.get(key)
    if not key_dict:
        return f"[Missing string: {key}]"
        
    normalized_lang = language.strip().title()
    if normalized_lang not in ("English", "Yoruba", "Nigerian Pidgin"):
        normalized_lang = "English"

    # Enforce translation review status
    status = STRING_REVIEW_STATUS.get(normalized_lang, "not reviewed")
    if not allow_unreviewed_translations and status != "reviewed":
        # Safe fallback to English
        return key_dict.get("English", "")

    return key_dict.get(normalized_lang, key_dict.get("English", ""))


def get_localized_string(key: str, language: str = "English") -> str:
    """
    Helper for Telegram bot UI elements that always renders the localized translation
    for the user's selected language.
    """
    return get_interface_string(key, language, allow_unreviewed_translations=True)
