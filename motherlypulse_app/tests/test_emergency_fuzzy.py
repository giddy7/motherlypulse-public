"""
Unit and Regression Tests for Emergency Fuzzy Matching & Multi-Turn Escalation
Verifies:
1. Bounded fuzzy matching (Levenshtein distance <= 2) for emergency misspellings across English, Yoruba, and Nigerian Pidgin (>= 30 tests).
2. Absence of false positive over-matching on routine messages.
3. Multi-turn escalation across English, Yoruba, and Nigerian Pidgin (>= 5 scenarios per language, including routine-to-emergency transitions).
"""

import unittest
from motherlypulse_app.classifier import DynamicTriageClassifier
from motherlypulse_app.assistant import MotherlyPulseAssistant


class TestEmergencyFuzzyMatching(unittest.TestCase):
    def setUp(self):
        self.classifier = DynamicTriageClassifier()

    def test_english_fuzzy_misspellings(self):
        cases = [
            ("hevy bleeeding", "emergency"),
            ("my baby has covulsion", "emergency"),
            ("she is having a seezure right now", "emergency"),
            ("experiencing severe hemmorrhage", "emergency"),
            ("patient is unconcious after fainting", "emergency"),
            ("danger signs of preclamsia", "emergency"),
            ("she has eclamsia fits", "emergency"),
            ("baby turned cyanocis lips", "emergency"),
            ("green meconeum in amniotic water", "emergency"),
            ("infant with lockjaw trysmus", "emergency"),
            ("soaked pad with heavy bleding", "emergency"),
            ("baby cannot breating well and gasping", "emergency"),
        ]
        for msg, expected in cases:
            with self.subTest(msg=msg):
                res = self.classifier.classify(msg)
                self.assertEqual(res["urgency_category"], expected, f"Failed for English: '{msg}' -> {res}")

    def test_yoruba_fuzzy_misspellings(self):
        cases = [
            ("mo n ri eje puppo ti o n da jade", "emergency"),
            ("eje pupp n tu jade lati ese", "emergency"),
            ("omo mi ni girri leralera", "emergency"),
            ("iyawo mi ni fiti lojiji", "emergency"),
            ("aboyun ni idarudappo opolo", "emergency"),
            ("iba gbigbona 39.5 omi to n run kinkankan", "emergency"),
            ("eje popo lati oju ara", "emergency"),
            ("omo n dekun mimmi ko le mi daadaa", "emergency"),
            ("ko si mo nnkan kan mo girri", "emergency"),
            ("eje pupoo ti n da jade", "emergency"),
        ]
        for msg, expected in cases:
            with self.subTest(msg=msg):
                res = self.classifier.classify(msg)
                self.assertEqual(res["urgency_category"], expected, f"Failed for Yoruba: '{msg}' -> {res}")

    def test_pidgin_fuzzy_misspellings(self):
        cases = [
            ("blood dey poor well well", "emergency"),
            ("pikin body dey hot wel wel", "emergency"),
            ("my sister dey covulsion", "emergency"),
            ("heavy bleeeding no de stop", "emergency"),
            ("baby no de breeth at all", "emergency"),
            ("she faint and unconshous", "emergency"),
            ("pikin stomach hard like stoone", "emergency"),
            ("water burst with thick green slyme", "emergency"),
            ("blood de com plenty plenty", "emergency"),
            ("pikin body hot well well", "emergency"),
        ]
        for msg, expected in cases:
            with self.subTest(msg=msg):
                res = self.classifier.classify(msg)
                self.assertEqual(res["urgency_category"], expected, f"Failed for Pidgin: '{msg}' -> {res}")

    def test_no_routine_overmatching(self):
        routine_cases = [
            "What foods help with nausea during early pregnancy?",
            "How much clean water should a breastfeeding mother drink daily?",
            "Can I bathe my baby with warm water?",
            "How often should an infant breastfeed?",
            "Bawo ni mo se le toju ara mi ni osu akoko?",
            "Ounje wo lo dara fun alaboyun?",
            "Wetin person go chop when belle dey do am somehow?",
            "How I fit clean my baby skin?"
        ]
        for msg in routine_cases:
            with self.subTest(msg=msg):
                res = self.classifier.classify(msg)
                self.assertEqual(res["urgency_category"], "routine", f"Over-matched routine query: '{msg}' -> {res}")


class TestMultiTurnEmergencyEscalation(unittest.TestCase):
    def setUp(self):
        self.assistant_en = MotherlyPulseAssistant(language="English")
        self.assistant_yo = MotherlyPulseAssistant(language="Yoruba")
        self.assistant_pcm = MotherlyPulseAssistant(language="Nigerian Pidgin")

    def test_english_multi_turn_scenarios(self):
        # Scenario 1: Routine -> Emergency bleeding
        r1 = self.assistant_en.handle_message("What foods help with morning nausea?")
        self.assertEqual(r1["urgency_category"].lower(), "routine")
        self.assertNotIn("EMERGENCY", r1["reply"])

        r2 = self.assistant_en.handle_message(
            "Also I have sudden heavy bleeding soaking pads now",
            conversation_history=["What foods help with morning nausea?"]
        )
        self.assertEqual(r2["urgency_category"].lower(), "emergency")
        self.assertIn("EMERGENCY", r2["reply"])
        self.assertIn("112", r2["reply"])
        self.assertNotIn("morning nausea", r2["reply"].lower())

        # Scenario 2: Routine -> Emergency convulsion
        r1 = self.assistant_en.handle_message("Can I take rest in the afternoon?")
        self.assertEqual(r1["urgency_category"].lower(), "routine")

        r2 = self.assistant_en.handle_message(
            "My baby just started having convulsions and rolling eyes",
            conversation_history=["Can I take rest in the afternoon?"]
        )
        self.assertEqual(r2["urgency_category"].lower(), "emergency")
        self.assertIn("EMERGENCY", r2["reply"])

        # Scenario 3: Direct Emergency - Unconscious
        r = self.assistant_en.handle_message("The mother fainted and is unconscious")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

        # Scenario 4: Direct Emergency - Severe epigastric pain and blurry vision
        r = self.assistant_en.handle_message("Terrible headache with blurry vision and swollen face")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

        # Scenario 5: Direct Emergency - Infant gasping
        r = self.assistant_en.handle_message("Newborn baby has chest indrawing and struggling to breathe")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

    def test_yoruba_multi_turn_scenarios(self):
        # Scenario 1: Routine -> Emergency (eje pupo)
        r1 = self.assistant_yo.handle_message("Ounje wo lo dara fun aboyun?", language="Yoruba")
        self.assertEqual(r1["urgency_category"].lower(), "routine")

        r2 = self.assistant_yo.handle_message(
            "Eje pupo n tu jade lati ese mi lẹsẹkẹsẹ",
            language="Yoruba",
            conversation_history=["Ounje wo lo dara fun aboyun?"]
        )
        self.assertEqual(r2["urgency_category"].lower(), "emergency")
        self.assertIn("EMERGENCY", r2["reply"])
        self.assertIn("112", r2["reply"])

        # Scenario 2: Routine -> Emergency (giri)
        r1 = self.assistant_yo.handle_message("Bawo ni mo se le we omo mi?", language="Yoruba")
        self.assertEqual(r1["urgency_category"].lower(), "routine")

        r2 = self.assistant_yo.handle_message(
            "Omo mi ni giri to le koko",
            language="Yoruba",
            conversation_history=["Bawo ni mo se le we omo mi?"]
        )
        self.assertEqual(r2["urgency_category"].lower(), "emergency")
        self.assertIn("EMERGENCY", r2["reply"])

        # Scenario 3: Direct Emergency - Eclampsia vision
        r = self.assistant_yo.handle_message("Oju mi n sokunkun pelu ori fifo lile", language="Yoruba")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

        # Scenario 4: Direct Emergency - Dekun mimi
        r = self.assistant_yo.handle_message("Omo mi dekun mimi ko le mi", language="Yoruba")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

        # Scenario 5: Direct Emergency - Foul amniotic
        r = self.assistant_yo.handle_message("Omi oyun be pelu awo eweko ti o ki meconium", language="Yoruba")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

    def test_pidgin_multi_turn_scenarios(self):
        # Scenario 1: Routine -> Emergency (heavy bleeding)
        r1 = self.assistant_pcm.handle_message("Wetin I fit drink for morning sickness?", language="Nigerian Pidgin")
        self.assertEqual(r1["urgency_category"].lower(), "routine")

        r2 = self.assistant_pcm.handle_message(
            "Wait, blood dey pour from my body heavy now now",
            language="Nigerian Pidgin",
            conversation_history=["Wetin I fit drink for morning sickness?"]
        )
        self.assertEqual(r2["urgency_category"].lower(), "emergency")
        self.assertIn("EMERGENCY", r2["reply"])
        self.assertIn("112", r2["reply"])

        # Scenario 2: Routine -> Emergency (pikin body hot / convulsions)
        r1 = self.assistant_pcm.handle_message("How many times pikin suppose sleep for afternoon?", language="Nigerian Pidgin")
        self.assertEqual(r1["urgency_category"].lower(), "routine")

        r2 = self.assistant_pcm.handle_message(
            "Pikin body dey hot wel wel and e de roll eyes",
            language="Nigerian Pidgin",
            conversation_history=["How many times pikin suppose sleep for afternoon?"]
        )
        self.assertEqual(r2["urgency_category"].lower(), "emergency")
        self.assertIn("EMERGENCY", r2["reply"])

        # Scenario 3: Direct Emergency - Pikin no de breathe
        r = self.assistant_pcm.handle_message("My newborn baby lips turn blue and baby no de breathe", language="Nigerian Pidgin")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

        # Scenario 4: Direct Emergency - Stomach hard like stone
        r = self.assistant_pcm.handle_message("Stomach hard like stone and pain dey tear my belly", language="Nigerian Pidgin")
        self.assertEqual(r["urgency_category"].lower(), "emergency")

        # Scenario 5: Direct Emergency - Heavy blood de come
        r = self.assistant_pcm.handle_message("Blood de com plenty plenty and I de faint", language="Nigerian Pidgin")
        self.assertEqual(r["urgency_category"].lower(), "emergency")


if __name__ == "__main__":
    unittest.main()
